import json
import logging
import pika
from pika.adapters.tornado_connection import TornadoConnection
from slack import slack_event_handler
from pika.exchange_type import ExchangeType

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

FUNC_HANDLERS = {
    "slack.observed": slack_event_handler
}


class Consumer:

    EXCHANGE_TYPE = ExchangeType.topic

    def __init__(self, amqp_url, exchange_name, binding_keys, queue_name=""):
        self.queue_name = queue_name
        self.exchange_name = exchange_name
        self.binding_keys = binding_keys
        self._url = amqp_url
        self._connection = None
        self._consumer_tag = None
        self._channel = None
        self._closing = False

    def close_connection(self):
        """This method closes the connection to RabbitMQ."""
        logging.info('Closing connection')
        self._connection.close()

    def add_on_connection_close_callback(self):
        """This method adds an on close callback that will be invoked by pika
        when RabbitMQ closes the connection to the publisher unexpectedly.

        """
        logging.info('Adding connection close callback')
        self._connection.add_on_close_callback(self.on_connection_closed)

    def on_connection_closed(self, _connection, reason):
        """This method is invoked by pika when the connection to RabbitMQ is
        closed unexpectedly. Since it is unexpected, we will reconnect to
        RabbitMQ if it disconnects.

        :param pika.connection.Connection _connection: The closed connection obj
        :param Exception reason: exception representing reason for loss of
            connection.

        """
        self._channel = None
        if self._closing:
            self._connection.ioloop.stop()
        else:
            logging.warning(f"Connection closed, reopening in 5 seconds: {reason}",)
            self._connection.ioloop.call_later(5, self.reconnect)

    def on_connection_open(self, _unused_connection):
        """This method is called by pika once the connection to RabbitMQ has
        been established. It passes the handle to the connection object in
        case we need it, but in this case, we'll just mark it unused.

        :param pika.SelectConnection _unused_connection: The connection
        """
        logging.info('Connection opened')
        self.add_on_connection_close_callback()
        self.open_channel()

    def open_channel(self):
        """Open a new channel with RabbitMQ by issuing the Channel.Open RPC
        command. When RabbitMQ responds that the channel is open, the
        on_channel_open callback will be invoked by pika.

        """
        logging.info('Creating a new channel')
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        """This method is invoked by pika when the channel has been opened.
        The channel object is passed in so we can make use of it.

        Since the channel is now open, we'll declare the exchange to use.

        :param pika.channel.Channel channel: The channel object

        """
        logging.info('Channel opened')
        self._channel = channel
        self.add_on_channel_close_callback()

        logging.info('Declaring exchange %s', self.exchange_name)
        self._channel.exchange_declare(
            callback=self.on_exchange_declare_ok,
            exchange=self.exchange_name,
            exchange_type=self.EXCHANGE_TYPE,
        )

    def add_on_channel_close_callback(self):
        """This method tells pika to call the on_channel_closed method if
        RabbitMQ unexpectedly closes the channel.

        """
        logging.info('Adding channel close callback')
        self._channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, reason):
        """Invoked by pika when RabbitMQ unexpectedly closes the channel.
        Channels are usually closed if you attempt to do something that
        violates the protocol, such as re-declare an exchange or queue with
        different parameters. In this case, we'll close the connection
        to shut down the object.

        :param pika.channel.Channel channel: The closed channel
        :param Exception reason: why the channel was closed

        """
        logging.warning('Channel %i was closed: %s', channel, reason)
        self._connection.close()

    def connect(self):
        """This method connects to RabbitMQ, returning the connection handle.
        When the connection is established, the on_connection_open method
        will be invoked by pika.

        :rtype: pika.SelectConnection

        """
        logging.info('Connecting to host %s', self._url)
        parameters = pika.URLParameters(self._url)
        return TornadoConnection(
            parameters,
            self.on_connection_open,
        )

    def reconnect(self):
        """Will be invoked by the IOLoop timer if the connection is
        closed. See the on_connection_closed method.

        """
        if not self._closing:
            # Create a new connection
            self._connection = self.connect()

    def close_channel(self):
        """Call to close the channel with RabbitMQ cleanly by issuing the
        Channel.Close RPC command.

        """
        logging.info('Closing the channel')
        self._channel.close()

    def stop_consuming(self):
        """Tell RabbitMQ that you would like to stop consuming by sending the
        Basic.Cancel RPC command.

        """
        if self._channel:
            logging.info('Sending a Basic.Cancel RPC command to RabbitMQ')
            self._channel.basic_cancel(self.close_channel, self._consumer_tag)

    def run(self):
        """Run the example consumer by connecting to RabbitMQ and then
        starting the IOLoop to block and allow the SelectConnection to operate.

        """
        self._connection = self.connect()
        self._connection.ioloop.start()

    def stop(self):
        """Cleanly shutdown the connection to RabbitMQ by stopping the consumer
        with RabbitMQ. When RabbitMQ confirms the cancellation, on_cancelok
        will be invoked by pika, which will then closing the channel and
        connection. The IOLoop is started again because this method is invoked
        when CTRL-C is pressed raising a KeyboardInterrupt exception. This
        exception stops the IOLoop which needs to be running for pika to
        communicate with RabbitMQ. All of the commands issued prior to starting
        the IOLoop will be buffered but not processed.

        """
        logging.info('Stopping')
        self._closing = True
        self.stop_consuming()
        self._connection.ioloop.start()
        logging.info('Stopped')

    def on_exchange_declare_ok(self, _unused_frame):
        """Invoked by pika when RabbitMQ has finished the Exchange.Declare RPC
        command.

        :param pika.Frame.Method _unused_frame: Exchange.DeclareOk response frame

        """
        logging.info('Exchange declared queue')
        self._channel.queue_declare(
            queue=self.queue_name,
            callback=self.on_queue_declare_ok,
        )

    def on_queue_declare_ok(self, method_frame):
        """Method invoked by pika when the Queue.Declare RPC call made in
        setup_queue has completed. In this method we will bind the queue
        and exchange together with the routing key by issuing the Queue.Bind
        RPC command. When this command is complete, the on_bindok method will
        be invoked by pika.

        :param pika.frame.Method method_frame: The Queue.DeclareOk frame

        """
        _queue_name = method_frame.method.queue
        self.queue_name = _queue_name
        print("[*] Waiting for data for " + _queue_name + ".To exit press CTRL+C")
        for binding_key in self.binding_keys:
            logging.info('Binding %s to %s with %s', self.exchange_name, _queue_name, binding_key)
            self._channel.queue_bind(
                queue=_queue_name,
                exchange=self.exchange_name,
                routing_key=binding_key,
                callback=self.start_consuming,
            )

    def start_consuming(self, _unused_frame):
        """This method sets up the consumer by first calling
        add_on_cancel_callback so that the object is notified if RabbitMQ
        cancels the consumer. It then issues the Basic.Consume RPC command
        which returns the consumer tag that is used to uniquely identify the
        consumer with RabbitMQ. We keep the value to use it when we want to
        cancel consuming. The on_message method is passed in as a callback pika
        will invoke when a message is fully received.
        :param pika.frame.Method _unused_frame: The Queue.BindOk response frame
        """
        logging.info('Issuing consumer related RPC commands')
        self.add_on_cancel_callback()
        self._consumer_tag = self._channel.basic_consume(
            on_message_callback=self.on_message_callback,
            queue=self.queue_name,
        )

    def add_on_cancel_callback(self):
        """Add a callback that will be invoked if RabbitMQ cancels the consumer
        for some reason. If RabbitMQ does cancel the consumer,
        on_consumer_cancelled will be invoked by pika.

        """
        logging.info('Adding consumer cancellation callback')
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)

    def on_consumer_cancelled(self, method_frame):
        """Invoked by pika when RabbitMQ sends a Basic.Cancel for a consumer
        receiving messages.

        :param pika.frame.Method method_frame: The Basic.Cancel frame

        """
        logging.info('Consumer was cancelled remotely, shutting down: %r', method_frame)
        if self._channel:
            self._channel.close()

    def on_message_callback(self, _channel, method, _properties, body):
        binding_key = method.routing_key
        logging.info('Received message # %s from %s: %s', method.delivery_tag, _properties.app_id, body)
        if binding_key in FUNC_HANDLERS:
            FUNC_HANDLERS[binding_key](json.loads(body.decode('utf8')))
        else:
            logging.info("not register handler.")
        self.acknowledge_message(method.delivery_tag)

    def acknowledge_message(self, delivery_tag):
        """Acknowledge the message delivery from RabbitMQ by sending a
        Basic.Ack RPC method for the delivery tag.

        :param int delivery_tag: The delivery tag from the Basic.Deliver frame

        """
        logging.info('Acknowledging message %s', delivery_tag)
        self._channel.basic_ack(delivery_tag)

    def execute(self):
        try:
            self.run()
        except KeyboardInterrupt:
            self.stop()

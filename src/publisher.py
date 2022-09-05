import pika
import json


class Publisher:

    def __init__(self, _url, exchange):
        self._url = _url
        self.exchange = exchange

    def publish(self, routing_key, message):
        connection = self.create_connection()
        # Create a new channel with the next available channel number
        # or pass in a channel number to use
        channel = connection.channel()
        # Creates an exchange if it does not already exist, and if the exchange exists,
        # verifies that it is of the correct and expected class.
        channel.exchange_declare(exchange=self.exchange, exchange_type="topic")
        # Publishes message to the exchange with the given routing ke
        channel.basic_publish(exchange=self.exchange, routing_key=routing_key, body=message)
        print("[x] Sent message %r for %r”" % (message, routing_key))

    def create_connection(self):
        param = pika.URLParameters(self._url)
        return pika.BlockingConnection(param)


config = {"host": "localhost", "port": 5672, "exchange": "notification_queue"}

publisher = Publisher(exchange="notification_queue",
                      _url="amqps://lvilkyom:SVr2qRYPC5Dmv69q0kdSe_4lnEQ0hwNx@mustang.rmq.cloudamqp.com/lvilkyom")
payload = {
    "title": "S3 Bucket Encryption",
    "id": "sample-id",
    "description": "Enable bucket encryption",
    "severity_type": "Critical",
    "compliance": "PCI-DSS",
    "resource_type": "Storage",
    "resource_items": [
        {"name": "bucket1", "id": "id1"}
    ],
    "webhook_url": "https://hooks.slack.com/services/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"
}

publisher.publish("slack.observed", json.dumps(payload))

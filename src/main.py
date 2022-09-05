import sys
import os
from consumer import Consumer


if __name__ == '__main__':
    # key in the form exchange.*
    binding_keys = ["slack.observed"]
    if not binding_keys:
        sys.stderr.write("Usage: %s [binding_key]...\n" % sys.argv[0])
        sys.exit(1)
    cluster_url = os.getenv("CLUSTER_URL", "amqp://guest:guest@localhost:5672/")
    subscriber = Consumer(binding_keys=binding_keys,
                          amqp_url="amqps://lvilkyom:SVr2qRYPC5Dmv69q0kdSe_4lnEQ0hwNx@mustang.rmq.cloudamqp.com/lvilkyom",

                          exchange_name="notification_queue")
    subscriber.execute()

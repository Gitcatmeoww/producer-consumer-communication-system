import pika
import os
from config_rabbitmq import RabbitMQConfig

class RabbitMQSetup:
    def __init__(self, config: RabbitMQConfig):
        self.config = config
        self.connection = None
        self.channel = None

    def connect(self) -> None:
        credentials = pika.PlainCredentials(self.config.user, self.config.password)
        parameters = pika.ConnectionParameters(
            self.config.host,
            virtual_host=self.config.vhost,
            credentials=credentials
        )
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

    def declare_queue(self, queue_name: str) -> None:
        """
        Declares a queue in RabbitMQ.
        
        Args:
            queue_name (str): The name of the queue to declare.
        """
        self.channel.queue_declare(queue=queue_name, durable=True)
        print(f"🐰 Declared queue: {queue_name}", flush=True)

    def setup_queues(self) -> None:
        """
        Declares all necessary queues in RabbitMQ.
        """
        self.declare_queue('request_queue')
        self.declare_queue('response_queue')

    def close(self) -> None:
        """
        Closes the RabbitMQ connection.
        """
        if self.connection:
            self.connection.close()
            print("🐰 RabbitMQ connection closed", flush=True)

if __name__ == "__main__":
    rabbitmq_config = RabbitMQConfig(
        host=os.getenv('RABBITMQ_HOST'),
        user=os.getenv('RABBITMQ_DEFAULT_USER'),
        password=os.getenv('RABBITMQ_DEFAULT_PASS'),
        vhost=os.getenv('RABBITMQ_DEFAULT_VHOST')
    )

    rabbitmq_setup = RabbitMQSetup(rabbitmq_config)
    
    try:
        rabbitmq_setup.connect()
        rabbitmq_setup.setup_queues()
    except pika.exceptions.AMQPConnectionError as e:
        print(f"⛔ Failed to connect to RabbitMQ: {e}", flush=True)
    except Exception as e:
        print(f"⛔ Failed to set up RabbitMQ queues: {e}", flush=True)
    finally:
        rabbitmq_setup.close()

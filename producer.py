import pika
import uuid
import os
import logging
import asyncio
from typing import Optional
from config_rabbitmq import RabbitMQConfig
from setup_rabbitmq import RabbitMQSetup

# Configure logging
logging.basicConfig(level=logging.INFO)

class Producer:
    def __init__(self, rabbitmq_setup: RabbitMQSetup):
        """
        Initializes the Producer with a RabbitMQ setup instance.
        
        Args:
            rabbitmq_setup (RabbitMQSetup): An instance of RabbitMQSetup for connection handling.
        """
        self.rabbitmq_setup = rabbitmq_setup
        self.connection = self.rabbitmq_setup.connection
        self.channel = self.rabbitmq_setup.channel
        self.callback_queue = None  # A temporary queue to receive responses for a specific request
        self.futures = {}  # Dictionary to store futures associated with correlation IDs

    def setup_callback_queue(self) -> None:
        """
        Sets up a callback queue for receiving responses from the consumer.
        This queue is temporary and exclusive to the connection that declares it.
        """
        self.callback_queue = self.channel.queue_declare(queue='', exclusive=True).method.queue
        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True
        )
        logging.info(f"👯‍♀️ Callback queue setup with name: {self.callback_queue}")

    def on_response(self, ch: pika.channel.Channel, method: pika.spec.Basic.Deliver, props: pika.spec.BasicProperties, body: bytes) -> None:
        """
        Handles the response from the consumer.
        
        Args:
            ch (pika.channel.Channel): The channel object.
            method (pika.spec.Basic.Deliver): Delivery method.
            props (pika.spec.BasicProperties): Properties of the message.
            body (bytes): The body of the message.
        """
        logging.info(f"📥 Producer received response with correlation_id: {props.correlation_id}")
        future = self.futures.pop(props.correlation_id, None)
        if future is not None:
            future.set_result(body)  # Set the result of the future with the response body

    async def call(self, message: str) -> Optional[str]:
        """
        Sends a message to the request queue and waits for a response.
        
        Args:
            message (str): The message to send.
        
        Returns:
            Optional[str]: The response from the consumer, if any.
        """
        loop = asyncio.get_running_loop()  # Get the running event loop
        corr_id = str(uuid.uuid4())  # Generate a unique correlation ID

        future = loop.create_future()  # Create a new future
        self.futures[corr_id] = future  # Store the future with the correlation ID

        try:
            # Publish the message to the request queue
            self.channel.basic_publish(
                exchange='',  # Use the default exchange
                routing_key='request_queue',
                properties=pika.BasicProperties(
                    reply_to=self.callback_queue,  # The callback queue where the response should be sent
                    correlation_id=corr_id,  # Unique identifier for correlating the response
                ),
                body=message
            )
            logging.info(f"📤 Producer sent message: {message} with correlation_id: {corr_id}")
        except Exception as e:
            logging.error(f"⛔ Failed to send message: {e}")
            return None

        response = await future  # Wait for the future to be set with the response
        logging.info(f"📥 Producer received response: {response.decode()}")
        return response.decode()  # Decode and return the response

    def close(self) -> None:
        """
        Closes the RabbitMQ connection.
        """
        self.rabbitmq_setup.close()

if __name__ == "__main__":
    rabbitmq_config = RabbitMQConfig(
        host=os.getenv('RABBITMQ_HOST'),
        user=os.getenv('RABBITMQ_DEFAULT_USER'),
        password=os.getenv('RABBITMQ_DEFAULT_PASS'),
        vhost=os.getenv('RABBITMQ_DEFAULT_VHOST')
    )

    rabbitmq_setup = RabbitMQSetup(rabbitmq_config)
    
    producer = None
    try:
        rabbitmq_setup.connect()
        producer = Producer(rabbitmq_setup)
        producer.setup_callback_queue()
        
        async def main():
            # Test for sending one message
            # response = await producer.call('Hello, Consumer!')
            # logging.info(f"📥 Received response: {response}")

            # Test for sending multiple messages
            messages = ['Hello, Consumer! 1', 'Hello, Consumer! 2', 'Hello, Consumer! 3']
            tasks = [producer.call(message) for message in messages]
            responses = await asyncio.gather(*tasks)
            for response in responses:
                logging.info(f"📥 Producer received response: {response}")
        
        asyncio.run(main())
    except Exception as e:
        logging.error(f"⛔ An error occurred in the producer service: {e}")
    finally:
        if producer:
            producer.close()

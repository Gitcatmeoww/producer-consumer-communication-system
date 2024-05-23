import pika
import os
import logging
import asyncio
from config_rabbitmq import RabbitMQConfig
from setup_rabbitmq import RabbitMQSetup

# Configure logging
logging.basicConfig(level=logging.INFO)

class Consumer:
    def __init__(self, rabbitmq_setup: RabbitMQSetup):
        """
        Initializes the Consumer with a RabbitMQ setup instance.
        
        Args:
            rabbitmq_setup (RabbitMQSetup): An instance of RabbitMQSetup for connection handling.
        """
        self.rabbitmq_setup = rabbitmq_setup
        self.connection = self.rabbitmq_setup.connection
        self.channel = self.rabbitmq_setup.channel

    def on_request(self, ch: pika.channel.Channel, method: pika.spec.Basic.Deliver, props: pika.spec.BasicProperties, body: bytes) -> None:
        """
        Handles the incoming request from the producer, processes it, and sends a response.
        
        Args:
            ch (pika.channel.Channel): The channel object.
            method (pika.spec.Basic.Deliver): Delivery method.
            props (pika.spec.BasicProperties): Properties of the message.
            body (bytes): The body of the message.
        """
        message = body.decode()
        logging.info(f"📥 Consumer received request: {message} with correlation_id: {props.correlation_id}")

        # Simulate processing the request
        response = f"🤖 Consumer processed {message}"

        # Send the response back to the producer
        ch.basic_publish(
            exchange='',
            routing_key=props.reply_to,
            properties=pika.BasicProperties(correlation_id=props.correlation_id),
            body=response
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)  # Acknowledge that the message has been processed
        logging.info(f"📤 Consumer sent response: {response} with correlation_id: {props.correlation_id}")

    async def consume(self) -> None:
        """
        Starts consuming messages from the request queue.
        """
        self.channel.basic_qos(prefetch_count=1)  # Ensures that the consumer fetches only one message at a time
        self.channel.basic_consume(queue='request_queue', on_message_callback=self.on_request)

        logging.info("🔄 Awaiting requests")
        await self._consume()  # Start the event loop to process messages

    async def _consume(self) -> None:
        """
        Helper method to run the event loop for consuming messages.
        """
        while True:
            # Processes network events and handles message delivery
            # Keep the connection to RabbitMQ alive and processes incoming messages
            self.connection.process_data_events()
            # Help to manage CPU usage and prevent the loop from running too fast
            await asyncio.sleep(0.1)

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
    
    consumer = None
    try:
        rabbitmq_setup.connect()
        consumer = Consumer(rabbitmq_setup)
        
        async def main():
            await consumer.consume()
        
        asyncio.run(main())
    except Exception as e:
        logging.error(f"⛔ An error occurred in the consumer service: {e}")
    finally:
        if consumer:
            consumer.close()

import os
import pytest
import asyncio
import pika
from producer import Producer
from config_rabbitmq import RabbitMQConfig
from setup_rabbitmq import RabbitMQSetup

@pytest.fixture
def rabbitmq_setup():
    rabbitmq_config = RabbitMQConfig(
        host=os.getenv('RABBITMQ_HOST'),
        user=os.getenv('RABBITMQ_DEFAULT_USER'),
        password=os.getenv('RABBITMQ_DEFAULT_PASS'),
        vhost=os.getenv('RABBITMQ_DEFAULT_VHOST')
    )
    setup = RabbitMQSetup(rabbitmq_config)
    setup.connect()
    return setup

@pytest.fixture
def producer(rabbitmq_setup):
    producer = Producer(rabbitmq_setup)
    producer.setup_callback_queue()
    return producer

@pytest.mark.asyncio
async def test_single_request(producer):
    message = "Test Message 1"

    await producer.call(message)

    # Verify that one message was published to the request queue
    producer.channel.basic_publish.assert_called_once_with(
        exchange='',
        routing_key='request_queue',
        properties=pika.BasicProperties(reply_to=producer.callback_queue),
        body=message
    )

@pytest.mark.asyncio
async def test_multiple_requests(producer):
    messages = ["Test Message 1", "Test Message 2", "Test Message 3"]

    await asyncio.gather(*[producer.call(message) for message in messages])

    # Verify that multiple messages were published to the request queue
    assert producer.channel.basic_publish.call_count == len(messages)
    for message in messages:
        producer.channel.basic_publish.assert_any_call(
            exchange='',
            routing_key='request_queue',
            properties=pika.BasicProperties(reply_to=producer.callback_queue),
            body=message
        )
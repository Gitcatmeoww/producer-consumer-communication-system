import os
import pytest
import asyncio
from multiprocessing import Process
from producer import Producer
from consumer import Consumer
from config_rabbitmq import RabbitMQConfig
from setup_rabbitmq import RabbitMQSetup
import logging

logging.basicConfig(level=logging.INFO)

@pytest.fixture(scope='module')
def rabbitmq_setup():
    rabbitmq_config = RabbitMQConfig(
        host=os.getenv('RABBITMQ_HOST'),
        user=os.getenv('RABBITMQ_DEFAULT_USER'),
        password=os.getenv('RABBITMQ_DEFAULT_PASS'),
        vhost=os.getenv('RABBITMQ_DEFAULT_VHOST')
    )
    setup = RabbitMQSetup(rabbitmq_config)
    setup.connect()
    yield setup
    setup.close()

@pytest.fixture(scope='module')
def producer(rabbitmq_setup):
    producer = Producer(rabbitmq_setup)
    producer.setup_callback_queue()
    return producer

@pytest.fixture(scope='module')
def consumer(rabbitmq_setup):
    consumer = Consumer(rabbitmq_setup)
    return consumer

@pytest.fixture(scope='module', autouse=True)
def start_consumer(consumer):
    p = Process(target=asyncio.run, args=(consumer.consume(),))
    p.start()
    yield
    p.terminate()

@pytest.mark.asyncio
async def test_single_request(producer):
    message = "Test Message 1"
    logging.info("🔄 Sending single request")
    response = await producer.call(message)
    logging.info(f"📥 Received response: {response}")
    assert response == f"🤖 Processed {message}"

@pytest.mark.asyncio
async def test_multiple_requests(producer):
    messages = ["Test Message 1", "Test Message 2", "Test Message 3"]
    logging.info("🔄 Sending multiple requests")
    responses = await asyncio.gather(*[producer.call(message) for message in messages])
    logging.info(f"📥 Received responses: {responses}")
    assert responses == [f"🤖 Processed {message}" for message in messages]

from dataclasses import dataclass

@dataclass
class RabbitMQConfig:
    host: str
    user: str
    password: str
    vhost: str
import json
import logging
import os
from typing import Optional

try:
    import redis as redis_lib
except ImportError:  # pragma: no cover
    redis_lib = None  # type: ignore

try:
    import pika
    from pika.adapters.blocking_connection import BlockingChannel
except ImportError:  # pragma: no cover
    pika = None  # type: ignore
    BlockingChannel = None  # type: ignore


logger = logging.getLogger(__name__)

_redis_client: Optional["redis_lib.Redis"] = None
_rabbit_connection = None
_rabbit_channel: Optional["BlockingChannel"] = None


def get_redis() -> Optional["redis_lib.Redis"]:
    global _redis_client
    if redis_lib is None:
        return None

    if _redis_client is not None:
        return _redis_client

    url = os.getenv("REDIS_URL", "redis  localhost:6379/0")
    try:
        client = redis_lib.Redis.from_url(url, decode_responses=True)
        client.ping()
        _redis_client = client
        return _redis_client
    except Exception as exc:  # pragma: no cover
        logger.warning("Redis not available: %s", exc)
        _redis_client = None
        return None


def get_rabbitmq_channel() -> Optional["BlockingChannel"]:
    global _rabbit_connection, _rabbit_channel

    if pika is None:
        return None

    if _rabbit_channel is not None and _rabbit_channel.is_open:
        return _rabbit_channel

    url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    try:
        params = pika.URLParameters(url)
        _rabbit_connection = pika.BlockingConnection(params)
        _rabbit_channel = _rabbit_connection.channel()
        _rabbit_channel.queue_declare(queue="slot_spins", durable=True)
        return _rabbit_channel
    except Exception as exc:  # pragma: no cover
        logger.warning("RabbitMQ not available: %s", exc)
        _rabbit_connection = None
        _rabbit_channel = None
        return None


def publish_spin_event(event: dict) -> None:
    channel = get_rabbitmq_channel()
    if channel is None:
        return

    body = json.dumps(event).encode("utf-8")
    try:
        channel.basic_publish(
            exchange="",
            routing_key="slot_spins",
            body=body,
            properties=pika.BasicProperties(  # type: ignore[attr-defined]
                delivery_mode=2,
                content_type="application/json",
            ),
        )
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to publish spin event: %s", exc)

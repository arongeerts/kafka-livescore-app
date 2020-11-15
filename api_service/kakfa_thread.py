import json
from time import sleep

from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

from api_service.helpers import ConnectionManager, DataManager, Message, GameEncoder

KAFKA_URL = "kafka:9092"


async def run(sockets: ConnectionManager, data: DataManager):
    consumer = connect_consumer()
    for message in consumer:
        message = Message(**json.loads(message.value))
        updated_game = data.process_message(message)
        if updated_game:
            await sockets.broadcast(json.dumps(updated_game, cls=GameEncoder))
    print("Kafka thread ended")


def connect_consumer():
    while True:
        try:
            consumer = KafkaConsumer(
                "raw-events",
                bootstrap_servers=KAFKA_URL,
            )
            print("Kafka consumer initiated")
            break
        except NoBrokersAvailable:
            sleep(1)
    return consumer

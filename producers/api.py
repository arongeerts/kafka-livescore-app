import threading
import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from kafka import KafkaProducer

from producers.football_data_producer import produce

app = FastAPI()
KAFKA_URL = "kafka:9092"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/games/{game_id}")
def start_game(game_id: str):
    """
    Start events for a game
    :return:
    """

    producer = KafkaProducer(bootstrap_servers=KAFKA_URL)
    emitter = threading.Thread(target=produce, args=(producer, game_id))
    emitter.start()

    return {
        "status_code": 200,
        "detail": f"Started emitting events for game {game_id}"
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")

import datetime
import json
import os
import time
from typing import Any, Dict

from kafka import KafkaProducer

SPEED_UP_FACTOR = 30  # Means a game takes 3 minutes to process


def produce(producer: KafkaProducer, game_id: str):
    print(f"Starting game events for game {game_id}")
    clock = Clock()
    game = Game(game_id)
    while not game.is_finished:
        while clock >= event_timestamp(game.current_event()):
            produce_event(producer, game.game_id, game.current_event())
            game.next()
        clock.tick()
        time.sleep(1 / SPEED_UP_FACTOR)
    print(f"Finished events for {game_id}")


def produce_event(producer, game_id: str, event: Dict[str, Any]):
    payload = {
        "game_id": game_id,
        "event": event
    }
    payload = json.dumps(payload).encode("utf-8")
    producer.send("raw-events", payload)


def read_file(game_id: str):
    events = "/".join(os.path.abspath(__file__).split("/")[:-1]) + "/data/events/"
    return json.load(open(f"{events}/{game_id}.json"))


def event_timestamp(event):
    minute = event.get("minute", 100000)  # Very large value
    second = event.get("second", 0)
    return datetime.time(minute // 60, minute % 60, second)


class Clock:
    def __init__(self):
        self._time = datetime.datetime(2000, 1, 1)

    def tick(self):
        self._time += datetime.timedelta(seconds=1)

    @property
    def time(self):
        return self._time.time()

    def __ge__(self, other):
        if isinstance(other, str):
            try:
                t = datetime.datetime.strptime(other, "%H:%M:%S.%f").time()
            except ValueError:
                t = datetime.datetime.strptime(other, "%H:%M:%S").time()
            return self.time >= t
        elif isinstance(other, datetime.time):
            return self.time >= other
        else:
            raise TypeError()


class Game:
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.event_index = 0
        self.events = read_file(game_id)
        self.is_finished = False

    def finish(self):
        self.is_finished = True

    def current_event(self):
        return self.events[self.event_index]

    def next(self):
        self.event_index += 1
        if self.event_index == len(self.events):
            self.finish()
        else:
            return self.current_event()

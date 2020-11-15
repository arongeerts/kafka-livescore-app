import datetime
import json
import traceback
from dataclasses import dataclass, asdict
from time import sleep
from typing import List, Dict, Any, Optional

from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from starlette.websockets import WebSocket

KAFKA_URL = "kafka:9092"


def connect_consumer():
    while True:
        try:
            consumer = KafkaConsumer(
                f"raw-events",
                max_poll_records=1,
                bootstrap_servers=KAFKA_URL,
            )
            break
        except NoBrokersAvailable:
            sleep(1)
    return consumer


def parse(message):
    return json.loads(message.value.decode("utf-8"))


class Types:
    SHOT = 16
    FOUL = 22
    BAD_BEHAVIOUR = 24
    STARTING_XI = 35
    END_HALF = 34


class Outcomes:
    GOAL = 97
    FOUL_YELLOW = "Yellow Card" # The docs are wrong here, so judging based on event name
    FOUL_SECOND_YELLOW = "Second Yellow Card"
    FOUL_RED = "Red Card"
    BAD_BEHAVIOR_YELLOW = "Yellow Card"
    BAD_BEHAVIOR_SECOND_YELLOW = "Second Yellow Card"
    BAD_BEHAVIOR_RED = "Red Card"


@dataclass
class Message(object):
    game_id: str
    event: Dict[str, Any]


@dataclass
class Player(object):
    id: int
    name: str

    def encode(self):
        return {
            "id": self.id,
            "name": self.id
        }


@dataclass
class YellowCard(object):
    player: Player
    minute: int
    team_id: int

    @classmethod
    def from_event(cls, event):
        return YellowCard(
            player=Player(**event["player"]),
            minute=event["minute"],
            team_id=event["team"]["id"],
        )


@dataclass
class SecondYellow(object):
    player: Player
    minute: int
    team_id: int

    @classmethod
    def from_event(cls, event):
        return SecondYellow(
            player=Player(**event["player"]),
            minute=event["minute"],
            team_id=event["team"]["id"],
        )


@dataclass
class RedCard(object):
    player: Player
    minute: int
    team_id: int

    @classmethod
    def from_event(cls, event):
        return RedCard(
            player=Player(**event["player"]),
            minute=event["minute"],
            team_id=event["team"]["id"],
        )


@dataclass
class Goal(object):
    team_id: int
    player: Player
    minute: int

    @classmethod
    def from_event(cls, event):
        return Goal(
            team_id=event["team"]["id"],
            player=Player(**event["player"]),
            minute=event["minute"],
        )


@dataclass
class Team(object):
    id: int
    name: str


@dataclass
class Game:
    game_id: str
    yellow_cards: List[YellowCard]
    red_cards: List[RedCard]
    second_yellows: List[SecondYellow]
    goals: List[Goal]
    home_team: Optional[Team]
    away_team: Optional[Team]
    events: List[str]

    def __init__(self, game_id):
        self.game_id = game_id
        self.yellow_cards = []
        self.red_cards = []
        self.second_yellows = []
        self.goals = []
        self.home_team = None
        self.away_team = None
        self.events = []

    def dict(self):
        return {
            "yellow_cards": self.yellow_cards,
            "red_cards": self.red_cards,
            "second_yellow": self.yellow_cards,
            "goals": self.goals,
            "home_team": self.home_team,
            "away_team": self.away_team
        }

    def apply(self, event) -> bool:
        """
        Apply the event and return whether something happened
        :param event:
        :return:
        """
        if event["id"] in self.events:
            return False
        try:
            self.events.append(event["id"])
            if self.__is_starting_XI(event):
                print("Starting XI event")
                team = Team(**event["team"])
                if event["index"] == 1:
                    self.home_team = team
                elif event["index"] == 2:
                    self.away_team = team
            elif self.__is_goal(event):
                print("Goal event")
                goal = Goal.from_event(event)
                self.goals.append(goal)
            elif self.__is_yellow(event):
                print("Yellow card event")
                yellow = YellowCard.from_event(event)
                self.yellow_cards.append(yellow)
            elif self.__is_red(event):
                print("Red card event")
                red = RedCard.from_event(event)
                self.red_cards.append(red)
            elif self.__is_second_yellow(event):
                print("Second yellow card event")
                sy = SecondYellow.from_event(event)
                self.second_yellows.append(sy)
            else:
                t = event["type"]["id"]
                return False
            return True
        except KeyError as e:
            print("could not process event")
            print(event)
            print(traceback.format_exc())

    @staticmethod
    def __is_goal(event):
        return event["type"]["id"] == Types.SHOT \
               and event["shot"]["outcome"]["id"] == Outcomes.GOAL

    @staticmethod
    def __is_yellow(event):
        if "foul_committed" in event:
            return (
                    event["type"]["id"] == Types.FOUL and
                    event["foul_committed"].get("card", {}).get("name", "DUMMY") == Outcomes.FOUL_YELLOW
            )
        if "bad_behaviour" in event:
            return (
                    event["type"]["id"] == Types.BAD_BEHAVIOUR and
                    event["bad_behaviour"].get("card", {}).get("name", "DUMMY") == Outcomes.BAD_BEHAVIOR_YELLOW
            )
        return False

    @staticmethod
    def __is_second_yellow(event):
        if "foul_committed" in event:
            return (
                    event["type"]["id"] == Types.FOUL and
                    event["foul_committed"].get("card", {}).get("name", "DUMMY") == Outcomes.FOUL_SECOND_YELLOW
            )
        if "bad_behaviour" in event:
            return (
                    event["type"]["id"] == Types.BAD_BEHAVIOUR and
                    event["bad_behaviour"].get("card", {}).get("name", "DUMMY") == Outcomes.BAD_BEHAVIOR_SECOND_YELLOW
            )
        return False

    @staticmethod
    def __is_red(event):
        if "foul_committed" in event:
            return (
                    event["type"]["id"] == Types.FOUL and
                    event["foul_committed"].get("card", {}).get("name", "DUMMY") == Outcomes.FOUL_RED
            )
        if "bad_behaviour" in event:
            return (
                    event["type"]["id"] == Types.BAD_BEHAVIOUR and
                    event["bad_behaviour"].get("card", {}).get("name", "DUMMY") == Outcomes.BAD_BEHAVIOR_RED
            )
        return False

    @staticmethod
    def __is_starting_XI(event):
        return event["type"]["id"] == Types.STARTING_XI


class DataManager:
    games: Dict[str, Game] = {}

    def process_message(self, message: Message) -> Game:
        if message.game_id not in self.games:
            self.games[message.game_id] = Game(message.game_id)

        game = self.games[message.game_id]
        updated = game.apply(message.event)

        if self.is_end_match(message.event):
            del self.games[message.game_id]

        if updated:
            return game

    @staticmethod
    def is_end_match(event):
        return (
                event["type"]["id"] == Types.END_HALF and
                event["period"] == 2
        )


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


class GameEncoder(json.JSONEncoder):
    def default(self, o):
        if type(o) in [Game, Team, Player, YellowCard, RedCard]:
            return asdict(o)
        return super().default(o)

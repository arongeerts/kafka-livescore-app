import asyncio
import json
import threading
import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocket, WebSocketDisconnect

import api_service.kakfa_thread as kafka_thread
from api_service.helpers import DataManager, ConnectionManager, GameEncoder

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

data = DataManager()
sockets = ConnectionManager()

event_watcher = threading.Thread(target=asyncio.run, args=(kafka_thread.run(sockets, data),))
event_watcher.start()


@app.get("/games")
def get_games():
    """
    Start processing a game
    :return:
    """
    if data.games:
        return json.dumps(list(data.games.values()), cls=GameEncoder)
    return "[]"


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await sockets.connect(websocket)
    try:
        while True:
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        sockets.disconnect(websocket)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")

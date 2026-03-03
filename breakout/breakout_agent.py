"""
Breakout agent WebSocket client

This script connects to the Breakout WebSocket relay server at
ws://localhost:6789/agent_breakout.  It listens for state messages from
the game and responds with action messages to move the paddle toward the
ball.  The agent uses a simple strategy: move left if the centre of the
paddle is to the right of the ball, move right if it is to the left, and
stop when aligned.  This is sufficient to play at a very high level.

Usage:

    python breakout_agent.py

Make sure the Breakout relay server (`breakout_ws_server.py`) is running and
that the game is connected to the `/game_breakout` endpoint.
"""

import asyncio
import json
import websockets


async def run_breakout_agent(host: str = "localhost", port: int = 6789) -> None:
    uri = f"ws://{host}:{port}/agent_breakout"
    async with websockets.connect(uri) as ws:
        print(f"Connected to Breakout server at {uri}")
        try:
            async for message in ws:
                data = json.loads(message)
                if data.get("type") != "state":
                    continue
                ball_x = data["ball"]["x"]
                paddle_x = data["paddleX"]
                paddle_width = data.get("paddleWidth", 80)
                paddle_centre = paddle_x + paddle_width / 2
                move = None
                tolerance = 6
                if paddle_centre < ball_x - tolerance:
                    move = "right"
                elif paddle_centre > ball_x + tolerance:
                    move = "left"
                else:
                    move = "stop"
                action = {"type": "action", "move": move}
                await ws.send(json.dumps(action))
        except websockets.ConnectionClosed:
            print("Disconnected from Breakout server")


if __name__ == "__main__":
    asyncio.run(run_breakout_agent())
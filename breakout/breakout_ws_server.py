"""
WebSocket relay server for the Breakout demo.

This server listens on localhost:6789 and allows two types of clients to connect:

* The **game** client connects at path `/game_breakout`.  It should send state
  updates containing the ball coordinates, paddle position, number of remaining
  bricks and score.  Messages from the game will be forwarded to the
  connected agent client (if present).

* The **agent** client connects at path `/agent_breakout`.  It should send
  action messages instructing the game to move the paddle left, right or
  stop, or to activate the built‑in AI.  Messages from the agent will be
  forwarded to the connected game client.

Message format is JSON.  The server does not inspect or modify payloads beyond
simple routing.

Run this server in a terminal before starting the game and agent scripts:

    python breakout_ws_server.py

The server runs indefinitely until interrupted (Ctrl+C).
"""

import asyncio
import json
from typing import Dict
import websockets
import paho.mqtt.client as mqtt

class BreakoutRelayServer:
    """Simple relay between Breakout game and agent WebSocket clients with MQTT integration."""

    def __init__(self, host: str = "localhost", port: int = 6789) -> None:
        self.host = host
        self.port = port
        self.clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        
        # MQTT Settings
        self.mqtt_broker = "localhost"
        self.mqtt_port = 1883
        self.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message
        
        # State tracking for publishing
        self.latest_state = None

    def on_mqtt_connect(self, client, userdata, flags, reason_code, properties):
        print(f"Connected to MQTT broker with result code {reason_code}")
        # Subscribe to commands topic
        client.subscribe("olink/commands")

    def on_mqtt_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode('utf-8').strip()
            
            # Remove quotes if they exist
            if payload.startswith('"') and payload.endswith('"'):
                payload = payload[1:-1]
            if payload.startswith("'") and payload.endswith("'"):
                payload = payload[1:-1]
                
            payload = payload.lower()
            
            # We also might receive JSON like {"command": "pause"}
            try:
                data = json.loads(payload)
                if isinstance(data, dict):
                     command = data.get("command", "").lower()
                     if command:
                         payload = command
            except json.JSONDecodeError:
                pass # It was just a raw string
            
            if 'pause' in payload:
                action = 'pause_game'
            elif 'resume' in payload:
                action = 'resume_game'
            else:
                action = None
                
            if action:
                print(f"Received MQTT command: {action}")
                
                # Forward to game client
                if "game" in self.clients:
                    command_msg = json.dumps({"type": "command", "action": action})
                    # Schedule the send in the asyncio event loop
                    asyncio.run_coroutine_threadsafe(
                        self.clients["game"].send(command_msg), 
                        self.loop
                    )
        except Exception as e:
            print(f"Error handling MQTT message: {e}")

    async def publish_state_loop(self):
        """Publish the game state to MQTT every 20 seconds."""
        while True:
            await asyncio.sleep(20)
            if self.latest_state:
                try:
                    payload = json.dumps({
                        "game": "breakout",
                        "score": self.latest_state.get("score", 0),
                        "level": self.latest_state.get("level", 1),
                        "lives": self.latest_state.get("lives", 5),
                        "remainingBricks": self.latest_state.get("remainingBricks", 0),
                        "status": self.latest_state.get("status", "active")
                    })
                    self.mqtt_client.publish("olink/context", payload)
                    print(f"Published state to olink/context: {payload}")
                except Exception as e:
                    print(f"Failed to publish to MQTT: {e}")

    async def handler(self, websocket, *args) -> None:
        path = args[0] if args else getattr(websocket.request, "path", "")
        role = None
        # Determine role based on path
        if path == "/game_breakout":
            role = "game"
        elif path == "/agent_breakout":
            role = "agent"
        else:
            # Unknown path; attempt to read role from message
            try:
                message = await websocket.recv()
                data = json.loads(message)
                role = data.get("role")
            except Exception:
                await websocket.close(code=4000, reason="Unknown client role")
                return
        # Register client
        self.clients[role] = websocket
        print(f"Breakout {role} client connected from {websocket.remote_address}")
        try:
            async for message in websocket:
                # Store latest state for MQTT publishing
                if role == "game":
                    try:
                        data = json.loads(message)
                        if data.get("type") == "state":
                            self.latest_state = data
                    except json.JSONDecodeError:
                        pass
                
                # Relay messages
                if role == "game" and "agent" in self.clients:
                    await self.clients["agent"].send(message)
                elif role == "agent" and "game" in self.clients:
                    await self.clients["game"].send(message)
        except websockets.ConnectionClosed:
            pass
        finally:
            if self.clients.get(role) is websocket:
                del self.clients[role]
            print(f"Breakout {role} client disconnected from {websocket.remote_address}")

    async def run(self) -> None:
        self.loop = asyncio.get_running_loop()
        
        # Connect MQTT Client (running in background thread natively via paho)
        try:
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start() # Starts network loop in background thread
        except Exception as e:
            print(f"Could not connect to MQTT broker: {e}")
            
        # Start the pub loop
        asyncio.create_task(self.publish_state_loop())

        async with websockets.serve(self.handler, self.host, self.port):
            print(f"Breakout relay server running on ws://{self.host}:{self.port}")
            await asyncio.Future()  # run forever


if __name__ == "__main__":
    server = BreakoutRelayServer()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("Stopping...")
        server.mqtt_client.loop_stop()
        server.mqtt_client.disconnect()
        print("Server stopped")
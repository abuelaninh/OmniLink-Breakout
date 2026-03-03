"""
Breakout agent V2 WebSocket client

This script connects to the Breakout WebSocket relay server at
ws://localhost:6789/agent_breakout. It listens for state messages from
the game and responds with action messages to move the paddle toward the
predicted position of the ball.

This agent is "smarter" and can handle fast balls by predicting where
the ball will intersect the paddle's Y-coordinate, factoring in wall bounces.

Usage:
    python breakout_agent_v2.py
"""

import asyncio
import json
import websockets
import time

async def run_breakout_agent(host: str = "localhost", port: int = 6789) -> None:
    uri = f"ws://{host}:{port}/agent_breakout"
    
    # Paddle width is 80, ball radius is 6, game width is 640.
    # We define padding to not strictly calculate up to the exact pixel.
    canvas_width = 640
    ball_radius = 6
    
    async with websockets.connect(uri) as ws:
        print(f"Connected to Breakout server at {uri} (V2 Predictive Agent)")
        try:
            async for message in ws:
                data = json.loads(message)
                if data.get("type") != "state":
                    continue
                
                # Get game state
                ball_x = data["ball"]["x"]
                ball_y = data["ball"]["y"]
                ball_vx = data["ball"]["vx"]
                ball_vy = data["ball"]["vy"]
                
                paddle_x = data["paddleX"]
                paddle_width = data.get("paddleWidth", 80)
                paddle_centre = paddle_x + paddle_width / 2

                target_x = paddle_centre # default to stay in middle
                
                # Predict where the ball will be at the paddle's Y coordinate (approx 480 - 10 - 10 = 460)
                # But we simplify by just tracking trajectory
                if ball_vy > 0:
                    paddle_y = 460
                    # time to reach paddle
                    time_to_hit = (paddle_y - ball_y) / ball_vy
                    
                    if time_to_hit > 0:
                        predicted_x = ball_x + (ball_vx * time_to_hit)
                        
                        # Fold predicted_x based on wall bounces
                        # We use modulo math to determine if it's going right or left after bounces
                        # fold width is (canvas_width - ball_radius)
                        fold_width = canvas_width - ball_radius * 2
                        
                        # adjust to 0-based for folding
                        adjusted_x = predicted_x - ball_radius
                        
                        num_bounces = int(abs(adjusted_x) / fold_width) if adjusted_x != 0 else 0
                        
                        rem = abs(adjusted_x) % fold_width
                        
                        if adjusted_x < 0:
                            if num_bounces % 2 == 0:
                                target_x = ball_radius + rem
                            else:
                                target_x = canvas_width - ball_radius - rem
                        else:
                            if num_bounces % 2 == 0:
                                target_x = ball_radius + rem
                            else:
                                target_x = canvas_width - ball_radius - rem
                else:
                    # ball is going up, slowly drift towards center to be safe
                    target_x = canvas_width / 2

                move = None
                tolerance = 10
                
                if paddle_centre < target_x - tolerance:
                    move = "right"
                elif paddle_centre > target_x + tolerance:
                    move = "left"
                else:
                    move = "stop"
                    
                action = {"type": "action", "move": move}
                await ws.send(json.dumps(action))
                
        except websockets.ConnectionClosed:
            print("Disconnected from Breakout server")

if __name__ == "__main__":
    asyncio.run(run_breakout_agent())

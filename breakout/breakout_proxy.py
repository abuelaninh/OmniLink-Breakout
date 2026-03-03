import asyncio
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import websockets

# Configuration
WS_URI = "ws://localhost:6789/agent_breakout"
HTTP_PORT = 5000
HOST = "localhost"

# Global Shared State
latest_game_state = {
    "command": "IDLE", # Initial state until we get data
    "payload": "Waiting for game...",
    "version": 0
}
command_queue = asyncio.Queue()

# --- HTTP Server (Threaded) ---

class ProxyRequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type='application/json'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*') # Allow browser access
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers()

    def do_GET(self):
        """Serve the latest game state."""
        if self.path == '/data':
            self._set_headers()
            # Wrap the game state in the expected format
            response_data = latest_game_state
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
        else:
            self._set_headers(404)
            self.wfile.write(b'Not Found')

    def do_POST(self):
        """Receive action commands."""
        if self.path == '/callback':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data)
                
                # Check for action
                if "action" in data:
                     # Put into the async queue for the WS loop to pick up
                     if loop:
                         asyncio.run_coroutine_threadsafe(command_queue.put(data["action"]), loop)
                
                self._set_headers()
                self.wfile.write(json.dumps({"status": "OK"}).encode('utf-8'))
            except Exception as e:
                self._set_headers(400)
                self.wfile.write(b'Error processing JSON')
        else:
            self._set_headers(404)

def run_http_server():
    server_address = (HOST, HTTP_PORT)
    httpd = HTTPServer(server_address, ProxyRequestHandler)
    print(f"[HTTP] Breakout Proxy Server running on http://{HOST}:{HTTP_PORT}")
    httpd.serve_forever()

# --- WebSocket Client (Asyncio) ---

async def ws_client():
    global latest_game_state
    
    print(f"[WS] Connecting to {WS_URI}...")
    async with websockets.connect(WS_URI) as ws:
        print("[WS] Connected!")
        
        # Task to read from WS
        async def receive_loop():
            nonlocal ws
            global latest_game_state
            async for message in ws:
                try:
                    data = json.loads(message)
                    if data.get("type") == "state":
                        # Update global state
                        # We format it to match the 'PythonState' interface request
                        latest_game_state = {
                            "command": "ACTIVATE",
                            "payload": json.dumps(data), # The agent parses this string
                            "version": int(time.time() * 1000)
                        }
                except Exception as e:
                    print(f"[WS] Error parsing: {e}")

        # Task to write to WS
        async def send_loop():
            nonlocal ws
            while True:
                # Get command from queue
                cmd = await command_queue.get()
                if cmd:
                    # Map the command to the explicit WS format 
                    msg = None
                    if cmd == "LEFT":
                        msg = {"type": "action", "move": "left"}
                    elif cmd == "RIGHT":
                        msg = {"type": "action", "move": "right"}
                    elif cmd == "STOP":
                        msg = {"type": "action", "move": "stop"}
                    elif isinstance(cmd, dict):
                        msg = cmd
                    else:
                        msg = {"type": "action", "move": cmd.lower()}
                    
                    if msg:
                        await ws.send(json.dumps(msg))
                        
        # Run both
        await asyncio.gather(receive_loop(), send_loop())

if __name__ == "__main__":
    # Get the event loop for the main thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Start HTTP Server in a separate thread
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    # Run WS Client in main thread (async)
    try:
        loop.run_until_complete(ws_client())
    except KeyboardInterrupt:
        print("Stopping...")

/**
 * Agent Tool for Breakout Demo
 * 
 * Target: Browser (EcmaScript Module / Tool Console)
 * 
 * Responsibilities:
 * 1. Poll http://localhost:5000/data for Game State.
 * 2. Parse the state (Ball X vs Paddle X).
 * 3. Decide Move (LEFT/RIGHT).
 * 4. Post Move to http://localhost:5000/callback.
 */

// Interfaces matching the Proxy's JSON structure
interface PythonState {
    command: "IDLE" | "ACTIVATE";
    payload: string; // JSON string of the GameState
    version: number;
}

interface GameState {
    type: "state";
    ball: { x: number, y: number, vx: number, vy: number };
    paddleX: number;
    paddleWidth: number;
    remainingBricks: number;
    score: number;
}

interface AgentAction {
    action: "LEFT" | "RIGHT" | "STOP";
    version: number;
    timestamp: string;
}

const API_URL = "http://localhost:5000";

let lastLogTime = 0;
const LOG_INTERVAL_MS = 500;

async function agentLoop() {
    try {
        // --- STEP 1: GET Game State ---
        const response = await fetch(`${API_URL}/data`);
        if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);

        const wrapper: PythonState = await response.json();

        if (wrapper.command === "ACTIVATE") {
            // Parse the inner payload (Game State)
            const gameState: GameState = JSON.parse(wrapper.payload);

            // --- STEP 2: Logic (The Brain) ---
            const paddleWidth = gameState.paddleWidth || 80;
            const paddleCenter = gameState.paddleX + (paddleWidth / 2);
            const ballX = gameState.ball.x;
            const tolerance = 6; // Pixels distance tolerance

            let move: "LEFT" | "RIGHT" | "STOP" = "STOP";

            if (paddleCenter < ballX - tolerance) {
                move = "RIGHT";
            } else if (paddleCenter > ballX + tolerance) {
                move = "LEFT";
            }

            if (move !== "STOP") {
                const now = Date.now();
                if (now - lastLogTime > LOG_INTERVAL_MS) {
                    console.log(`[AGENT] Ball X: ${Math.round(ballX)} | Paddle X: ${Math.round(paddleCenter)} -> Moving ${move}`);
                    lastLogTime = now;
                }

                // --- STEP 3: Act (POST Command) ---
                const actionPayload: AgentAction = {
                    action: move,
                    version: wrapper.version,
                    timestamp: new Date().toISOString()
                };

                await fetch(`${API_URL}/callback`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(actionPayload),
                });
            }
        }
    } catch (error) {
        // Log but don't crash, simple retry
        // console.error("Connection Error:", error);
    }
}

// Start the Polling Loop
console.log(`� Breakout Agent Started. Polling ${API_URL} as fast as possible...`);

// Recursive "Tight Loop"
async function runFastLoop() {
    await agentLoop();
    // Schedule next iteration immediately
    setTimeout(runFastLoop, 15); // small delay to prevent browser freeze
}

runFastLoop();

export { }; // Make this an ES module to avoid global scope clashes

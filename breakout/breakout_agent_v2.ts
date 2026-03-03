/**
 * Breakout Agent V2 for Breakout Demo
 * 
 * Target: Browser (EcmaScript Module / Tool Console) / Node.js
 * 
 * Responsibilities:
 * 1. Poll http://localhost:5000/data for Game State.
 * 2. Parse the state including ball velocities.
 * 3. Predict the interaction point with the paddle.
 * 4. Post Move to http://localhost:5000/callback.
 */

interface PythonState {
    command: "IDLE" | "ACTIVATE";
    payload: string;
    version: number;
}

interface GameState {
    type: "state";
    ball: { x: number, y: number, vx: number, vy: number };
    paddleX: number;
    paddleWidth: number;
    remainingBricks: number;
    score: number;
    level?: number;
    lives?: number;
}

interface AgentAction {
    action: "LEFT" | "RIGHT" | "STOP";
    version: number;
    timestamp: string;
}

const API_URL = "http://localhost:5000";

let lastLogTime = 0;
const LOG_INTERVAL_MS = 500;

const CANVAS_WIDTH = 640;
const BALL_RADIUS = 6;
const PADDLE_Y = 460;

async function agentLoop() {
    try {
        const response = await fetch(`${API_URL}/data`);
        if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);

        const wrapper: PythonState = await response.json();

        if (wrapper.command === "ACTIVATE") {
            const gameState: GameState = JSON.parse(wrapper.payload);

            const paddleWidth = gameState.paddleWidth || 80;
            const paddleCenter = gameState.paddleX + (paddleWidth / 2);

            const { x: ballX, y: ballY, vx: ballVx, vy: ballVy } = gameState.ball;

            let targetX = paddleCenter;

            // Prediction Logic
            if (ballVy > 0) {
                const timeToHit = (PADDLE_Y - ballY) / ballVy;
                if (timeToHit > 0) {
                    const predictedX = ballX + (ballVx * timeToHit);
                    const foldWidth = CANVAS_WIDTH - BALL_RADIUS * 2;
                    const adjustedX = predictedX - BALL_RADIUS;

                    const numBounces = Math.floor(Math.abs(adjustedX) / foldWidth);
                    const rem = Math.abs(adjustedX) % foldWidth;

                    if (adjustedX < 0) {
                        targetX = (numBounces % 2 === 0) ? BALL_RADIUS + rem : CANVAS_WIDTH - BALL_RADIUS - rem;
                    } else {
                        targetX = (numBounces % 2 === 0) ? BALL_RADIUS + rem : CANVAS_WIDTH - BALL_RADIUS - rem;
                    }
                }
            } else {
                // Ball going up, return to center
                targetX = CANVAS_WIDTH / 2;
            }

            const tolerance = 10;
            let move: "LEFT" | "RIGHT" | "STOP" = "STOP";

            if (paddleCenter < targetX - tolerance) {
                move = "RIGHT";
            } else if (paddleCenter > targetX + tolerance) {
                move = "LEFT";
            }

            if (move !== "STOP") {
                const now = Date.now();
                if (now - lastLogTime > LOG_INTERVAL_MS) {
                    console.log(`[AGENT V2] Lvl: ${gameState.level || 1} | Ball predicted X: ${Math.round(targetX)} | Moving ${move}`);
                    lastLogTime = now;
                }

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
        // silent fail on connection errors to avoid console flood
    }
}

console.log(`🚀 Breakout Predictive Agent V2 Started. Polling ${API_URL}...`);

async function runFastLoop() {
    await agentLoop();
    setTimeout(runFastLoop, 15);
}

runFastLoop();

export { }; // Make this an ES module to avoid global scope clashes

## Breakout Knowledge

### Game Rules

Breakout is a single‑player arcade game in which the player controls a horizontal
paddle at the bottom of the screen.  A ball ricochets around the
playfield, destroying a wall of coloured bricks at the top.  The rules are:

1. **Paddle movement** – The player moves the paddle left or right to intercept
   the ball.  The paddle cannot move vertically.
2. **Ball physics** – The ball bounces off the top, left and right walls, and
   reverses direction when it strikes the paddle or a brick.  If the ball
   passes below the paddle and touches the bottom wall, the player loses a
   life or the ball resets.  In this demo the ball simply resets without
   tracking lives.
3. **Brick destruction** – When the ball hits a brick, the brick is removed
   and the ball’s vertical direction is inverted.  The goal is to clear all
   bricks without allowing the ball to escape past the paddle.
4. **Winning** – Clearing all bricks completes the level.  The demo
   automatically regenerates the bricks when they are cleared so play can
   continue indefinitely.

### Strategy and Tactics

Achieving high scores in Breakout requires anticipating the ball’s trajectory
and controlling its angle of return.  Useful tips include:

* **Centre the paddle under the ball** – Always try to align the paddle’s
  centre with the ball’s horizontal position.  This maximises your chance
  of contact and gives you time to react to faster shots.
* **Use the paddle edges to change angle** – Hitting the ball on the edge of
  the paddle increases its horizontal speed and changes its reflection
  angle, allowing you to reach bricks more efficiently.
* **Control speed and spin** – Skilled players vary the impact point on the
  paddle to adjust the ball’s speed and trajectory.  Our AI does this by
  adding a small horizontal velocity component based on where the ball
  strikes the paddle.

### Demo AI Overview

In this demonstration, the right paddle AI is replaced by a moving ball and
bricks; the paddle is at the bottom and is controlled by your Omni Link agent.
The built‑in AI moves the paddle towards the ball’s horizontal position at a
constant speed, ensuring it almost never misses.  When you enable the AI via
`startAgentAI()`, the paddle automatically tracks the ball.  Alternatively,
you can implement your own agent that listens to game state via the
WebSocket relay and sends actions (`left`, `right` or `stop`) to keep the
paddle aligned with the ball.

### WebSocket Integration

To provide real‑time feedback for the agent, the Breakout game broadcasts
its state via a WebSocket connection:

* The game connects to `ws://localhost:6789/game_breakout` and sends a JSON
  message after every frame containing the ball’s position and velocity,
  the paddle’s current position and width, the number of remaining bricks
  and the current score.
* A relay server (`breakout_ws_server.py`) forwards messages between the
  game and an agent connected to `ws://localhost:6789/agent_breakout`.
* An example agent (`breakout_agent.py`) reads the state messages,
  computes whether the paddle needs to move left, right or stay in
  position, and sends action messages back to the game.  This simple
  strategy keeps the paddle aligned with the ball and demonstrates
  closed‑loop control.

By uploading this knowledge file and configuring your Omni Link agent with
appropriate commands, you can instruct it to discuss the rules and
strategies of Breakout, start the game, or activate the AI to control the
paddle via WebSocket.
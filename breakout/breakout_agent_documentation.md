# Breakout Master Agent Documentation

## Overview

This document describes the **Breakout Master** demo built for the Omni Link
platform.  Breakout is a classic single‑player arcade game where the
player uses a horizontal paddle to keep a bouncing ball in play while
destroying a wall of bricks.  In this demo the left paddle (at the bottom
of the screen) is controlled by the Omni Link agent.  The demo showcases
how the agent can observe live game state via WebSockets and issue
commands to move the paddle or start an internal AI, achieving
high‑performance play.

The Breakout Master agent’s responsibilities include:

* Greeting the user and offering to play or explain Breakout.
* Explaining the rules and basic strategies for Breakout.
* Directing the user to run the **breakout.html** demo file and start
  the relay server for state feedback.
* Optionally running a built‑in AI that keeps the paddle aligned with
  the ball.

## Game Implementation and WebSocket Integration

The game is implemented in a single HTML/JavaScript file (`breakout.html`).
It draws the playfield on a canvas and updates the game at ~60 fps using
`requestAnimationFrame()`.  Key components of the implementation include:

* **Paddle and Ball** – A horizontal paddle moves along the bottom of
  the screen.  The ball bounces off the walls, paddle and bricks.  When
  the ball touches the bottom of the screen, it resets to the centre.
* **Bricks** – A grid of bricks near the top of the screen is
  generated at the start of each round.  When hit, a brick disappears and
  the ball reverses its vertical direction.  Clearing all bricks resets
  the grid and allows continuous play.
* **Agent control** – The paddle awaits agent commands.  It can be moved
  left or right via the `moveAgentPaddle(direction)` function or
  completely automated via `startAgentAI()`, which tracks the ball.
* **WebSocket state** – After each update, the game sends a JSON
  message containing the ball and paddle positions, remaining bricks and
  score to a relay server at `ws://localhost:6789/game_breakout`.  It
  listens for incoming `action` messages with `move` fields
  (`left`, `right`, `stop`) or an `ai` message to start its internal AI.

### Relay Server

The relay server (`breakout_ws_server.py`) accepts connections on
`ws://localhost:6789`.  Clients connecting to `/game_breakout` are treated
as the game; clients connecting to `/agent_breakout` are treated as the
agent.  Messages from the game are forwarded to the agent, and vice
versa.  This simple design allows the agent to receive state updates and
return control commands in real time.

### Reference Agent

A Python reference agent (`breakout_agent.py`) demonstrates how to use the
WebSocket interface.  It connects to `/agent_breakout`, reads the game
state, and calculates whether the paddle centre is left or right of the
ball.  It then sends an `action` message to move the paddle in the
appropriate direction.  This straightforward strategy consistently
intercepts the ball and prevents misses.

## Knowledge File

The file **`breakout_knowledge.md`** contains a concise description of
Breakout’s rules, strategy tips and an overview of the demo’s AI.
Uploading this file in Omni Link’s **Knowledge** section provides the
agent with factual context to answer questions about the game.

## Agent Configuration

To configure an Omni Link agent to act as the Breakout Master, the
following elements should be set in the **Configuration** panel:

* **Main Task** – Define the agent as a Breakout expert who can discuss
  rules, offer strategy advice, and demonstrate or play the game via
  WebSocket.  Instruct the agent to direct the user to start the
  relay server and game when appropriate.
* **Available Commands** – Define commands such as:
  * `greet`: A friendly greeting that introduces the agent and explains
    its capabilities.
  * `describe_breakout_rules`: Summarises the rules of Breakout.
  * `describe_breakout_strategy`: Provides tips on effective paddle
    movement and ball control.
  * `start_breakout_game`: Instructs the user to open `breakout.html` and
    run the relay server; describes what to expect.
  * `start_breakout_ai_control`: Supplies a JavaScript snippet calling
    `startAgentAI()` to enable the built‑in paddle AI.  Optionally
    instructs the user to run `breakout_ws_server.py` and
    `breakout_agent.py` for a demonstration of WebSocket control.
* **Agent Name** – E.g. **“Breakout Master”**.
* **Agent Personality** – Friendly, attentive, and encouraging; emphasises
  skillful play and patient explanations.
* **Custom Instructions** – Remind the agent to maintain context,
  reference the current score, and provide clear guidance on launching
  the game and controlling the paddle.
* **Code Responses & Tool Usage** – Enable both to allow the agent to
  display code and use the Omni Link tools panel.

After saving these settings and uploading the knowledge file, the agent
will be ready to assist users with Breakout.

## Testing & Results

The Breakout Master agent was tested in Omni Link’s text mode.  The
following interactions were observed:

1. **Greeting and explanation** – When greeted, the agent introduced itself
   as an expert in Breakout and offered to explain the rules or start
   a game.
2. **Rule description** – Asking about the rules prompted a clear
   explanation of paddle control, ball physics, brick destruction and
   scoring.
3. **Strategy advice** – Requesting tips produced succinct guidance on
   centring the paddle, using the edges for angle control and varying
   speed.【228638949760798†screenshot】
4. **Starting the game** – Saying “Start Breakout” triggered instructions
   to run `breakout_ws_server.py` and open `breakout.html`.  The agent
   explained that the paddle would remain still until commanded and
   suggested enabling the built‑in AI or connecting a custom agent
   via WebSocket.
5. **WebSocket demonstration** – Running the relay server and the
   reference Python agent alongside the game resulted in the paddle
   automatically tracking the ball.  The game state messages showed that
   the paddle centre aligned with the ball’s horizontal position,
   preventing any missed shots.  The agent was able to describe this
   process and report the real‑time score, demonstrating closed‑loop
   control.

## Conclusion & Future Work

The Breakout Master demo illustrates how Omni Link can integrate a
web‑based game with a real‑time control loop.  By exposing simple
JavaScript functions and broadcasting the game state over WebSockets,
the agent can play Breakout at a near‑perfect level or guide the user
through the experience.  Future enhancements might include multiple
levels, varied brick arrangements, or introducing power‑ups and
additional challenge elements.  Nevertheless, the current demo achieves
its goals: clear rule explanations, robust strategy advice and live
interaction with the game via the Omni Link agent.
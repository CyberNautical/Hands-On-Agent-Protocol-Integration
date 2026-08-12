"""
Publish the interop agent over A2A.

`to_a2a()` takes an ordinary ADK agent and returns a Starlette application that
speaks A2A: it serves the agent card at the well-known URL and handles incoming
task requests. You then run it with any ASGI server.

Note this is the OTHER way to publish an A2A agent. In Section 2 we used the
CLI (`adk api_server --a2a`), which needs a hand-written agent.json. Here the
card is generated from the agent's own name and description.

  CLI + agent.json  ->  you control the card exactly; good for production
  to_a2a()          ->  zero config; good for getting something running fast

`to_a2a` is marked experimental in ADK. Fine for a workshop; check its status
before you depend on it in a customer deployment.

RUN IT
------
    scripts/run_interop.sh

Then see docs/03-lab-interop.md.
"""

from __future__ import annotations

import os

import uvicorn
from google.adk.a2a.utils.agent_to_a2a import to_a2a

from helpdesk.interop.support_agent.agent import root_agent

PORT = int(os.getenv("INTEROP_PORT", "8003"))

# The host and port are baked into the generated agent card's `url`, so they
# must match where the server is actually reachable. Get this wrong and
# discovery appears to work while every call fails.
app = to_a2a(root_agent, host="localhost", port=PORT)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=PORT)

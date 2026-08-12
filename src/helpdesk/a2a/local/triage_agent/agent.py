"""
=============================================================================
 SECTION 2 -- A2A: giving an agent colleagues
=============================================================================

Where MCP connects an agent DOWN to capabilities, A2A connects an agent ACROSS
to other agents. This file is the triage desk: it handles what it can itself,
and hands billing questions to a specialist running in a different process.

The thing to notice is how little code that takes.

  - `RemoteA2aAgent` is used exactly like a local sub-agent.
  - The only difference is that instead of a Python object, you give it a URL.
  - Everything else -- transport, task lifecycle, message format -- is the
    protocol's problem, not yours.

That is the promise of A2A: agents built by different teams, in different
languages, on different infrastructure, compose the same way local objects do.

RUN IT
------
    scripts/run_a2a_server.sh     # publishes billing_agent  on :8001
    scripts/run_web.sh            # opens the ADK dev UI     on :8002

Then see docs/02-lab-a2a.md.
"""

from __future__ import annotations

import os

from google.adk.agents.llm_agent import Agent
from google.adk.agents.remote_a2a_agent import (
    AGENT_CARD_WELL_KNOWN_PATH,
    RemoteA2aAgent,
)

from helpdesk import data
from helpdesk.azure_llm import azure_model

# ---------------------------------------------------------------------------
# Where the remote specialist lives.
#
# Two details that cost people time:
#
# 1. ALWAYS build the card URL from AGENT_CARD_WELL_KNOWN_PATH, never hardcode
#    it. The path changed between a2a-sdk versions:
#        a2a-sdk 0.3.x  ->  /.well-known/agent.json
#        a2a-sdk 1.x    ->  /.well-known/agent-card.json
#    The constant tracks whichever version you have installed.
#
# 2. The `/a2a/billing_agent` segment comes from the FOLDER NAME under the
#    directory you point `adk api_server --a2a` at. Rename the folder and this
#    URL breaks.
# ---------------------------------------------------------------------------
A2A_HOST = os.getenv("A2A_HOST", "http://localhost:8001")
BILLING_CARD_URL = f"{A2A_HOST}/a2a/billing_agent{AGENT_CARD_WELL_KNOWN_PATH}"


# ---------------------------------------------------------------------------
# The remote colleague.
#
# No model, no instructions, no tools -- because none of that lives here. This
# object is a client stub. The real agent is in another process, and we only
# know what its agent card advertises.
#
# `use_legacy` selects the A2A message format. It currently defaults to True,
# but we set it explicitly: a default that changes underneath a demo is a bad
# surprise to have in front of an audience.
# ---------------------------------------------------------------------------
billing_agent = RemoteA2aAgent(
    name="billing_agent",
    description=(
        "Remote billing specialist. Delegate anything about invoices, charges, "
        "refunds, credits or plan changes to this agent."
    ),
    agent_card=BILLING_CARD_URL,
    use_legacy=True,
)


# ---------------------------------------------------------------------------
# A local tool, for contrast.
#
# Having one local capability next to one remote agent makes the comparison
# concrete: the model picks between them the same way, and does not know or
# care that one of them crosses a network boundary.
# ---------------------------------------------------------------------------
def lookup_ticket(ticket_id: str) -> dict:
    """
    Look up any support ticket by id.

    Args:
        ticket_id: The ticket identifier, for example "TICK-1001".
    """
    ticket = data.get_ticket(ticket_id)
    if ticket is None:
        return {"found": False, "message": f"No ticket with id {ticket_id!r}."}
    return {"found": True, **ticket}


# ---------------------------------------------------------------------------
# The triage desk itself.
#
# `sub_agents=[billing_agent]` is the whole integration. ADK exposes the remote
# agent to the model as something it can transfer the conversation to, using
# the `description` above to decide when that is appropriate.
#
# Which means: the quality of your `description` is the quality of your routing.
# ---------------------------------------------------------------------------
root_agent = Agent(
    name="triage_agent",
    model=azure_model(),
    description="Front-line IT support triage desk.",
    instruction=(
        "You are the front-line triage desk for an IT support team.\n\n"
        "Routing rules:\n"
        "- Anything about invoices, charges, refunds, credits or plan changes "
        "is a billing matter. Transfer to billing_agent.\n"
        "- For any other ticket question, use the lookup_ticket tool and answer "
        "directly.\n\n"
        "When you transfer to a specialist, say so in one short sentence first "
        "so the user knows what is happening."
    ),
    tools=[lookup_ticket],
    sub_agents=[billing_agent],
)

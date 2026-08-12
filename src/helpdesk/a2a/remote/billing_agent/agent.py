"""
The BILLING SPECIALIST -- a remote agent, reached over A2A.

This is an ordinary ADK agent. There is nothing A2A-specific in this file, and
that is the point: `adk api_server --a2a` publishes it over the protocol without
the agent itself knowing or caring.

What makes it discoverable is the `agent.json` sitting next to this file. See
the comments there.
"""

from __future__ import annotations

from google.adk.agents.llm_agent import Agent

from helpdesk import data
from helpdesk.azure_llm import azure_model


def lookup_billing_ticket(ticket_id: str) -> dict:
    """
    Look up a billing-related support ticket by id.

    Args:
        ticket_id: The ticket identifier, for example "TICK-1002".
    """
    ticket = data.get_ticket(ticket_id)
    if ticket is None:
        return {"found": False, "message": f"No ticket with id {ticket_id!r}."}
    return {"found": True, **ticket}


def search_billing_guidance(query: str) -> list[dict]:
    """
    Search the knowledge base for billing guidance.

    Args:
        query: Description of the billing problem, e.g. "duplicate charge".
    """
    return data.search_kb(query, limit=2)


# ---------------------------------------------------------------------------
# ADK looks for a module-level variable named exactly `root_agent`.
# If you rename it, the agent silently will not load.
# ---------------------------------------------------------------------------
root_agent = Agent(
    name="billing_agent",
    model=azure_model(),
    description=(
        "Billing specialist. Handles invoices, duplicate or unexpected charges, "
        "refunds, credits and plan changes."
    ),
    instruction=(
        "You are the billing specialist on an IT support desk.\n\n"
        "Always ground your answer in the knowledge base before replying:\n"
        "1. If the user mentions a ticket id, call lookup_billing_ticket.\n"
        "2. Call search_billing_guidance with a short description of the issue.\n"
        "3. Give a direct answer, then state the concrete next step and any "
        "expected timeline.\n\n"
        "Be concise. You are talking to another agent, not to an end user, so "
        "skip pleasantries and return the substance."
    ),
    tools=[lookup_billing_ticket, search_billing_guidance],
)

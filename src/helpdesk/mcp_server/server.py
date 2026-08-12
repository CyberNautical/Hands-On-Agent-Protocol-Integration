"""
=============================================================================
 SECTION 1 -- MCP: giving an agent hands
=============================================================================

MCP (Model Context Protocol) is a *vertical* protocol: it connects one agent
down to the capabilities and data it needs. This file is a complete MCP server
for our IT support desk.

An MCP server exposes three kinds of thing. This server has one of each so you
can see all three side by side:

  TOOLS      Functions the model can decide to CALL. Model-controlled.
             -> lookup_ticket, search_knowledge_base, open_ticket

  RESOURCES  Read-only data the client can FETCH by URI. Application-controlled.
             -> helpdesk://tickets/open

  PROMPTS    Reusable prompt templates the USER can invoke. User-controlled.
             -> triage_prompt

That "who controls it" distinction is the part people most often miss, and it
is the thing worth remembering: tools are for the model, resources are for the
application, prompts are for the human.

RUN IT
------
    python -m helpdesk.mcp_server.server          (or scripts/run_mcp_server.sh)

Then see docs/01-lab-mcp.md.
"""

from __future__ import annotations

import os

from fastmcp import FastMCP

from helpdesk import data

# ---------------------------------------------------------------------------
# The server object
# ---------------------------------------------------------------------------
# The name and instructions are not decoration -- they are sent to clients
# during discovery. An agent uses them to decide whether this server is
# relevant at all, so write them the way you would write a tool description.
mcp = FastMCP(
    name="helpdesk",
    instructions=(
        "IT support desk. Use these tools to look up existing tickets, search "
        "the internal knowledge base for troubleshooting guidance, and raise "
        "new tickets on behalf of a user."
    ),
)


# ===========================================================================
# TOOLS -- model-controlled
# ===========================================================================
#
# Read the next function carefully, because it is the single most important
# idea in MCP for a Forward Deployed Engineer:
#
#   You never write a JSON schema. FastMCP builds it from the type hints,
#   and it uses the docstring as the description the model actually reads.
#
# That means your Python signature IS the API contract the model sees. Sloppy
# type hints and vague docstrings degrade model behaviour directly -- this is
# prompt engineering wearing a function signature.


@mcp.tool
def lookup_ticket(ticket_id: str) -> dict:
    """
    Look up a support ticket by its identifier.

    Use this whenever the user mentions a ticket number such as TICK-1001.
    Returns the ticket's subject, status, priority, category and notes.

    Args:
        ticket_id: The ticket identifier, for example "TICK-1001".
    """
    ticket = data.get_ticket(ticket_id)

    # Returning a structured error rather than raising is a deliberate choice.
    # The model can read this, understand what went wrong, and recover -- for
    # example by asking the user to re-check the number. An exception would
    # surface as a protocol-level error, which is far less useful to it.
    if ticket is None:
        return {
            "found": False,
            "ticket_id": ticket_id,
            "message": f"No ticket found with id {ticket_id!r}.",
        }

    return {"found": True, **ticket}


@mcp.tool
def search_knowledge_base(query: str, limit: int = 3) -> list[dict]:
    """
    Search the internal knowledge base for troubleshooting articles.

    Use this before answering any technical question so the answer is grounded
    in documented guidance rather than guesswork.

    Args:
        query: Natural-language description of the problem, e.g. "vpn fails after MFA".
        limit: Maximum number of articles to return. Defaults to 3.
    """
    # `limit` has a default, so FastMCP marks it optional in the generated
    # schema while `query` stays required. The schema mirrors the signature.
    return data.search_kb(query, limit=limit)


@mcp.tool
def open_ticket(subject: str, category: str, priority: str = "medium") -> dict:
    """
    Create a new support ticket.

    Only call this after confirming with the user that they want a ticket
    raised. Returns the newly created ticket including its assigned id.

    Args:
        subject: One-line summary of the problem.
        category: One of "network", "billing", "access", or "hardware".
        priority: One of "low", "medium", or "high". Defaults to "medium".
    """
    return data.create_ticket(subject=subject, category=category, priority=priority)


# ===========================================================================
# RESOURCE -- application-controlled
# ===========================================================================
#
# A resource is addressed by URI and fetched deliberately, not chosen by the
# model. Think of tools as verbs the model may invoke, and resources as nouns
# the application decides to put in front of it.
#
# Good use: pin a dashboard, a config file, or a summary into context on every
# turn without hoping the model remembers to ask for it.


@mcp.resource("helpdesk://tickets/open")
def open_tickets_resource() -> str:
    """A plain-text digest of all currently open tickets."""
    return data.open_ticket_summary()


# ===========================================================================
# PROMPT -- user-controlled
# ===========================================================================
#
# Prompts are reusable, parameterised templates that a client surfaces to the
# user -- typically as a slash-command or a menu item. They are how you ship
# your team's hard-won prompt engineering as a first-class, discoverable
# artifact instead of a wiki page nobody opens.


@mcp.prompt
def triage_prompt(ticket_id: str) -> str:
    """Generate a structured triage checklist for a given ticket."""
    return (
        f"You are triaging support ticket {ticket_id}.\n\n"
        "Work through these steps in order:\n"
        "1. Call lookup_ticket to retrieve the ticket details.\n"
        "2. Call search_knowledge_base using the ticket subject as the query.\n"
        "3. Summarise the likely root cause in one sentence.\n"
        "4. Recommend the next concrete action for the support engineer.\n"
        "5. State whether this should be escalated to a specialist team."
    )


# ===========================================================================
# ENTRY POINT
# ===========================================================================

if __name__ == "__main__":
    # -----------------------------------------------------------------------
    # Two transports, two different jobs:
    #
    #   stdio  The client launches the server as a subprocess and talks over
    #          stdin/stdout. This is how desktop tools like Claude Desktop and
    #          most IDE integrations run MCP servers. One client, one process.
    #
    #   http   Streamable HTTP. The server is a normal web service that many
    #          clients can reach over the network. This is what you deploy.
    #
    # We use HTTP so the notebook, curl, and the ADK agent can all talk to the
    # same running server at once -- which stdio cannot do.
    # -----------------------------------------------------------------------
    #
    # stateless_http=True is the flag worth understanding.
    #
    # By default FastMCP's HTTP transport keeps a per-client session in memory
    # on the instance that created it. That is fine for one process, but it
    # breaks the moment you scale out: the client connects to instance A, the
    # load balancer sends the next request to instance B, and instance B has
    # never heard of that session.
    #
    # You might reach for sticky sessions. They do not reliably work here --
    # many MCP clients use fetch() internally and do not round-trip cookies, so
    # the load balancer has nothing to pin on.
    #
    # In stateless mode each request carries everything needed to serve it, so
    # any instance can answer any request. Ordinary round-robin load balancing
    # works, and the server becomes serverless-friendly.
    #
    # This is also the direction the protocol itself is moving -- see
    # docs/04-stateless-mcp.md.
    #
    # The trade-off: features that genuinely need a live session (sampling and
    # elicitation, where the server calls back to the client mid-request) are
    # not available. This workshop deliberately avoids them.
    # -----------------------------------------------------------------------
    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=int(os.getenv("MCP_PORT", "8000")),
        stateless_http=True,
    )

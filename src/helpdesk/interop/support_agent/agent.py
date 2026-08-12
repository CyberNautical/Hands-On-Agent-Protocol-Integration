"""
=============================================================================
 SECTION 3 -- INTEROP: both protocols in one agent
=============================================================================

Sections 1 and 2 taught the protocols separately. Here they meet.

This one agent:

  * CONSUMES an MCP server  -- it gets its tools from the helpdesk MCP server
                               running on :8000, over Streamable HTTP.

  * IS PUBLISHED over A2A   -- other agents can discover and call it as a peer.
                               (see serve.py next door)

Which is the whole mental model in a single object:

        MCP is how this agent gets its HANDS.
        A2A is how this agent gets COLLEAGUES.

They are different layers, not competing choices. Almost every real deployment
you will build for a customer uses both.

The practical thing to notice: the agent code below contains no MCP client
logic. It does not know how many tools exist, what they are called, or what
arguments they take. It learns all of that at startup by asking the server.
Add a tool to the MCP server, restart, and this agent can use it -- with no
change to this file.
"""

from __future__ import annotations

import os

from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset

from helpdesk.azure_llm import azure_model

# ---------------------------------------------------------------------------
# Where the MCP server is.
#
# FastMCP's HTTP transport mounts at /mcp/ by default, so the full endpoint is
# host:port/mcp/ -- a missing trailing path here is a common 404.
# ---------------------------------------------------------------------------
MCP_URL = os.getenv("MCP_URL", "http://127.0.0.1:8000/mcp/")


# ---------------------------------------------------------------------------
# McpToolset is the bridge.
#
# At startup it connects to the MCP server, calls tools/list, and turns every
# tool it finds into an ADK tool the model can call. The JSON schemas that
# FastMCP generated from our Python type hints in Section 1 become the function
# declarations sent to the model here.
#
# So the chain is:
#     Python type hints -> MCP JSON schema -> ADK tool -> model function call
#
# You wrote the first link. The protocol handled the rest.
#
# `tool_filter` is optional but worth using in production: it whitelists which
# of the server's tools this agent may call, so adding a destructive tool to a
# shared MCP server does not silently hand it to every agent on the network.
# ---------------------------------------------------------------------------
helpdesk_tools = McpToolset(
    connection_params=StreamableHTTPConnectionParams(url=MCP_URL),
    tool_filter=["lookup_ticket", "search_knowledge_base", "open_ticket"],
)


root_agent = LlmAgent(
    name="support_agent",
    model=azure_model(),
    description=(
        "Full-service IT support agent. Looks up tickets, searches the "
        "knowledge base, and raises new tickets."
    ),
    instruction=(
        "You are an IT support agent. Your tools come from the helpdesk MCP "
        "server.\n\n"
        "For any technical question:\n"
        "1. If a ticket id is mentioned, call lookup_ticket first.\n"
        "2. Search the knowledge base before answering.\n"
        "3. Answer from what you found, and say which article you used.\n"
        "4. Only call open_ticket if the user explicitly asks for a ticket."
    ),
    tools=[helpdesk_tools],
)

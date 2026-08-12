#!/usr/bin/env bash
# Section 3 -- the interop agent: consumes MCP, published over A2A, on :8003
#
# Requires the MCP server from Section 1 to be running on :8000, because this
# agent fetches its tool list from it at startup.
set -euo pipefail
cd "$(dirname "$0")/.."

export PYTHONPATH="${PWD}/src"
export INTEROP_PORT="${INTEROP_PORT:-8003}"

echo "Interop agent ->  http://localhost:${INTEROP_PORT}"
echo "Agent card    ->  http://localhost:${INTEROP_PORT}/.well-known/agent-card.json"
echo "Needs the MCP server on :8000."
echo

exec uv run python -m helpdesk.interop.support_agent.serve

#!/usr/bin/env bash
# Section 1 -- start the MCP server on :8000
#
# PYTHONPATH=src is how `import helpdesk` resolves. The repo is run in place
# rather than installed as a package, which keeps setup to a single uv sync.
set -euo pipefail
cd "$(dirname "$0")/.."

export PYTHONPATH="${PWD}/src"
export MCP_PORT="${MCP_PORT:-8000}"

echo "MCP server  ->  http://127.0.0.1:${MCP_PORT}/mcp/"
echo "Press Ctrl-C to stop."
echo

exec uv run python -m helpdesk.mcp_server.server

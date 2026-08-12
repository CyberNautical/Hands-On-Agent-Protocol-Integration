#!/usr/bin/env bash
# Section 2 -- publish billing_agent over A2A on :8001
#
# `--a2a` is what turns the API server into an A2A server. It scans the given
# directory for agent folders and publishes each one that has an agent.json.
#
# If your agent does not appear, the cause is almost always a missing or
# misnamed agent.json. The file must be named exactly that.
set -euo pipefail
cd "$(dirname "$0")/.."

export PYTHONPATH="${PWD}/src"
A2A_PORT="${A2A_PORT:-8001}"

echo "A2A server  ->  http://localhost:${A2A_PORT}/a2a/billing_agent"
echo "Agent card  ->  http://localhost:${A2A_PORT}/a2a/billing_agent/.well-known/agent-card.json"
echo "Press Ctrl-C to stop."
echo

exec uv run adk api_server --a2a --port "${A2A_PORT}" src/helpdesk/a2a/remote

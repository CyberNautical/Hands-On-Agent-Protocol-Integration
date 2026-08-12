#!/usr/bin/env bash
# Section 2 -- the ADK dev UI on :8002, serving triage_agent
#
# Point this at the LOCAL agents directory only. triage_agent lives here;
# billing_agent does not, because from triage's point of view billing is a
# remote peer reached over A2A, not a local module it imports.
#
# That separation is the point of the whole section. Keep the two directories
# apart and it stays obvious.
set -euo pipefail
cd "$(dirname "$0")/.."

export PYTHONPATH="${PWD}/src"
WEB_PORT="${WEB_PORT:-8002}"

echo "ADK dev UI  ->  http://127.0.0.1:${WEB_PORT}"
echo "Make sure run_a2a_server.sh is already running on :8001."
echo

exec uv run adk web --port "${WEB_PORT}" src/helpdesk/a2a/local

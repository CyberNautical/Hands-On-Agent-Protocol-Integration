# Troubleshooting

Start here:

```bash
uv run python scripts/preflight.py
```

It checks versions, makes a real Azure call, tests the ports, and validates
`agent.json`. Most problems below are things it catches.

---

## Azure / model

### `AzureConfigError: missing ... AZURE_API_KEY`

No `.env`, or it's incomplete.

```bash
cp .env.example .env
```

Then fill in all four values.

### 404 from Azure

Two common causes.

**Deployment name vs model name.** `AZURE_OPENAI_DEPLOYMENT` must be the name
*you* gave the deployment in the Azure portal, which is often not the model
name. If you deployed `gpt-4o` and named the deployment `gpt-4o-prod`, the
value is `gpt-4o-prod`.

**Wrong API surface.** AI Foundry resources (`*.services.ai.azure.com`) serve
`/openai/v1/` and return `Resource not found` for the older
`/openai/deployments/...` route — no matter how recent the dated API version
is. Set:

```dotenv
AZURE_API_VERSION=v1
```

Classic `*.openai.azure.com` resources keep using a dated version such as
`2024-10-21`. Note that only `v1`, `latest` and `preview` select the new route;
of those, `v1` is the one that works with LiteLLM 1.97.

Also check `AZURE_API_BASE` — scheme included, no trailing path:
`https://my-resource.openai.azure.com`

### Preflight fails but the same call works standalone

Something already exported `AZURE_*` into your shell. `.env` is loaded with
`override=False`, so real environment variables win — a stale
`AZURE_API_VERSION` from an earlier `source .env` will quietly beat the value
you just edited.

```bash
env | grep AZURE_    # should be empty
```

Open a fresh terminal, or unset them.

### 401 from Azure

Wrong key, or the key belongs to a different resource than `AZURE_API_BASE`.

### The model ignores the tools entirely

`AZURE_API_VERSION` too old to support tool calling. Use `2024-10-21` or newer.
The failure mode is silent — the model just answers from memory.

---

## Keyless auth (Entra ID / managed identity)

Set `AZURE_AUTH_MODE=entra` (or just leave `AZURE_API_KEY` blank) to
authenticate as an Azure identity instead of with a shared key. Preflight
prints the mode it resolved, so start there.

### `AzureConfigError: Keyless auth needs the azure-identity package`

The dependency is optional:

```bash
uv sync --group entra
```

### `CredentialUnavailableError` / `DefaultAzureCredential failed to retrieve a token`

Nothing is signed in. Locally:

```bash
az login
```

On Azure compute, confirm a managed identity is actually assigned to the
resource. For a **user-assigned** identity you must also set `AZURE_CLIENT_ID`
to that identity's client ID — otherwise the credential does not know which one
to use.

### 401 or 403 with keyless auth

The token is fine, the permissions are not. Grant the identity the
**Cognitive Services OpenAI User** role on the Azure OpenAI resource:

```bash
az role assignment create \
  --role "Cognitive Services OpenAI User" \
  --assignee <object-id-or-upn> \
  --scope <resource-id-of-the-azure-openai-resource>
```

Role assignments can take a few minutes to propagate.

### It used a key when you expected keyless (or vice versa)

`AZURE_AUTH_MODE` defaults to `auto`, which prefers the key whenever
`AZURE_API_KEY` is set — including a stale value left in your shell. Set the
mode explicitly (`key` or `entra`) to remove the ambiguity.

---

## MCP

### `Connection refused` on :8000

The server isn't running. `./scripts/run_mcp_server.sh` in another terminal.

### 404 at the MCP endpoint

Missing path. FastMCP's HTTP transport mounts at `/mcp/`, so the URL is
`http://127.0.0.1:8000/mcp/` — not `http://127.0.0.1:8000/`.

### `ModuleNotFoundError: No module named 'helpdesk'`

`PYTHONPATH` isn't set. The run scripts export it; if you're running Python
directly:

```bash
export PYTHONPATH="$PWD/src"
```

In notebooks, the devcontainer sets it. Outside the devcontainer:

```python
import sys; sys.path.insert(0, "src")
```

### Interop agent fails at startup

It fetches its tool list from MCP at boot. Start the MCP server first.

---

## A2A

### The agent isn't published — no error, nothing there

**Check for `agent.json`.** `adk api_server --a2a` only publishes folders that
contain a file named exactly that. Wrong name, wrong directory, or missing
entirely → the server starts cleanly and publishes nothing.

```bash
ls src/helpdesk/a2a/remote/billing_agent/agent.json
```

### 404 fetching the agent card

Path differs by `a2a-sdk` version:

- 1.x → `/.well-known/agent-card.json`
- 0.3.x → `/.well-known/agent.json`

In code, always use `AGENT_CARD_WELL_KNOWN_PATH` instead of hardcoding.

### Card fetches fine but calls fail

The `url` field in the card is absolute. If the card says `localhost:8001` and
you're calling from somewhere that can't reach that address, discovery works
and invocation doesn't.

In this workshop: keep everything inside the Codespace. In production: make the
URL configurable per environment.

### `triage_agent` doesn't appear in `adk web`

- Missing `__init__.py` with `from . import agent`
- The module-level variable isn't named exactly `root_agent`
- You pointed `adk web` at the wrong directory (it should be
  `src/helpdesk/a2a/local`)

### Triage answers billing questions itself instead of delegating

The model didn't think it needed to. Sharpen the `description` on the
`RemoteA2aAgent` and the routing rules in triage's `instruction`. This is a
prompt problem, not a protocol problem — and it's a genuinely useful thing to
demonstrate live.

---

## Ports

### `Address already in use`

Something from an earlier run is still up.

```bash
lsof -ti:8000 | xargs -r kill    # or 8001 / 8002 / 8003
```

Port map: MCP `8000`, A2A `8001`, dev UI `8002`, interop `8003`.

---

## Environment

### `uv: command not found`

Outside the devcontainer:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Dependency resolution fails

```bash
rm -rf .venv && uv sync
```

`fastmcp==3.4.7` and `google-adk==2.6.3` are pinned deliberately — they request
compatible `mcp` ranges, which is what lets them share one environment. Bumping
`fastmcp` to 4.x will break that; see [04 — Stateless MCP](04-stateless-mcp.md).

### Notebook can't find the kernel

Select the workspace interpreter: `.venv/bin/python`.

---

## Still stuck

Version drift is the usual culprit for anything not listed here. Compare:

```bash
uv run python -c "import importlib.metadata as m; print(m.version('fastmcp'), m.version('google-adk'))"
```

Expected: `3.4.7 2.6.3`.

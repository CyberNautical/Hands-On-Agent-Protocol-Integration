# Troubleshooting

Find your symptom. Apply the fix.

**Before anything else:**

```bash
uv run python scripts/preflight.py
```

It checks the five things that usually break, and tells you which one it is.

---

## Setup

### `uv: command not found`

The Codespace installs `uv` during build. If it is missing, the build did not
finish — rebuild the Codespace (**Command Palette → Codespaces: Rebuild
Container**), or install it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### `ModuleNotFoundError: No module named 'fastmcp'`

Dependencies are not installed, or you ran Python outside the project
environment.

```bash
uv sync
```

Then always start commands with `uv run`, or use the provided scripts.

### `Permission denied: ./scripts/run_mcp_server.sh`

```bash
chmod +x scripts/*.sh
```

### `bad interpreter: /usr/bin/env bash^M`

The file has Windows line endings. `.gitattributes` should prevent this, but if
it happens:

```bash
sed -i 's/\r$//' scripts/*.sh
```

---

## Azure

Every one of these comes from `.env`. Open it — the comments explain each
value. `preflight.py` prints which auth mode it resolved, so start there.

| Error | Cause | Fix |
|---|---|---|
| `404 Not Found` | wrong deployment name, or wrong API version | see below |
| `401` / `403` | wrong key, or missing role for keyless | see below |
| `429 Too Many Requests` | quota exhausted | wait, or raise quota in the portal |
| `Connection refused` on Azure | wrong endpoint URL | `AZURE_API_BASE` needs the scheme and **no trailing path** |
| model ignores tools | API version too old | use `v1`, or `2024-10-21` or newer |

### The 404 — two causes

This is the most common failure in the entire workshop.

**1. Deployment name vs model name.** `AZURE_OPENAI_DEPLOYMENT` is the name
**you chose** when creating the deployment, not the model name. Deploy `gpt-4o`
and call it `gpt-4o-prod`, and the correct value is `gpt-4o-prod`. Check it in
the Azure portal under **Deployments**.

**2. Wrong API surface.** The two kinds of Azure resource use different routes,
and a recent date does not help:

| Your endpoint looks like | Set `AZURE_API_VERSION` to |
|---|---|
| `*.services.ai.azure.com` (AI Foundry) | `v1` |
| `*.openai.azure.com` (classic) | `2024-10-21` or newer |

If a dated version gives `Resource not found`, try `v1`.

Also check `AZURE_API_BASE` has the scheme and no trailing path. If the portal
showed you `.../openai/v1/responses`, drop everything from `/openai` onward:

```
correct    https://my-resource.openai.azure.com
wrong      https://my-resource.openai.azure.com/openai/v1/responses
```

### Preflight fails, but the same call works elsewhere

Something already exported `AZURE_*` into your shell. `.env` does not override
real environment variables, so a stale value quietly wins over the one you just
edited.

```bash
env | grep AZURE_    # should be empty
```

Open a fresh terminal, or unset them.

---

## Keyless auth (optional)

Only relevant if you left `AZURE_API_KEY` blank, or set
`AZURE_AUTH_MODE=entra`.

| Error | Fix |
|---|---|
| `Keyless auth needs the azure-identity package` | `uv sync --group entra` |
| `CredentialUnavailableError`, or failed to get a token | Nothing is signed in — run `az login`, or assign a managed identity |
| `401` / `403` with a valid token | Missing role — see below |
| It used a key when you wanted keyless | `AZURE_AUTH_MODE` defaults to `auto`, which prefers a key whenever one is set. Set it to `entra` explicitly |

The identity needs the **Cognitive Services OpenAI User** role on the Azure
OpenAI resource:

```bash
az role assignment create \
  --role "Cognitive Services OpenAI User" \
  --assignee <object-id-or-upn> \
  --scope <resource-id-of-the-azure-openai-resource>
```

Role assignments take a few minutes to take effect.

For a **user-assigned** managed identity you must also set `AZURE_CLIENT_ID` to
that identity's client ID — otherwise Azure does not know which one to use.

---

## Lab 1 — MCP

### `404` when connecting to the MCP server

The URL must end in `/mcp/`:

```
correct    http://127.0.0.1:8000/mcp/
wrong      http://127.0.0.1:8000
```

### `Connection refused` on port 8000

The server is not running. In another terminal:

```bash
./scripts/run_mcp_server.sh
```

### `Address already in use`

Something is already on that port:

```bash
lsof -ti:8000 | xargs kill -9
```

### The notebook hangs on a cell

Restart the kernel (**Kernel → Restart**), confirm the server is still running,
and re-run from the top of the section.

---

## Lab 2 — A2A

### The agent card returns 404

Two possible causes.

**1. Missing or misnamed file.** Each agent folder needs a file named exactly
`agent.json`, in the folder itself:

```
src/helpdesk/a2a/remote/billing_agent/
    agent.json      <- must be exactly this name, exactly here
    agent.py
    __init__.py
```

If it is missing or named `agent-card.json`, the server starts normally,
reports nothing, and publishes no agents.

**2. Different path in your SDK version.**

```bash
curl -s http://localhost:8001/a2a/billing_agent/.well-known/agent-card.json   # a2a-sdk 1.x
curl -s http://localhost:8001/a2a/billing_agent/.well-known/agent.json        # a2a-sdk 0.3.x
```

### Triage never delegates to billing

- Is the billing server actually running on 8001?
- Is the question clearly about billing? Try *"Why was I charged twice this
  month?"*
- Check `BILLING_CARD_URL` in
  `src/helpdesk/a2a/local/triage_agent/agent.py`.
- Weak `description` text on the remote agent. The model reads it to decide —
  vague text means no delegation.

### `adk web` shows no agents

Run it from the repository root. It looks for agent folders relative to the
current directory. `./scripts/run_web.sh` handles this for you.

---

## Lab 3 — Interop (⭐ optional bonus lab)

### The agent fails to start

It fetches its tools from MCP at startup, so the MCP server must already be
running:

```bash
./scripts/run_mcp_server.sh
```

### It starts but has no tools

Check `MCP_URL` in `src/helpdesk/interop/support_agent/agent.py` ends in
`/mcp/`, and that the names in `tool_filter` match the tools the server
actually offers.

---

## Codespaces

### A port is not forwarded

Open the **Ports** panel and confirm 8000–8003 are listed. Add any missing one
manually.

### A URL works in the terminal but not the browser

Use the forwarded URL from the **Ports** panel, not `localhost`. Agent cards
contain absolute URLs, so a mismatch shows up as discovery succeeding and calls
failing.

---

## Still stuck?

1. Run `uv run python scripts/preflight.py` and read every line.
2. Restart the affected server. Most failures are a stale process.
3. Confirm your `.env` values are filled in, and that `env | grep AZURE_`
   returns nothing unexpected.
4. Rebuild the Codespace — it is a clean slate and takes a couple of minutes.

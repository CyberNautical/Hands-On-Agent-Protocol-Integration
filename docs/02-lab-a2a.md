# 02 — A2A with Google ADK

**Time: ≤ 5 minutes.**

**Goal:** understand how one agent discovers and delegates to another agent
running in a different process.

You can stop the MCP server from Section 1 — this section doesn't use it.

---

## Step 1 — Publish the billing agent (45s)

```bash
./scripts/run_a2a_server.sh
```

**You should see** uvicorn start on `:8001`.

Leave it running. New terminal for the rest.

### What just happened

`adk api_server --a2a` scanned `src/helpdesk/a2a/remote/` and published every
agent folder it found that contains a file named exactly **`agent.json`**.

> **The single most common failure in A2A work:** no `agent.json`, or it's
> named `agent-card.json`, or it's one directory too high. The server starts
> normally, reports no error, and publishes nothing. If your agent isn't
> reachable, check this first. `preflight.py` checks it for you.

---

## Step 2 — Read the agent card (90s)

Open `notebooks/02_a2a_inspector.ipynb` and run the first cells.

**You should see** the card JSON, with `name`, `url`, `capabilities`, and a
`skills` array.

### The point

That's all of A2A discovery. One JSON document at a well-known URL.

No registry. No service mesh. No broker. If you can GET that file, you can work
with the agent.

Three fields matter:

- **`skills`** — natural-language descriptions of what it does. This is what
  the *calling* agent's model reads to decide whether to delegate here. Same
  lesson as MCP docstrings: if it's vague, delegation won't happen.
- **`capabilities`** — protocol features like streaming.
- **`url`** — where work actually goes.

> **Deployment gotcha, worth flagging now:** `url` is absolute. Publish this
> card behind a different hostname and discovery still succeeds while every
> call fails. That's why this workshop keeps traffic inside the Codespace
> rather than routing through public forwarded URLs.

---

## Step 3 — Send work by hand (45s)

Run the `message/send` cell.

**You should see** a JSON-RPC response containing the billing agent's answer.

No framework was involved. A2A over HTTP is JSON-RPC with a `message` object.
That's it — which is exactly why a Python agent can delegate to a Java one.

---

## Step 4 — Watch an agent do it (90s)

Second terminal:

```bash
./scripts/run_web.sh
```

Open http://127.0.0.1:8002, choose **triage_agent**, and ask:

> *Why was I charged twice this month?*

**You should see** triage recognise this as billing and hand off. Expand the
trace in the UI to watch the delegation.

Then ask something it should keep:

> *What's the status of ticket TICK-1001?*

**You should see** it answer directly with its own local tool — no handoff.

That contrast is the lesson. The model routes based on the descriptions.

---

## Step 5 — Read the source (30s)

`src/helpdesk/a2a/local/triage_agent/agent.py`:

```python
billing_agent = RemoteA2aAgent(
    name="billing_agent",
    description="Handles billing enquiries: invoices, refunds, charges.",
    agent_card=BILLING_CARD_URL,
)

root_agent = Agent(
    ...
    tools=[lookup_ticket],
    sub_agents=[billing_agent],
)
```

A remote agent goes into `sub_agents` exactly like a local one. The model
cannot tell the difference — and that's the abstraction A2A is selling.

Also open `src/helpdesk/a2a/remote/billing_agent/agent.py` and notice what
isn't there: **nothing A2A-specific**. It's a plain ADK agent. A2A was added by
dropping a JSON file next to it.

---

## MCP vs A2A, side by side

| | MCP | A2A |
|---|---|---|
| Connects | agent → capability | agent → agent |
| The other side is | a function | an autonomous agent |
| Discovery via | `tools/list` | agent card at a well-known URL |
| You get back | a return value | a delegated result |
| Reach for it when | the agent needs to *do* something | the work belongs to someone else |

---

## Checkpoint

You can now answer:

- How does an agent find another agent? → fetch its card.
- What makes an ADK agent A2A-reachable? → an `agent.json` next to it.
- How does a caller use a remote agent? → `RemoteA2aAgent` in `sub_agents`.
- What decides whether delegation happens? → the skill descriptions.

**Next:** [03 — Interop](03-lab-interop.md) — both at once.

# 02 — A2A with Google ADK

**Time: 5 minutes**

**Goal:** see how one agent finds another agent running in a different process,
and hands work to it.

You can stop the MCP server from Lab 1 — this lab does not use it.

---

## Step 1 — Publish the billing agent (45s)

```bash
./scripts/run_a2a_server.sh
```

You should see a server start on port `8001`.

Leave it running and open a new terminal.

### What just happened

The command scanned `src/helpdesk/a2a/remote/` and published every folder that
contains a file named exactly **`agent.json`**.

> **The most common A2A mistake:** that file is missing, named something else
> (`agent-card.json`), or one folder too high. The server starts normally,
> reports no error, and publishes nothing at all.
>
> If an agent is not reachable, check this first. `preflight.py` checks it for
> you.

---

## Step 2 — Read the agent card (90s)

Open `notebooks/02_a2a_inspector.ipynb` and run **sections 1 and 2**.

You should see the card as JSON — a `name`, a `capabilities` object, a `skills`
array, and a URL.

### What just happened

That is all of A2A discovery: **one JSON file at a predictable address.**

No registry. No service mesh. No broker. If you can fetch that file, you can
work with the agent.

Three fields carry the weight:

- **`skills`** — plain-language descriptions of what this agent does. The
  **calling** agent's model reads these to decide whether to delegate. Same
  lesson as MCP docstrings: vague text means delegation never happens.
- **`capabilities`** — which protocol features it supports, such as streaming.
- **the URL** — where work actually gets sent.

> **Deployment gotcha:** that URL is absolute. Publish the card behind a
> different hostname and discovery still succeeds while every call fails. This
> is why the workshop keeps all traffic inside the Codespace.

---

## Step 3 — Send work by hand (45s)

Run **section 3**.

You should see a JSON response containing the billing agent's answer.

No framework was involved — just an HTTP POST carrying JSON. That is exactly
why a Python agent can delegate to a Java one.

---

## Step 4 — Watch an agent delegate (90s)

In a new terminal:

```bash
./scripts/run_web.sh
```

Open http://127.0.0.1:8002, pick **triage_agent**, and ask:

> *Why was I charged twice this month?*

You should see triage recognise this as billing and hand it off. Expand the
trace in the UI to watch the delegation happen.

Now ask something it should keep for itself:

> *What's the status of ticket TICK-1001?*

You should see it answer directly using its own tool — no handoff.

**That contrast is the whole lesson.** Nothing routes these requests. The model
chose, based on the descriptions it read.

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

A remote agent is listed in `sub_agents` exactly like a local one. The model
cannot tell the difference — and that is precisely what A2A is selling.

Now open `src/helpdesk/a2a/remote/billing_agent/agent.py` and notice what is
**not** there: nothing about A2A at all. It is an ordinary agent. It became
reachable because a JSON file sits next to it.

---

## MCP vs A2A

| | MCP | A2A |
|---|---|---|
| Connects | agent → tool | agent → agent |
| The other side is | a function | another agent |
| You discover it by | asking for the tool list | fetching the agent card |
| You get back | a return value | a delegated answer |
| Use it when | the agent needs to *do* something | the work belongs to someone else |

---

## Checkpoint

You can now answer:

- **How does an agent find another agent?** It fetches its card.
- **What makes an agent A2A-reachable?** An `agent.json` file beside it.
- **How does a caller use a remote agent?** `RemoteA2aAgent` in `sub_agents`.
- **What decides whether delegation happens?** The skill descriptions.

**Next:** [03 — Both together](03-lab-interop.md) — ⭐ optional bonus lab, or
skip ahead to [04 — Stateless MCP](04-stateless-mcp.md).

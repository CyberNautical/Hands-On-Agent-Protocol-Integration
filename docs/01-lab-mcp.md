# 01 — MCP with FastMCP

**Time: ≤ 5 minutes.**

**Goal:** understand how an agent finds out what a server can do, without
importing any of the server's code.

---

## Step 1 — Start the server (30s)

```bash
./scripts/run_mcp_server.sh
```

**You should see:**

```
MCP server  ->  http://127.0.0.1:8000/mcp/
```

followed by FastMCP's banner and `Uvicorn running on http://127.0.0.1:8000`.

Leave it running. Open a **second terminal** for everything below.

---

## Step 2 — Discover it (90s)

Open `notebooks/01_mcp_inspector.ipynb` and run the cells down to section 2.

**You should see** three tools listed:

```
lookup_ticket            Look up a single support ticket by its id.
search_knowledge_base    Search the IT knowledge base for articles...
open_ticket              Create a new support ticket.
```

Then the JSON schema for `lookup_ticket`.

### The point

Nobody wrote that schema. `server.py` contains this:

```python
@mcp.tool
def lookup_ticket(ticket_id: str) -> dict:
    """Look up a single support ticket by its id.
    ...
    """
```

FastMCP read the type hints and the docstring and generated the schema. The
agent then read the schema over HTTP.

**Say this out loud, because it's the thing people miss:** the docstring is not
documentation. It is the prompt the model uses to decide whether to call this
tool. A vague docstring is a bug that presents as "the agent ignores my tool."

---

## Step 3 — Call it (60s)

Run the `call_tool` cells.

**You should see** ticket `TICK-1001` returned as a dict, then a knowledge base
search returning matching article titles.

This is exactly the request a model produces: a tool name and a dict of
arguments. Nothing else.

---

## Step 4 — The other two primitives (60s)

Run the `list_resources` / `list_prompts` cells.

**You should see** `helpdesk://tickets/open` and `triage_prompt`.

MCP has three primitives, and they differ by **who decides**:

| Primitive | Controlled by | Feels like | Here |
|---|---|---|---|
| **Tool** | the model | a function call | `lookup_ticket` |
| **Resource** | the application | a file read | `helpdesk://tickets/open` |
| **Prompt** | the user | a slash command | `triage_prompt` |

Almost everyone builds only tools and then wonders why their agent's context is
a mess. Resources are for context you want loaded, not decided on. Prompts are
for workflows you want a human to trigger deliberately.

---

## Step 5 — Stateless (90s)

Run the final `httpx` cells.

**You should see** `Mcp-Session-Id returned: <none>`, and then a second,
completely independent POST that returns a real tool result anyway.

### Why this is the slide the customer's architect cares about

Original MCP required a session: initialize, get an `Mcp-Session-Id`, send it
on every later request. Which means every request in a conversation must land
on the same process.

One laptop: fine. Behind a load balancer: a problem. And sticky sessions don't
rescue you, because many MCP clients call the server with a bare `fetch()` and
never return cookies — the load balancer has nothing to pin on.

Our server sets `stateless_http=True`. Any instance can serve any request. That
means plain round-robin, autoscaling, and serverless all just work.

More in [04 — Stateless MCP](04-stateless-mcp.md).

---

## Step 6 — Read the source (60s)

Open `src/helpdesk/mcp_server/server.py`.

It is roughly 40 lines of actual code and a lot of commentary. The commentary
is the lab.

---

## Checkpoint

You can now answer:

- How does an agent learn what a server offers? → it asks; `tools/list`.
- Where do tool schemas come from? → type hints and docstrings.
- Why three primitives? → different actors decide to use them.
- Why does stateless matter? → it's the difference between one box and a fleet.

**Next:** [02 — A2A](02-lab-a2a.md)

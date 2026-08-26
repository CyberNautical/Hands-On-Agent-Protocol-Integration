# 01 — MCP with FastMCP

**Time: 5 minutes**

**Goal:** see how an agent discovers what a separate program can do — without
importing any of that program's code.

Unfamiliar term? Check the [glossary](glossary.md).

---

## Step 1 — Start the server (30s)

```bash
./scripts/run_mcp_server.sh
```

You should see:

```
MCP server  ->  http://127.0.0.1:8000/mcp/
```

followed by `Uvicorn running on http://127.0.0.1:8000`.

Leave it running and **open a second terminal** for everything below.

> The address ends in `/mcp/`. That trailing path matters — plain
> `http://127.0.0.1:8000` returns a 404.

---

## Step 2 — Discover the tools (90s)

Open `notebooks/01_mcp_inspector.ipynb` and run **sections 1 and 2**.

You should see three tools:

```
lookup_ticket            Look up a single support ticket by its id.
search_knowledge_base    Search the IT knowledge base for articles...
open_ticket              Create a new support ticket.
```

then the schema for `lookup_ticket`.

### What just happened

The notebook connected over HTTP and asked *"what can you do?"*. It knew
nothing about the server beforehand.

And nobody wrote that schema by hand. `server.py` contains only this:

```python
@mcp.tool
def lookup_ticket(ticket_id: str) -> dict:
    """Look up a single support ticket by its id."""
```

FastMCP read the type hint (`ticket_id: str`) and the docstring, then generated
the schema from them.

> **The thing most people miss:** the docstring is not documentation. It is the
> text the model reads when deciding whether to call this tool. A vague
> docstring shows up later as "the agent ignores my tool."

---

## Step 3 — Call a tool (60s)

Run **section 3**.

You should see ticket `TICK-1001` come back as a dictionary, then a knowledge
base search returning article titles.

This is exactly what a model produces when it wants a tool: a name and a
dictionary of arguments. Nothing more.

---

## Step 4 — The other two primitives (60s)

Run **section 4**.

You should see `helpdesk://tickets/open` and `triage_prompt`.

MCP has three primitives. They differ by **who decides to use them**:

| Primitive | Chosen by | Like | In this lab |
|---|---|---|---|
| **Tool** | the model | calling a function | `lookup_ticket` |
| **Resource** | the application | reading a file | `helpdesk://tickets/open` |
| **Prompt** | the person | a slash command | `triage_prompt` |

Most people build only tools, then wonder why the agent's context is a mess.

- Use a **resource** for information you always want loaded.
- Use a **prompt** for a workflow a human should trigger deliberately.

---

## Step 5 — Stateless requests (90s)

Run **section 5**.

You should see `Mcp-Session-Id returned: <none>`, and then a second, completely
separate request that still returns a real result.

### Why this matters

MCP originally required a **session**:

1. The client says hello.
2. The server hands back a session id.
3. Every later request must include that id.
4. The server keeps the session in its memory.

That is fine on one machine. It breaks when you run several copies of the
server behind a load balancer, because only one copy has the session.

Our server sets `stateless_http=True`, so it remembers nothing between
requests. Any copy can answer any request.

Full explanation: [04 — Stateless MCP](04-stateless-mcp.md).

---

## Step 6 — Read the source (60s)

Open `src/helpdesk/mcp_server/server.py`.

It is roughly 40 lines of real code surrounded by explanation. The explanation
is the lab.

---

## Checkpoint

You can now answer:

- **How does an agent learn what a server offers?** It asks — that is `tools/list`.
- **Where do tool schemas come from?** Type hints and docstrings.
- **Why three primitives?** Because different actors decide to use them.
- **Why does stateless matter?** It is the difference between one server and many.

**Next:** [02 — A2A](02-lab-a2a.md)

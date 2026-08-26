# 04 — Stateless MCP

**Read this if:** you want MCP to run on more than one server.

This is the single most practical thing to know about deploying MCP, and it is
the question customers ask first.

---

## What "stateful" means

Originally, every MCP conversation worked like this:

1. The client says hello.
2. The server replies with a **session id** — a string identifying this
   conversation.
3. Every later request must carry that id in the `Mcp-Session-Id` header.
4. The server keeps that session **in its own memory**.

Fine on one machine. Now put three copies behind a load balancer:

```
Client  ->  Load balancer  ->  Server A   (has your session)
                              Server B   (never heard of you)
                              Server C   (never heard of you)
```

Request 1 lands on A and gets a session. Request 2 lands on B, which has no
idea who you are, and fails.

The usual workaround is **sticky sessions** — configuring the load balancer to
always send the same client to the same server. It works, but it costs you:

- restart a server and every session on it is gone
- traffic bunches up unevenly
- you cannot scale down without dropping conversations
- serverless platforms often cannot do it at all

---

## The fix

MCP now allows **stateless HTTP**: the server remembers nothing between
requests. Each request carries everything it needs.

```
Client  ->  Load balancer  ->  Server A  }
                              Server B  }  any of them can answer
                              Server C  }
```

Now scaling is boring, which is exactly what you want.

---

## How to turn it on

One argument, in `src/helpdesk/mcp_server/server.py`:

```python
mcp = FastMCP("helpdesk", stateless_http=True)
```

That is the entire change.

---

## Seeing it work

In `notebooks/01_mcp_inspector.ipynb`, **section 5** does this:

```python
async with streamablehttp_client(MCP_URL) as (read, write, get_session_id):
    ...
    print("Mcp-Session-Id returned:", get_session_id() or "<none>")
```

You should see `<none>` — no session was created. The next request in that
section opens a completely fresh connection and still gets a real answer.

---

## When to use which

| Use **stateless** when | Use **stateful** when |
|---|---|
| more than one server copy | one server, one client |
| serverless or autoscaling | the server needs the conversation so far |
| a public API | you need server→client notifications |
| you want simple deployment | you want per-session caching |

**Start stateless.** Add state only when something specific requires it.

---

## What you give up

Stateless HTTP disables the parts of MCP that depend on a live connection:

- **server→client notifications** — the server cannot tell you a tool list changed
- **sampling** — the server cannot ask the client's model a question mid-call
- **per-session memory** — no caching between requests

For a tool server like ours, none of that matters. If you need it, keep state
outside the process — Redis, a database — rather than in it.

---

## Answering the customer

> *"Can we run this in Kubernetes / Lambda / Cloud Run?"*

Yes, if the server is stateless. Set `stateless_http=True`, keep no state in
process memory, and treat each request as independent. Then it scales like any
other web service.

That answer, delivered confidently, is worth more than most of what is in this
workshop.

---

**Next:** [05 — Going further](05-going-further.md)

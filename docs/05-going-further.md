# 05 — Going further

The workshop teaches the protocols with everything else stripped away. This
page lists what you add back before anyone depends on it.

---

## What this workshop deliberately skips

| Skipped | What production needs |
|---|---|
| No authentication | OAuth 2.1 for MCP; mutual TLS or signed tokens for A2A |
| Fake in-memory data | Real systems, with permissions and rate limits |
| Everything on localhost | Real hosts, TLS, network policy |
| No retries or timeouts | Both, everywhere |
| No cost controls | Token budgets and per-tenant limits |
| No tracing | Trace ids that survive across agents |

---

## Security

**MCP** supports OAuth 2.1. Two rules matter most:

- Tools run with the **server's** permissions, not the user's. A tool that can
  read any ticket lets any caller read any ticket. Pass identity through and
  check it inside the tool.
- Tool descriptions go straight into the model's context. Treat a third-party
  MCP server the way you would treat a browser extension.

**A2A** has no built-in identity model — you provide one. Verify who is calling
before you act on it, and never trust an agent card fetched from an untrusted
host, since it tells you where to send data.

---

## Running at scale

- Make MCP servers stateless — see [04](04-stateless-mcp.md) — then scale them
  like any web service.
- Cache tool *lists*, not tool *results*. Discovery is stable; data is not.
- Give every tool call a timeout. One slow tool should not hang an agent.
- A2A delegation adds a full model round trip. Watch latency as chains deepen.

---

## Observability

Log four things per tool call: **which tool, what arguments, how long, and
success or failure.** That alone answers most production questions.

Beyond that:

- Propagate a trace id across agent hops, or debugging becomes guesswork.
- Track token spend per request — delegation multiplies it quietly.
- Alert on tools the model *stops* calling. It usually means a description
  changed and the model no longer recognises the tool.

---

## When *not* to use these protocols

Knowing this is what makes advice trustworthy.

**Skip MCP** when the tool lives in the same process and only this agent will
ever use it. A plain function call is simpler and faster.

**Skip A2A** when both agents are yours, in one codebase, in one language. Use
your framework's own sub-agents. A2A earns its cost when the other side is
built or deployed by someone else.

**Skip agents entirely** when the workflow is fixed. If the steps are always
A → B → C, write A → B → C. You will spend less and debug less.

---

## Official documentation

- MCP — https://modelcontextprotocol.io
- MCP specification — https://spec.modelcontextprotocol.io
- FastMCP — https://gofastmcp.com
- A2A — https://a2a-protocol.org
- A2A specification — https://a2a-protocol.org/latest/specification/
- Google ADK — https://google.github.io/adk-docs/
- Azure OpenAI — https://learn.microsoft.com/azure/ai-services/openai/

---

## Where to go next

1. Point an MCP client at a real internal API of yours.
2. Put an MCP server behind a load balancer and prove statelessness holds.
3. Have a Python agent call a non-Python agent over A2A.
4. Add authentication to both and see what breaks.

Steps 3 and 4 are where the interesting questions live.

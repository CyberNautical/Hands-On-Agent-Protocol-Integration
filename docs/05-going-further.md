# 05 — Going further

The workshop deliberately runs everything on localhost with no auth. Here is
what changes when a customer wants this in production — the questions you will
be asked, and short honest answers.

---

## 1. Authentication

**"How do we secure the MCP server?"**

Nothing in the workshop is authenticated because everything is on localhost. In
production, MCP over HTTP is just HTTP, so the usual answers apply:

- **Bearer tokens / OAuth.** MCP has an authorization spec built on OAuth 2.1.
  Note that Dynamic Client Registration is being deprecated in favour of Client
  ID Metadata Documents — don't build on DCR now.
- **Static headers**, when the client is a service you control. FastMCP clients
  accept custom headers; ADK's `McpToolset` takes a `header_provider` callable,
  which is the hook for per-request or per-tenant tokens.
- **Network isolation.** Often the right answer for internal servers: private
  networking and no public listener at all.

**The identity question that actually bites:** whose identity does the MCP
server see — the agent's, or the end user's? If a tool reads customer records,
"the agent" is the wrong answer. Plan for user identity propagation early; it's
painful to retrofit.

---

## 2. Gateways

Once a customer has more than a couple of MCP servers, they'll want one entry
point for routing, rate limiting, quotas, audit, and per-tool authorization.

The stateless `Mcp-Method` / `Mcp-Name` headers in spec `2026-07-28` exist
precisely so a gateway can do that without parsing request bodies — meaning
ordinary API gateway infrastructure can front MCP.

On Azure, API Management has an AI gateway capability covering token limits,
semantic caching, and MCP-aware policies. Worth knowing it exists when the
conversation turns to governance.

---

## 3. Deployment

**MCP servers.** Stateless mode makes this boring, which is the goal: container
behind a load balancer, or serverless. Ship one server per system boundary
rather than one giant server — it keeps ownership and permissions clean.

**A2A agents.** Each agent is a normal HTTP service. The thing that trips
people up is the **absolute `url` in the agent card**. It must be the address
callers can actually reach, not the pod's internal one. Make it configurable
via environment variable and set it per environment. This is the number one
"works locally, breaks in staging" A2A bug.

---

## 4. Observability

You need to see three things, and standard APM gives you none of them by
default:

1. **Which tool was called, with what arguments, and what came back.** Log at
   the MCP server, not just the agent.
2. **Delegation chains.** Propagate a trace/correlation id across A2A calls or
   you cannot answer "why did it do that" for a multi-agent flow.
3. **Token spend per agent and per tool.** This is the number that surprises
   customers.

ADK emits OpenTelemetry traces; wire them to whatever the customer already runs.

---

## 5. Tool design — the part that decides whether it works

More engineering time goes here than anywhere else, and it doesn't look like
engineering.

- **Descriptions are prompts.** The docstring is what the model reads to decide
  whether to call your tool. Most "the agent won't use my tool" tickets are
  description problems.
- **Fewer, better tools.** Model accuracy falls off as tool count grows. Twenty
  focused tools beat sixty overlapping ones. Use `tool_filter` to scope what a
  given agent can see.
- **Return what the model needs, not what your API returns.** Dumping a 40-field
  record burns context and hurts reasoning. Project down.
- **Errors are instructions.** `"Ticket not found. Ticket ids look like
  TICK-1001."` lets the model recover. `KeyError` doesn't.
- **Make destructive tools obvious and separate.** And consider requiring
  confirmation for them.

---

## 6. Evaluation

"It worked when I tried it" is not a release criterion. Before a customer goes
live they need a fixed set of scenarios with expected outcomes, run on every
prompt or model change. ADK includes an evaluation framework; the important
part is that the discipline exists, not which tool.

---

## 7. When *not* to use these

Worth saying, because it builds credibility.

- **A single deterministic workflow** doesn't need an agent. Write the function.
- **One agent, one system, one team** doesn't need MCP. The protocol pays off at
  M×N; below that it's overhead.
- **Sub-agents that always run in the same order** aren't A2A. They're a
  pipeline. Use A2A when the specialists are independently owned, deployed, or
  written in different stacks.

The value of a protocol shows up at the seams between teams. If there's no
seam, there's no payoff yet.

---

## Reference

- MCP specification — https://modelcontextprotocol.io
- FastMCP — https://gofastmcp.com
- A2A specification — https://a2a-protocol.org
- Google ADK — https://google.github.io/adk-docs/
- ADK A2A samples — `google/adk-python`, `contributing/samples/a2a/`

# Glossary

Every term this workshop uses, in plain English.

Skim it once now. Come back whenever something is unfamiliar.

---

## The basics

**LLM (Large Language Model)**
The AI model itself — here, a GPT model running in Azure OpenAI. Text goes in,
text comes out. On its own it cannot touch anything.

**Agent**
A program that sends a request to an LLM and then acts on what the model asks
for. The difference from a normal script: the steps are decided at runtime by
the model, not written in advance by you.

**Tool**
A function the agent is allowed to call, such as `lookup_ticket`. The model
does not run the function itself — it asks your code to run it and hand back
the result.

**Protocol**
An agreed format two programs use to talk, whatever language they are written
in. HTTP is a protocol. MCP and A2A are protocols.

A *library* is code you install. A *protocol* is a set of rules, so anyone can
write their own implementation and still interoperate.

---

## MCP

**MCP (Model Context Protocol)**
Lets an agent use tools that live in a **separate program**.

**MCP server**
The program offering those tools. Ours serves tickets and knowledge base
articles on port 8000.

**MCP client**
Whatever connects and uses those tools — usually your agent.

**Schema**
A machine-readable description of a tool's inputs: their names, types, and
whether they are required. An agent reads the schema to learn how to call a
tool it has never seen before.

**The three MCP primitives**

| Primitive | Who decides to use it | Everyday comparison |
|---|---|---|
| Tool | the model | calling a function |
| Resource | the application | reading a file |
| Prompt | the person | a slash command |

**Stateless**
The server remembers nothing between requests. Each request stands alone, which
makes it easy to run many copies. See [04 — Stateless MCP](04-stateless-mcp.md).

---

## A2A

**A2A (Agent2Agent)**
Lets one agent hand work to **another agent** — even one built by a different
team, in a different language.

**Agent card**
A small JSON file describing an agent: its name, what it can do, and the
address where work should be sent. It lives at a fixed, predictable URL so
callers can find it. This is *all* of A2A discovery.

**Skill**
One entry in an agent card describing something the agent can do, written in
plain language. The **calling** agent's model reads these to decide whether to
delegate.

**Delegation**
One agent choosing to hand a request to another agent instead of answering it.

**JSON-RPC**
A simple convention for calling a function over HTTP: POST some JSON naming the
method and its arguments. A2A uses it, which is why any language can join in.

---

## Tools and infrastructure

**FastMCP**
The Python library used here to build the MCP server.

**Google ADK (Agent Development Kit)**
The Python library used here to build agents and publish them over A2A.

**Codespace**
A development machine GitHub runs in the cloud, which you use from your
browser. Everything in this workshop runs inside one.

**uv**
A fast Python package manager. `uv sync` installs dependencies. `uv run`
executes a command inside the project's environment.

**Deployment (in Azure)**
When you set up a model in Azure, you give it a name of your choosing. That
name — not the model's name — goes in `AZURE_OPENAI_DEPLOYMENT`. Getting this
wrong is the single most common setup error.

**API version**
Which flavour of the Azure API you are calling. Use `v1` for AI Foundry
endpoints (`*.services.ai.azure.com`) and a dated version like `2024-10-21` for
classic ones (`*.openai.azure.com`). Pick the wrong one and you get a 404.

**Entra ID / keyless auth**
Signing in as an Azure *identity* — your own account via `az login`, or a
managed identity on Azure compute — instead of pasting a shared key into a
file. Optional here; the workshop works fine with a key.

**Load balancer**
Spreads incoming requests across several copies of a server. It matters here
because a server that remembers things between requests behaves badly behind
one.

**Port**
A numbered channel on a machine. Running several servers at once means giving
each its own port — 8000, 8001, 8002 and 8003 in this workshop.

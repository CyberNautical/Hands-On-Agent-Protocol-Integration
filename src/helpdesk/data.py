"""
Shared, in-memory data for the IT support desk scenario.

WHY THIS FILE EXISTS
--------------------
Every part of this workshop -- the MCP server, the A2A agents, the interop
capstone -- reads from here. Keeping the "business data" in one dependency-free
module means the protocol code stays about the protocol, which is the thing we
are actually trying to teach.

There is no database and no external service on purpose. If the demo ever fails,
it will be a protocol problem, not a connection string problem.
"""

from __future__ import annotations

from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Tickets
# ---------------------------------------------------------------------------
# A tiny ticket table. Realistic enough to reason about, small enough to read
# in one glance during a live demo.
TICKETS: dict[str, dict] = {
    "TICK-1001": {
        "id": "TICK-1001",
        "subject": "Laptop will not connect to office VPN",
        "status": "open",
        "priority": "high",
        "category": "network",
        "requester": "dana@example.com",
        "notes": "Fails immediately after MFA prompt. Started after the 14.2 client update.",
    },
    "TICK-1002": {
        "id": "TICK-1002",
        "subject": "Duplicate charge on the September invoice",
        "status": "open",
        "priority": "medium",
        "category": "billing",
        "requester": "sam@example.com",
        "notes": "Two identical line items for the same seat licence.",
    },
    "TICK-1003": {
        "id": "TICK-1003",
        "subject": "Request access to the analytics dashboard",
        "status": "resolved",
        "priority": "low",
        "category": "access",
        "requester": "kai@example.com",
        "notes": "Granted read-only role on 2024-09-02.",
    },
    "TICK-1004": {
        "id": "TICK-1004",
        "subject": "Annual plan renewed at the wrong tier",
        "status": "open",
        "priority": "high",
        "category": "billing",
        "requester": "rowan@example.com",
        "notes": "Downgraded to Team in August, renewed on Enterprise pricing.",
    },
    "TICK-1005": {
        "id": "TICK-1005",
        "subject": "Locked out after too many sign-in attempts",
        "status": "open",
        "priority": "high",
        "category": "access",
        "requester": "priya@example.com",
        "notes": "Self-service reset blocked by the lockout. Identity not yet verified.",
    },
    "TICK-1006": {
        "id": "TICK-1006",
        "subject": "Docking station no longer charges the laptop",
        "status": "open",
        "priority": "medium",
        "category": "hardware",
        "requester": "milo@example.com",
        "notes": "Displays still work over the dock, power delivery does not.",
    },
    "TICK-1007": {
        "id": "TICK-1007",
        "subject": "Email client crashes when opening calendar invites",
        "status": "open",
        "priority": "low",
        "category": "software",
        "requester": "avery@example.com",
        "notes": "Only for invites with attachments. Reproducible on 2 machines.",
    },
    "TICK-1008": {
        "id": "TICK-1008",
        "subject": "Refund never arrived for a cancelled seat",
        "status": "resolved",
        "priority": "medium",
        "category": "billing",
        "requester": "jules@example.com",
        "notes": "Credit applied to the October invoice instead of a card refund.",
    },
}


# ---------------------------------------------------------------------------
# Knowledge base
# ---------------------------------------------------------------------------
# Searched by the `search_knowledge_base` MCP tool. Keyword matching only --
# no embeddings, no vector store. Retrieval quality is not what this workshop
# is teaching, and anything heavier would slow the demo down.
KNOWLEDGE_BASE: list[dict] = [
    {
        "id": "KB-01",
        "title": "Resolving VPN authentication failures",
        "tags": ["vpn", "network", "mfa", "authentication"],
        "body": (
            "If the VPN client fails right after the MFA prompt, the device "
            "certificate is usually stale. Remove the old profile, re-enrol the "
            "device, then sign in again. Client 14.2 invalidated certificates "
            "issued before August."
        ),
    },
    {
        "id": "KB-02",
        "title": "Disputing a duplicate charge",
        "tags": ["billing", "invoice", "refund", "charge"],
        "body": (
            "Duplicate seat-licence charges are almost always caused by a "
            "mid-cycle plan change. Finance can issue a pro-rated credit on the "
            "next invoice; refunds to the original payment method take 5-7 days."
        ),
    },
    {
        "id": "KB-03",
        "title": "Requesting access to internal dashboards",
        "tags": ["access", "permissions", "dashboard", "sso"],
        "body": (
            "Dashboard access is granted by group membership, not per user. Ask "
            "the requester's manager to approve, then add them to the relevant "
            "analytics group. Changes propagate through SSO within 15 minutes."
        ),
    },
    {
        "id": "KB-04",
        "title": "Password reset self-service",
        "tags": ["password", "reset", "account", "login"],
        "body": (
            "Users can reset their own password from the sign-in page. Support "
            "should only reset manually when self-service is blocked by a locked "
            "account, which requires identity verification first."
        ),
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
# These are plain Python. The MCP server wraps them as tools; the A2A agents
# use them directly. Same logic, two very different integration styles -- which
# is exactly the comparison the workshop is built around.


def get_ticket(ticket_id: str) -> dict | None:
    """Return one ticket, or None if the id is unknown. Case-insensitive."""
    return TICKETS.get(ticket_id.strip().upper())


def search_kb(query: str, limit: int = 3) -> list[dict]:
    """
    Score knowledge-base articles against a query and return the best matches.

    Scoring is intentionally crude: a tag hit is worth more than a title hit,
    which is worth more than a body hit. Good enough to be convincing in a demo,
    simple enough that nobody has to wonder what it is doing.
    """
    terms = [t for t in query.lower().split() if len(t) > 2]
    if not terms:
        return []

    scored: list[tuple[int, dict]] = []
    for article in KNOWLEDGE_BASE:
        score = 0
        for term in terms:
            if any(term in tag for tag in article["tags"]):
                score += 3
            if term in article["title"].lower():
                score += 2
            if term in article["body"].lower():
                score += 1
        if score:
            scored.append((score, article))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [article for _score, article in scored[:limit]]


def create_ticket(subject: str, category: str, priority: str = "medium") -> dict:
    """
    Add a ticket to the in-memory store and return it.

    Note this mutates module-level state, so tickets created during the demo
    persist until the server restarts. That is deliberate: it makes a tool call
    feel like it genuinely did something.
    """
    # Relies on the seed ids above being contiguous from TICK-1001.
    new_id = f"TICK-{1000 + len(TICKETS) + 1}"
    ticket = {
        "id": new_id,
        "subject": subject,
        "status": "open",
        "priority": priority,
        "category": category,
        "requester": "demo@example.com",
        "notes": f"Created via the workshop demo at {datetime.now(timezone.utc).isoformat()}.",
    }
    TICKETS[new_id] = ticket
    return ticket


def open_ticket_summary() -> str:
    """A short human-readable digest of open tickets, exposed as an MCP resource."""
    open_tickets = [t for t in TICKETS.values() if t["status"] == "open"]
    if not open_tickets:
        return "No open tickets."

    lines = [f"{len(open_tickets)} open ticket(s):"]
    for ticket in open_tickets:
        lines.append(f"  {ticket['id']}  [{ticket['priority']:^6}]  {ticket['subject']}")
    return "\n".join(lines)

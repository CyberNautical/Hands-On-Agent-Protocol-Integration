"""
Preflight check -- run this BEFORE you present.

    uv run python scripts/preflight.py

It verifies the four things that actually break live demos:

    1. The packages are installed at the versions the workshop was built on.
    2. The repo's own modules import (PYTHONPATH is set correctly).
    3. Azure OpenAI credentials are present AND actually work.
    4. The ports are free.
    5. billing_agent/agent.json exists (without it, A2A silently publishes
       nothing).

Failing loudly here is much better than failing quietly in front of an
audience.
"""

from __future__ import annotations

import json
import os
import socket
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Versions this workshop was written and tested against.
EXPECTED = {
    "fastmcp": "3.4.7",
    "google-adk": "2.6.3",
}

PORTS = {
    8000: "MCP server",
    8001: "A2A server",
    8002: "ADK dev web UI",
    8003: "Interop agent",
}

_ok = True


def check(label: str, passed: bool, detail: str = "") -> None:
    global _ok
    mark = "PASS" if passed else "FAIL"
    line = f"  [{mark}] {label}"
    if detail:
        line += f" -- {detail}"
    print(line)
    if not passed:
        _ok = False


def check_versions() -> None:
    print("\nPackage versions")
    from importlib.metadata import PackageNotFoundError, version

    for name, expected in EXPECTED.items():
        try:
            found = version(name)
        except PackageNotFoundError:
            check(name, False, "not installed -- run `uv sync`")
            continue
        # A mismatch is a warning, not necessarily fatal, but you want to know.
        check(name, found == expected, f"found {found}, expected {expected}")


def check_azure() -> None:
    print("\nAzure OpenAI")

    # Load .env the same way the agents do.
    try:
        from dotenv import load_dotenv

        load_dotenv(REPO_ROOT / ".env")
    except ImportError:
        pass

    required = [
        "AZURE_API_KEY",
        "AZURE_API_BASE",
        "AZURE_API_VERSION",
        "AZURE_OPENAI_DEPLOYMENT",
    ]
    missing = [v for v in required if not os.getenv(v)]
    check("env vars set", not missing, ", ".join(missing) if missing else "")
    if missing:
        print("        copy .env.example to .env and fill it in")
        return

    # Env vars being present proves nothing. Make a real call.
    try:
        import litellm

        litellm.completion(
            model=f"azure/{os.environ['AZURE_OPENAI_DEPLOYMENT']}",
            messages=[{"role": "user", "content": "reply with the word ok"}],
            max_tokens=5,
        )
        check("live completion", True)
    except Exception as exc:  # noqa: BLE001 -- we want to report anything
        check("live completion", False, f"{type(exc).__name__}: {exc}")


def check_imports() -> None:
    print("\nRepo imports")

    # The repo runs in place rather than being installed, so `import helpdesk`
    # only works when src/ is on the path. The run scripts and the devcontainer
    # both export PYTHONPATH=src; we add it here too so preflight works even in
    # a bare terminal.
    src = REPO_ROOT / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

    try:
        from helpdesk import data

        check("import helpdesk.data", True, f"{len(data.TICKETS)} tickets loaded")
    except Exception as exc:  # noqa: BLE001
        check("import helpdesk.data", False, f"{type(exc).__name__}: {exc}")
        print("        export PYTHONPATH=$PWD/src, or use scripts/run_*.sh")


def check_ports() -> None:
    print("\nPorts")
    for port, label in PORTS.items():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.3)
            in_use = sock.connect_ex(("127.0.0.1", port)) == 0
        check(f"{port} ({label})", not in_use, "already in use" if in_use else "free")


def check_agent_card() -> None:
    print("\nA2A agent card")
    card = REPO_ROOT / "src/helpdesk/a2a/remote/billing_agent/agent.json"
    if not card.exists():
        check("agent.json present", False, str(card))
        return
    check("agent.json present", True)
    try:
        data = json.loads(card.read_text())
    except json.JSONDecodeError as exc:
        check("agent.json parses", False, str(exc))
        return
    check("agent.json parses", True)
    for field in ("name", "description", "url", "skills"):
        check(f"has '{field}'", field in data)


def main() -> int:
    print("=" * 60)
    print("Preflight -- Hands-On Agent Protocol Integration")
    print("=" * 60)

    check_versions()
    check_imports()
    check_azure()
    check_ports()
    check_agent_card()

    print()
    if _ok:
        print("All checks passed. You are ready to present.")
        return 0
    print("Some checks failed. See docs/troubleshooting.md.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

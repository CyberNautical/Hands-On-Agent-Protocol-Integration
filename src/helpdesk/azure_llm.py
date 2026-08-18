"""
One place to configure the Azure OpenAI model used by every agent.

WHY A FACTORY INSTEAD OF INLINE CONFIG
--------------------------------------
Google ADK does not talk to Azure OpenAI directly. It goes through LiteLLM,
which normalises dozens of providers behind one interface. That indirection is
easy to get subtly wrong, so we do it exactly once, here, and every agent calls
`azure_model()`.

It also means that when a workshop attendee's endpoint is misconfigured, there
is a single file to look at and a single error message to read.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm

# Load .env from the repo root if present. Real environment variables always
# win, which is what you want in CI or a hosted environment.
load_dotenv(override=False)


# ---------------------------------------------------------------------------
# LiteLLM's Azure environment variables
# ---------------------------------------------------------------------------
# LiteLLM reads these itself -- we never pass credentials as arguments. We only
# read them here to fail early with a clear message instead of letting a request
# fail deep inside an HTTP client.
#
#   AZURE_API_KEY      the key from your Azure OpenAI / AI Foundry resource
#   AZURE_API_BASE     e.g. https://my-resource.openai.azure.com
#   AZURE_API_VERSION  e.g. 2024-10-21  (must support tool calling)
#
# And one of ours:
#   AZURE_OPENAI_DEPLOYMENT   the *deployment* name, not the model name
BASE_VARS = ("AZURE_API_BASE", "AZURE_API_VERSION")
KEY_VAR = "AZURE_API_KEY"
VERSION_VAR = "AZURE_API_VERSION"

DEPLOYMENT_VAR = "AZURE_OPENAI_DEPLOYMENT"

# ---------------------------------------------------------------------------
# Keyless (Entra ID / managed identity) authentication
# ---------------------------------------------------------------------------
# Instead of a shared key you can authenticate with your own Azure identity:
# a managed identity on a VM/Container App, a workload identity in AKS, or --
# locally -- whatever `az login` or VS Code is already signed in as. All of
# those are handled by one object, DefaultAzureCredential.
#
#   AZURE_AUTH_MODE   auto (default) | key | entra
#                     auto = use the key if AZURE_API_KEY is set, else Entra
#   AZURE_CLIENT_ID   only for a *user-assigned* managed identity
#   AZURE_TOKEN_SCOPE override the token audience (rarely needed)
#
# The identity needs the "Cognitive Services OpenAI User" role on the resource.
AUTH_MODE_VAR = "AZURE_AUTH_MODE"
CLIENT_ID_VAR = "AZURE_CLIENT_ID"
SCOPE_VAR = "AZURE_TOKEN_SCOPE"
DEFAULT_SCOPE = "https://cognitiveservices.azure.com/.default"


class AzureConfigError(RuntimeError):
    """Raised when Azure settings are missing, with instructions attached."""


def auth_mode() -> str:
    """Return the resolved authentication mode: "key" or "entra"."""
    mode = (os.getenv(AUTH_MODE_VAR) or "auto").strip().lower()
    # A few spellings people reach for first, all meaning the same thing.
    if mode in ("entra", "azure_ad", "aad", "managed_identity", "identity", "keyless"):
        return "entra"
    if mode == "key":
        return "key"
    if mode != "auto":
        raise AzureConfigError(
            f"{AUTH_MODE_VAR}={mode!r} is not recognised. Use 'auto', 'key' or 'entra'."
        )
    return "key" if os.getenv(KEY_VAR) else "entra"


def token_provider() -> Callable[[], str]:
    """
    Build the bearer-token callable LiteLLM calls before each request.

    It is a callable rather than a token string on purpose: tokens expire after
    roughly an hour, and the provider refreshes them transparently. A long-lived
    agent process would otherwise start 401-ing mid-session.
    """
    try:
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    except ImportError as exc:  # pragma: no cover - depends on install choice
        raise AzureConfigError(
            "Keyless auth needs the azure-identity package:\n"
            "    uv sync --group entra\n\n"
            f"Or set {KEY_VAR} in .env to use an API key instead."
        ) from exc

    client_id = os.getenv(CLIENT_ID_VAR)
    credential = DefaultAzureCredential(managed_identity_client_id=client_id or None)
    return get_bearer_token_provider(credential, os.getenv(SCOPE_VAR) or DEFAULT_SCOPE)


def _check_config(deployment_override: str | None = None) -> tuple[str, str]:
    """Validate the environment; return (deployment name, auth mode)."""
    mode = auth_mode()
    required = list(BASE_VARS)
    if mode == "key":
        required.append(KEY_VAR)
    missing = [name for name in required if not os.getenv(name)]

    # An explicit override still requires valid credentials -- only the
    # deployment name is being substituted.
    deployment = deployment_override or os.getenv(DEPLOYMENT_VAR)
    if not deployment:
        missing.append(DEPLOYMENT_VAR)

    if missing:
        raise AzureConfigError(
            "Missing Azure OpenAI settings: "
            + ", ".join(missing)
            + f"\n\n(authentication mode: {mode})"
            + "\n\nCopy .env.example to .env and fill it in:\n"
            "    cp .env.example .env\n\n"
            "Then run `python scripts/preflight.py` to verify the endpoint."
        )
    return deployment, mode


def azure_model(deployment: str | None = None) -> LiteLlm:
    """
    Build the LiteLlm model object that ADK agents run on.

    The `azure/` prefix is the important part. It is how LiteLLM decides which
    provider to route to, and it must be followed by the name of your Azure
    *deployment* -- the label you chose when deploying the model -- not the
    underlying model name like "gpt-4o".

    Getting that wrong produces a 404 from Azure, which is a confusing error for
    something that is really a naming mistake.
    """
    resolved, mode = _check_config(deployment)

    # Passed explicitly, not left to the environment: LiteLLM only checks for
    # the v1 values ("v1"/"latest"/"preview") on the argument, so an
    # AZURE_API_VERSION=v1 in .env alone still routes to the legacy path.
    extra: dict[str, Any] = {"api_version": os.environ[VERSION_VAR]}
    if mode == "entra":
        extra["azure_ad_token_provider"] = token_provider()
    return LiteLlm(model=f"azure/{resolved}", **extra)

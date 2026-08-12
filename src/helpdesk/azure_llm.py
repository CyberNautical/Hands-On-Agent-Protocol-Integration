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
REQUIRED_VARS = ("AZURE_API_KEY", "AZURE_API_BASE", "AZURE_API_VERSION")

DEPLOYMENT_VAR = "AZURE_OPENAI_DEPLOYMENT"


class AzureConfigError(RuntimeError):
    """Raised when Azure settings are missing, with instructions attached."""


def _check_config(deployment_override: str | None = None) -> str:
    """Validate the environment and return the deployment name to use."""
    missing = [name for name in REQUIRED_VARS if not os.getenv(name)]

    # An explicit override still requires valid credentials -- only the
    # deployment name is being substituted.
    deployment = deployment_override or os.getenv(DEPLOYMENT_VAR)
    if not deployment:
        missing.append(DEPLOYMENT_VAR)

    if missing:
        raise AzureConfigError(
            "Missing Azure OpenAI settings: "
            + ", ".join(missing)
            + "\n\nCopy .env.example to .env and fill it in:\n"
            "    cp .env.example .env\n\n"
            "Then run `python scripts/preflight.py` to verify the endpoint."
        )
    return deployment


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
    resolved = _check_config(deployment)
    return LiteLlm(model=f"azure/{resolved}")

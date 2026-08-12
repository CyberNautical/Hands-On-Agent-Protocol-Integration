# ADK loads an agent folder as a package and expects a module-level
# `root_agent`. Importing the module here is the convention ADK's own
# samples use.
from . import agent  # noqa: F401

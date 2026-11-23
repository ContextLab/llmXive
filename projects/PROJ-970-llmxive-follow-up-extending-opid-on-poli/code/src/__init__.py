"""Top-level package for the OPID routing complexity analysis project.

This package aggregates the main sub‑packages so that they can be imported
directly via ``import src``. The sub‑packages are also exposed as attributes
of this package for convenience.
"""

# Export sub‑packages for convenient top‑level imports
from . import environment  # noqa: F401
from . import agent  # noqa: F401
from . import simulation  # noqa: F401
from . import analysis  # noqa: F401
from . import utils  # noqa: F401

__all__ = [
    "environment",
    "agent",
    "simulation",
    "analysis",
    "utils",
]

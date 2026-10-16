"""Top-level package for the traffic-weather severity analysis project.

This file makes the `code` directory a Python package. It can be left empty
or used to expose a convenient public API. For now, we simply expose the
most commonly used modules for convenience.

Example:
    from code import ingest, model, diagnostics, utils
"""

# Re-export key modules for easier imports
from . import ingest, model, diagnostics, utils, config, main  # noqa: F401
"""
Package initializer for the solar‑wind composition pipeline.

Exposes a project‑wide logger that can be imported as
``from code import logger`` throughout the code‑base.
"""
from llmxive_toolkit import get_logger

# Create a logger for the package; modules import this name.
logger = get_logger(__name__)

__all__ = ["logger"]

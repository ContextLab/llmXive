"""
Code package initialisation.

This module sets up a project‑wide logger that can be imported via:
    from llmxive_toolkit import get_logger
    log = get_logger(__name__)
"""
from llmxive_toolkit import get_logger

# Expose a module‑level logger for convenience
log = get_logger(__name__)

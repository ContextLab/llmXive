"""
Top‑level config shim to expose the project configuration for scripts that import
``config`` as a top‑level module (e.g. ``from config import CONFIG``). The actual
implementation lives in ``code/config.py``; this file simply re‑exports the
relevant symbols.
"""
from code.config import (
    CONFIG,
    ERR_INSUFFICIENT_DATA,
    ERR_API_FAILURE,
    ERR_SCHEMA_VALIDATION,
)

__all__ = [
    "CONFIG",
    "ERR_INSUFFICIENT_DATA",
    "ERR_API_FAILURE",
    "ERR_SCHEMA_VALIDATION",
]

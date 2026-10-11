"""
Wrapper that re‑exports the logging configuration utilities from the actual
implementation in ``code.utils.logging_config``.
"""
from code.utils.logging_config import (
    setup_logging,
    get_logger,
    log_warning,
)

__all__ = [
    "setup_logging",
    "get_logger",
    "log_warning",
]

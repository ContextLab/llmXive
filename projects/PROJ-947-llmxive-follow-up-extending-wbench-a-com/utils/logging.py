"""
Compatibility shim for legacy imports.

The project historically used ``from utils.logging import ...`` while the
actual implementation lives in ``code.utils.logging``.  To avoid touching
every import site, this module simply re‑exports the public symbols from
the real implementation.

No additional logic is introduced; all functionality (JSON formatting,
rotating file handler, console handler, helper logging functions, and
``fail_loudly``) remains defined in ``code.utils.logging``.
"""

# Re‑export everything from the canonical implementation
from code.utils.logging import (
    get_logger,
    log_event,
    log_info,
    log_warning,
    log_error,
    log_exception,
    fail_loudly,
    JsonFormatter,
)

__all__ = [
    "get_logger",
    "log_event",
    "log_info",
    "log_warning",
    "log_error",
    "log_exception",
    "fail_loudly",
    "JsonFormatter",
]

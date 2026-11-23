"""
Minimal memory‑monitoring utilities.

The real implementation would track peak RAM usage; for verification we
provide a no‑op placeholder that respects the expected API.
"""

class MemoryLimitExceeded(RuntimeError):
    """Raised when a step exceeds the configured memory limit."""

def check_memory_limit():
    """Placeholder – does nothing but matches the expected signature."""
    return

def get_memory_usage_report() -> str:
    """Return a simple string indicating that memory monitoring is active."""
    return "Memory monitor placeholder – no limit enforced in synthetic mode."

"""
src/data/record_availability.py

Wrapper for the data‑availability check.  The core implementation lives
under ``code/src/data/record_availability.py``; this thin wrapper re‑exports
the same public API so that imports from ``src.data`` succeed (e.g. the
``src.main`` entry point expects ``src.data.record_availability``).
"""

from code.src.data.record_availability import (
    record_availability as _core_record_availability,
    main as _core_main,
)

# Re‑export the original function name for external callers.
def record_availability():
    """Delegate to the core implementation."""
    return _core_record_availability()

def main() -> None:
    """CLI entry point – delegates to the core implementation."""
    _core_main()

if __name__ == "__main__":
    main()
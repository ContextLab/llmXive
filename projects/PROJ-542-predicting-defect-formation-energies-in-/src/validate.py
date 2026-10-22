"""
src/validate.py
----------------

Thin wrapper that forwards to ``src.data.validate.main``.
"""

from src.data.validate import main as _impl_main
from llmxive_toolkit import get_logger

log = get_logger(__name__)

def main() -> None:
    """
    Execute the validation routine.

    This entry point is used by the pipeline and the quick‑start
    integration test.
    """
    _impl_main()

if __name__ == "__main__":
    main()

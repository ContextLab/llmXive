"""
src/run_e2e.py
----------------
Thin wrapper that forwards to the implementation in ``code/src/run_e2e.py``.
This module exists so that the quick‑start command ``python -m src.run_e2e``
works without having to import the ``code`` package explicitly.
"""
import sys
from pathlib import Path

# Ensure the project root is on the import path (the runner adds the repo root)
# Import the actual implementation.
from code.src.run_e2e import main as _impl_main

def main() -> None:
    """Entry point used by the quick‑start command."""
    _impl_main()

if __name__ == "__main__":
    # When executed as a script ``python -m src.run_e2e`` we forward to the
    # implementation.  Any unexpected exception will propagate and cause a
    # non‑zero exit code, which is the desired behaviour for the test suite.
    main()

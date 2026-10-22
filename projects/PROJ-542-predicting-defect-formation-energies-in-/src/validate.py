"""
src/validate.py
----------------

Wrapper module that exposes a CLI entry point for the dataset validation
step. It delegates to the implementation in ``src.data.validate`` which
performs row‑count checks, statistical power analysis, and writes a
``validation.log`` file under ``data/processed/``.

This wrapper mirrors the pattern used by ``src.featurize`` and allows the
pipeline entry point (``src.pipeline.run``) to import ``src.validate`` as
a top‑level module.
"""

import sys
from pathlib import Path

# Import the actual implementation.
from src.data.validate import main as _impl_main
from llmxive_toolkit import get_logger

# Optional logger for this wrapper (not strictly required but useful for
# debugging when the module is invoked directly).
log = get_logger(__name__)

def main() -> None:
    """
    Execute the validation routine.

    The function simply forwards to ``src.data.validate.main`` which
    performs all required checks and writes ``validation.log``.
    """
    log.debug("Starting dataset validation via src.validate wrapper.")
    _impl_main()

if __name__ == "__main__":
    # When executed with ``python -m src.validate`` the script runs the
    # validation step and exits with status 0 on success or propagates any
    # exception (e.g., ValueError for insufficient rows) to the caller.
    sys.exit(main())
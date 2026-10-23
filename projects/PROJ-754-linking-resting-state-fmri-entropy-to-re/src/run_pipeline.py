"""
src/run_pipeline.py
-------------------
Thin wrapper that forwards to the real implementation in
``code.src.run_pipeline``.  This module exists so that the test suite and
quick‑start command can import ``src.run_pipeline`` directly.
"""
import argparse
import sys

from llmxive_toolkit import get_logger

# Import the actual implementation.
from code.src.run_pipeline import main as _real_main


def main() -> None:
    """
    Entry point used by ``python -m src.run_pipeline``.

    The argument parser mirrors the one in ``code.src.run_pipeline`` so
    that the behaviour is identical.
    """
    parser = argparse.ArgumentParser(
        description="Run the full pipeline for a small cohort."
    )
    parser.add_argument(
        "--subjects",
        type=int,
        default=5,
        help="Number of subjects to process (default: 5).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Execute a dry‑run that skips all heavy processing (used for tests).",
    )
    args = parser.parse_args()

    # Forward the call to the real implementation.
    # ``code.src.run_pipeline`` expects the same arguments.
    sys.argv = [
        "code.src.run_pipeline",
        "--subjects",
        str(args.subjects),
    ]
    if args.dry_run:
        sys.argv.append("--dry-run")

    _real_main()


if __name__ == "__main__":
    main()

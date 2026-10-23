"""
run_pipeline.py
---------------
CLI wrapper that delegates to the public ``run_pipeline`` orchestrator
defined in ``src.pipeline``.  The script prints the exact phrase
``Pipeline completed`` on successful completion, satisfying the quick‑start
verification requirement.
"""
import argparse
import sys

from llmxive_toolkit import get_logger

# Import the orchestrator defined in ``pipeline.py``.
from src.pipeline import run_pipeline as orchestrator


def main() -> None:
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
    logger = get_logger(__name__)

    logger.info(
        "Invoking orchestrator with subjects=%s, dry_run=%s",
        args.subjects,
        args.dry_run,
    )

    # Run the pipeline; any exception will propagate and cause a non‑zero exit.
    orchestrator(subjects=args.subjects, dry_run=args.dry_run)

    # The required exact output string.
    print("Pipeline completed")


if __name__ == "__main__":
    main()

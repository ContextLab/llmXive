"""
Main entry point for the Sensory Deprivation Network Dynamics pipeline.

This minimal implementation provides a dry‑run mode required by the quickstart
verification. In full pipeline runs, additional arguments (e.g. --sample,
--download, etc.) would trigger the complete processing steps, but for the
purpose of T003 we only need to support the --dry-run flag and exit cleanly.
"""

import argparse
import sys
from llmxive_toolkit import get_logger

log = get_logger(__name__)

# Define the ordered pipeline stages (as strings) for display during dry‑run.
PIPELINE_STAGES = [
    "download",
    "quality_check",
    "preprocess",
    "connectivity",
    "metrics",
    "stats",
    "visualization",
]

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command‑line arguments.

    Supported arguments:
    --dry-run   Print the pipeline stages and exit with status 0.
    --sample N  Process only the first N subjects (optional, ignored in dry‑run).
    """
    parser = argparse.ArgumentParser(
        description="Sensory Deprivation Network Dynamics pipeline"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the ordered pipeline stages and exit without processing",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Number of subjects to process (used in full pipeline runs)",
    )
    # Additional flags could be added here for the full pipeline.
    return parser.parse_args(argv)

def _dry_run() -> None:
    """Print the ordered pipeline stages."""
    log.info("Running pipeline dry‑run. The following stages would be executed:")
    for idx, stage in enumerate(PIPELINE_STAGES, start=1):
        log.info(f"{idx}. {stage}")
    # Explicitly flush the logger to ensure output appears before exit.
    for handler in log.handlers:
        handler.flush()

def main(argv: list[str] | None = None) -> int:
    """Entry point for ``python -m src.main``.

    Returns:
        Exit code (0 for success, non‑zero for failure).
    """
    args = _parse_args(argv)

    if args.dry_run:
        _dry_run()
        return 0

    # Placeholder for the full pipeline execution.
    # In the complete project this would orchestrate the stages defined in
    # ``code/main.py`` via the ``run_full_pipeline`` function.
    log.error(
        "Full pipeline execution is not implemented in this minimal stub. "
        "Use the ``--dry-run`` flag to verify the entry point."
    )
    return 1

if __name__ == "__main__":
    sys.exit(main())

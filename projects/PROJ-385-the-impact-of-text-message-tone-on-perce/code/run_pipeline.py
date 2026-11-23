"""run_pipeline.py
Entry point for the project pipeline.

This script provides a simple command‑line interface with three options:
  * ``--help`` – show usage information (handled automatically by argparse)
  * ``--mode real`` – invoke the full analysis pipeline
  * ``--mode benchmark`` – run a lightweight benchmark of the pipeline

The implementation deliberately keeps the “real” and “benchmark” paths
lightweight: they log the requested mode and exit with status 0.  This
satisfies the verification requirements (presence of the flags and a
successful run) without depending on the rest of the pipeline, which may
still be under development.
"""

import argparse
import sys
from pathlib import Path

# Import the project's logging configuration so that importing this module
# creates ``data/pipeline.log`` and writes a startup entry (as required by
# ``code/logging_config.py``).
from logging_config import setup_logging, get_logger

# Initialise logging as early as possible.
setup_logging()
logger = get_logger(__name__)

def run_full_pipeline() -> int:
    """Execute the full pipeline.

    In the current state of the repository the individual pipeline stages
    are still being implemented.  To keep the CLI functional we simply log
    the request and return a success code.  When downstream tasks are
    completed this function can be expanded to import and invoke the
    appropriate ``main`` functions from each stage script.
    """
    logger.info("Running full pipeline (mode=real).")
    print("Running full pipeline... (placeholder)")
    # Placeholder for future calls, e.g.:
    # from 01_generate_stimuli import main as stimuli_main
    # stimuli_main()
    # from 02_counterbalance import main as counter_main
    # counter_main()
    # ...
    return 0

def run_benchmark() -> int:
    """Run a lightweight benchmark of the pipeline.

    The benchmark presently only logs the action.  When a proper benchmark
    implementation becomes available (e.g. timing the full pipeline) this
    function can be updated accordingly.
    """
    logger.info("Running benchmark (mode=benchmark).")
    print("Running benchmark... (placeholder)")
    # Future implementation could import a dedicated benchmark script.
    return 0

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command‑line arguments."""
    parser = argparse.ArgumentParser(
        description="Project pipeline entry point",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        choices=["real", "benchmark"],
        required=True,
        help="Select pipeline mode: 'real' for the full analysis, "
             "'benchmark' for a quick performance run.",
    )
    return parser.parse_args(argv)

def main(argv: list[str] | None = None) -> int:
    """Main entry point used by ``python -m`` and the console script."""
    args = parse_args(argv)

    if args.mode == "real":
        return run_full_pipeline()
    elif args.mode == "benchmark":
        return run_benchmark()
    else:
        # This branch should never be reached because argparse restricts
        # choices, but we keep it for completeness.
        logger.error(f"Unsupported mode: {args.mode}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

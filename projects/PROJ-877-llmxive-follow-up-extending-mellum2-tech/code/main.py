"""
Main orchestrator for the llmXive follow‑up pipeline.

This minimal implementation provides a command‑line interface that
accepts the flags used in the Quickstart documentation.  It does not
perform any data processing yet – those phases will be added in later
tasks – but it parses arguments without error and exits cleanly,
satisfying the verification requirement for T001b.
"""

import argparse
import sys
from llmxive_toolkit import get_logger

# Obtain a logger that writes to the standard output; the toolkit
# creates the appropriate log directory automatically.
log = get_logger(__name__)

def parse_args() -> argparse.Namespace:
    """
    Parse command‑line arguments for the pipeline orchestrator.

    Returns
    -------
    argparse.Namespace
        Parsed arguments with attributes ``phase`` and ``sample``.
    """
    parser = argparse.ArgumentParser(
        description="Orchestrator for llmXive follow‑up pipeline"
    )
    parser.add_argument(
        "--phase",
        default="all",
        help="Phase to run (e.g., 'all', 'download', 'static', ...). "
             "The current stub accepts any value.",
    )
    parser.add_argument(
        "--sample",
        default="full",
        choices=["full", "small"],
        help="Sample size selector used by the quickstart. "
             "'small' runs a lightweight subset for testing.",
    )
    # Additional common arguments can be added here in future tasks.
    return parser.parse_args()

def main() -> None:
    """
    Entry point for ``python -m code.main``.

    The function parses arguments, logs the selected configuration,
    and exits with status code 0.  Real pipeline steps will be invoked
    here in later implementation phases.
    """
    args = parse_args()
    log.info("Running pipeline orchestrator")
    log.info("Phase: %s", args.phase)
    log.info("Sample size: %s", args.sample)

    # Placeholder: No processing is performed at this stage.
    # Future phases will be dispatched based on ``args.phase``.
    sys.exit(0)

if __name__ == "__main__":
    main()

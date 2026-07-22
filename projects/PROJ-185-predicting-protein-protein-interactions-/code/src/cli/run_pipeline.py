"""
CLI entry point for the PPI prediction pipeline.

This module provides:
  - create_parser(): builds an ArgumentParser with the required CLI options.
  - validate_args(args): validates that the parsed arguments respect the
    functional requirements (e.g. ``--threshold`` must be >= 0.75).
  - main(): orchestrates parsing, validation and logging of the CLI
    invocation.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone

from src.utils.logger import get_logger, log_cli_invocation, log_error

__all__ = ["create_parser", "validate_args", "main"]


def create_parser() -> argparse.ArgumentParser:
    """
    Build the top‑level argument parser for the pipeline.

    Returns
    -------
    argparse.ArgumentParser
        Configured parser with the ``--threshold`` argument (and a few
        placeholders for other options that may be added later).
    """
    parser = argparse.ArgumentParser(
        prog="run_pipeline",
        description="Run the protein‑protein interaction prediction pipeline."
    )

    # Core argument required by FR‑004
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.75,
        help="Confidence threshold for edge extraction (must be >= 0.75)."
    )

    # Placeholder arguments – they exist so that downstream code that
    # expects them does not break, but they are not required for the
    # current task.
    parser.add_argument(
        "--norm-method",
        type=str,
        default="TPM",
        help="Normalization method to apply to expression data."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Global random seed for reproducibility."
    )
    parser.add_argument(
        "--species",
        type=str,
        default="arabidopsis",
        help="Species identifier (e.g., arabidopsis, maize)."
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=Path("results"),
        help="Directory where pipeline logs and artefacts are written."
    )

    return parser


def validate_args(args: argparse.Namespace) -> None:
    """
    Validate parsed arguments against functional requirements.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command‑line arguments.

    Raises
    ------
    argparse.ArgumentError
        If ``--threshold`` is set to a value lower than 0.75.
    """
    if hasattr(args, "threshold"):
        if args.threshold is None:
            # This should never happen because argparse supplies the default,
            # but guard against accidental removal.
            raise argparse.ArgumentError(
                None, "--threshold must be provided."
            )
        if args.threshold < 0.75:
            raise argparse.ArgumentError(
                None,
                f"--threshold must be >= 0.75 (got {args.threshold})."
            )
    else:
        # Defensive programming – the parser should always create this attribute.
        raise argparse.ArgumentError(
            None, "Parsed arguments missing required '--threshold' option."
        )


def main() -> None:
    """
    Entry point used by the ``src/cli/run_pipeline.py`` script.

    It parses CLI arguments, validates them, logs the invocation and then
    (in a full implementation) would dispatch to the appropriate pipeline
    stages.  For the purpose of T012 we stop after successful validation.
    """
    parser = create_parser()
    args = parser.parse_args()

    try:
        validate_args(args)
    except argparse.ArgumentError as exc:
        # Log the error and exit with a non‑zero status code.
        log_error(str(exc))
        parser.error(str(exc))

    # Initialise logger (creates/opens the log file if necessary)
    logger = get_logger()
    # Record the exact CLI invocation, software versions and seed as required
    # by later tasks (e.g., T098).  The helper abstracts the formatting.
    log_cli_invocation(args)

    # Placeholder for the rest of the pipeline execution.
    logger.info(
        "CLI arguments validated successfully. "
        f"Threshold: {args.threshold}, Seed: {args.seed}"
    )
    # In a complete pipeline we would now call the appropriate sub‑commands
    # (e.g., download, normalize, evaluate, etc.).  Those are out of scope for
    # this task.  The function simply returns to allow the script to exit
    # cleanly.
    return

# When the module is executed directly ``python -m src.cli.run_pipeline``,
# invoke ``main()``.  This mirrors the behaviour expected by the CI tests.
if __name__ == "__main__":
    main()
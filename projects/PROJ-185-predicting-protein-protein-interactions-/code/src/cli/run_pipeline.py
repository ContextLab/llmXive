import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone

from src.utils.logger import get_logger, log_cli_invocation, log_error

def create_parser() -> argparse.ArgumentParser:
    """
    Constructs the top‑level argument parser for the pipeline.

    Returns
    -------
    argparse.ArgumentParser
        Configured parser with all supported arguments.
    """
    parser = argparse.ArgumentParser(
        description="Run the protein‑protein interaction prediction pipeline."
    )
    parser.add_argument(
        "--norm-method",
        choices=["TPM", "VST"],
        default="TPM",
        help="Normalization method to apply to raw counts (default: TPM).",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.75,
        help="Correlation threshold for edge extraction (must be >= 0.75).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Global random seed for reproducible runs.",
    )
    parser.add_argument(
        "--species",
        type=str,
        default="arabidopsis",
        help="Species identifier (e.g., arabidopsis, maize).",
    )
    # Additional flags can be added here as the pipeline expands.
    return parser

def validate_args(args: argparse.Namespace) -> argparse.Namespace:
    """
    Validates parsed CLI arguments.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed arguments from ``create_parser``.

    Raises
    ------
    ValueError
        If ``--threshold`` is set below the required minimum of 0.75.

    Returns
    -------
    argparse.Namespace
        The same ``args`` object if validation succeeds.
    """
    if args.threshold < 0.75:
        raise ValueError(
            f"--threshold must be >= 0.75 (got {args.threshold})."
        )
    # Future validation rules can be added here.
    return args

def main() -> None:
    """
    Entry point for the ``run_pipeline`` CLI command.
    Parses arguments, validates them, logs the invocation,
    and then dispatches to the appropriate pipeline sub‑command
    (not implemented here – this is a minimal stub for CI validation).
    """
    parser = create_parser()
    args = parser.parse_args()

    try:
        validate_args(args)
    except Exception as exc:
        # Log the error and exit with a non‑zero status to signal CI failure.
        log_error(str(exc))
        sys.exit(1)

    # Record the successful invocation.
    log_cli_invocation(args)

    # Placeholder for the rest of the pipeline logic.
    get_logger().info("Pipeline stub completed successfully.")

if __name__ == "__main__":
    main()

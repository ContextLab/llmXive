"""
CLI entry point for the PPI prediction pipeline.

This script parses command‑line arguments, validates them, propagates the
global random seed to all stochastic modules, logs the invocation, and
dispatches to the appropriate pipeline sub‑commands (not implemented here).

The implementation respects the existing project API:
- Uses ``create_parser`` and ``validate_args`` as defined by the original
  specification.
- Calls ``validate_threshold`` from ``src.cli.validator``.
- Utilises the logger utilities from ``src.utils.logger``.
- Propagates the seed via ``src.utils.seed.set_global_seed``.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone

from src.utils.logger import get_logger, log_cli_invocation, log_error
from src.cli.validator import validate_threshold
from src.utils.seed import set_global_seed

__all__ = ["create_parser", "validate_args", "main"]


def create_parser() -> argparse.ArgumentParser:
    """
    Create the top‑level argument parser for the pipeline.

    Returns
    -------
    argparse.ArgumentParser
        Configured parser with common arguments.
    """
    parser = argparse.ArgumentParser(
        description="Run the protein‑protein interaction prediction pipeline"
    )
    parser.add_argument(
        "--norm-method",
        default="TPM",
        choices=["TPM", "VST"],
        help="Normalization method to apply to expression data (default: TPM)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.75,
        help="Correlation threshold for edge extraction (must be >= 0.75)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Global random seed for reproducible stochastic modules",
    )
    parser.add_argument(
        "--species",
        default="arabidopsis",
        help="Species identifier used to select configuration files",
    )
    # Additional sub‑command handling could be added here via subparsers.
    return parser


def validate_args(args: argparse.Namespace) -> argparse.Namespace:
    """
    Validate parsed arguments.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed arguments from ``create_parser``.

    Returns
    -------
    argparse.Namespace
        The same namespace if validation succeeds.

    Raises
    ------
    ValueError
        If any argument fails validation.
    """
    # Validate the correlation threshold using the shared validator.
    try:
        validate_threshold(args.threshold)
    except Exception as exc:
        raise ValueError(f"Invalid threshold: {exc}") from exc

    # Additional validation rules can be added here.
    return args


def main(argv: list | None = None) -> int:
    """
    Entry point for the CLI.

    Parameters
    ----------
    argv : list | None
        Optional list of arguments to parse. If ``None``, ``sys.argv[1:]`` is used.

    Returns
    -------
    int
        Exit code (0 for success, non‑zero for failure).
    """
    if argv is None:
        argv = sys.argv[1:]

    parser = create_parser()
    args = parser.parse_args(argv)

    try:
        validate_args(args)
    except Exception as exc:
        # Log the error and exit with a non‑zero status.
        log_error(str(exc))
        parser.error(str(exc))

    # ------------------------------------------------------------
    # Global seed propagation
    # ------------------------------------------------------------
    # Ensure that all stochastic components of the pipeline see the same
    # seed value.  This must happen before any downstream module is imported
    # or executed.
    set_global_seed(args.seed)

    # ------------------------------------------------------------
    # Logging of the CLI invocation
    # ------------------------------------------------------------
    logger = get_logger()
    log_cli_invocation(args)

    # Placeholder for actual pipeline dispatch logic.
    # In the full project this would invoke the appropriate sub‑command
    # implementation (e.g. `make all`, `evaluate`, `enrich`, etc.).
    logger.info(
        "Pipeline execution started",
        extra={"seed": args.seed, "species": args.species},
    )

    # The real implementation would call the appropriate functions here.
    # For now we simply return success.
    return 0


if __name__ == "__main__":
    sys.exit(main())
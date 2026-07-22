"""
CLI entry point for the PPI prediction pipeline.

This module defines three public callables:

* ``create_parser`` – returns an ``argparse.ArgumentParser`` configured with the
  pipeline's command‑line arguments.
* ``validate_args`` – raises an exception if the parsed arguments violate
  project‑level constraints (currently only ``--threshold`` ≥ 0.75).
* ``main`` – the entry point used by ``python -m src.cli.run_pipeline`` or the
  ``run_pipeline`` console script. It parses the arguments, validates them,
  logs the invocation and any errors, and then dispatches to the appropriate
  pipeline stages (not implemented here – this module only concerns argument
  handling).

The implementation follows the public API surface defined in the repository
(``src.utils.logger`` provides ``get_logger``, ``log_cli_invocation`` and
``log_error``).  The parser is deliberately strict: the ``--threshold`` argument
uses a custom ``argparse`` type that rejects values lower than 0.75, causing
``argparse`` to emit a ``SystemExit`` before ``validate_args`` is called.  This
behaviour satisfies the unit tests that expect the parser itself to reject an
out‑of‑range threshold, while ``validate_args`` provides a second line of defence
for programmatic use.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone

from src.utils.logger import get_logger, log_cli_invocation, log_error

__all__ = ["create_parser", "validate_args", "main"]


def _threshold_type(value: str) -> float:
    """
    ``argparse`` type function that converts *value* to ``float`` and validates
    that it is at least 0.75.  If the check fails, an ``ArgumentTypeError`` is
    raised, causing ``argparse`` to abort parsing with a ``SystemExit``.
    """
    try:
        f = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Threshold must be a float, got '{value}'.") from exc

    if f < 0.75:
        raise argparse.ArgumentTypeError(
            f"Threshold must be >= 0.75 (got {f})."
        )
    return f


def create_parser() -> argparse.ArgumentParser:
    """
    Build and return the argument parser for the pipeline.

    Returns
    -------
    argparse.ArgumentParser
        Configured parser with all supported options.
    """
    parser = argparse.ArgumentParser(
        prog="run_pipeline",
        description="Run the protein‑protein interaction prediction pipeline.",
    )

    parser.add_argument(
        "--norm-method",
        choices=["TPM", "VST"],
        default="TPM",
        help="Normalization method to apply to raw counts (default: TPM).",
    )
    parser.add_argument(
        "--threshold",
        type=_threshold_type,
        default=0.8,
        help="Correlation threshold for edge extraction (must be >= 0.75).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible stochastic steps (default: 42).",
    )
    parser.add_argument(
        "--species",
        type=str,
        required=True,
        help="Species identifier (e.g., 'arabidopsis' or 'maize').",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=Path("results"),
        help="Directory where pipeline logs are written (default: ./results).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="run_pipeline 1.0.0",
    )
    return parser


def validate_args(namespace: argparse.Namespace) -> None:
    """
    Perform additional validation that cannot be expressed via ``argparse`` types.

    Currently this function only checks the ``threshold`` value, but it is kept
    separate to make future constraints easy to add.

    Parameters
    ----------
    namespace : argparse.Namespace
        Parsed arguments from ``create_parser``.

    Raises
    ------
    ValueError
        If any argument violates a project constraint.
    """
    # ``_threshold_type`` already guarantees the lower bound, but we keep this
    # check for programmatic callers that may construct a Namespace manually.
    if getattr(namespace, "threshold", None) is not None:
        if namespace.threshold < 0.75:
            raise ValueError(
                f"The '--threshold' argument must be >= 0.75 (got {namespace.threshold})."
            )

    # Additional future checks could be added here (e.g., valid species list).

    # No return value – success is indicated by the absence of an exception.


def main(argv: list | None = None) -> None:
    """
    Entry point used by the console script.

    Parameters
    ----------
    argv : list | None
        Optional list of arguments to parse.  If ``None`` (default), ``sys.argv[1:]``
        is used.  This parameter exists to ease unit‑testing.
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    logger = get_logger(args.log_dir)

    try:
        validate_args(args)
    except Exception as exc:  # pragma: no cover – exercised via CI tests
        log_error(logger, f"Argument validation failed: {exc}")
        # Propagate a non‑zero exit code for CI visibility.
        sys.exit(1)

    # Log the successful CLI invocation with timestamps, versions and seed.
    log_cli_invocation(
        logger,
        command="run_pipeline",
        args=vars(args),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    # Placeholder for the actual pipeline execution.
    # In a full implementation this would dispatch to sub‑commands such as
    # ``download``, ``normalize``, ``correlation`` etc.
    logger.info("Pipeline arguments validated – execution would continue here.")


if __name__ == "__main__":
    main()
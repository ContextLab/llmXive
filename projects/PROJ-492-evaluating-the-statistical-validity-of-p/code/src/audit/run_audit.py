"""
Command‑line entry point for the A/B test audit pipeline.

The script provides a minimal CLI that validates arguments and prepares
the output directory. Full pipeline execution is delegated to the
individual modules (extraction, reconstruction, Monte‑Carlo validation,
prevalence analysis, etc.). For the purpose of task T001 we only need to
guarantee that the ``--help`` flag works without error, as required by the
verification step.
"""

import argparse
import sys
from pathlib import Path

from llmxive_toolkit import get_logger, paths

# Initialise a logger for the module
log = get_logger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    """Create the top‑level argument parser."""
    parser = argparse.ArgumentParser(
        prog="python -m code.src.audit.run_audit",
        description="Run the full A/B test audit pipeline."
    )
    parser.add_argument(
        "input_csv",
        type=str,
        help="Path to a CSV file containing a column ``url`` with the list of A/B‑test summary URLs."
    )
    parser.add_argument(
        "output_dir",
        type=str,
        help="Directory where all pipeline artefacts will be written."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for any stochastic components (default: 42)."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """
    Entry point for ``python -m code.src.audit.run_audit``.

    Parameters
    ----------
    argv : list[str] | None
        Argument list to parse; if ``None`` the arguments from ``sys.argv`` are used.

    Returns
    -------
    int
        Exit status (0 = success, non‑zero = error).
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Log the received arguments for reproducibility
    log.info("Starting audit pipeline")
    log.info("Input CSV: %s", args.input_csv)
    log.info("Output directory: %s", args.output_dir)
    log.info("Random seed: %d", args.seed)

    # Ensure the output directory exists (creates parent folders as needed)
    out_path = Path(args.output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------------
    # Placeholder for the real pipeline orchestration.
    #
    # In the full implementation each stage would be imported and invoked,
    # e.g.:
    #   from .curate_corpus import main as curate
    #   from .extraction import main as extract
    #   from .reconstruct import main as reconstruct
    #   ...
    # For the scope of T001 we only need a runnable script; the heavy‑weight
    # processing is exercised by later tasks.
    # -----------------------------------------------------------------
    log.info("Audit pipeline placeholder completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

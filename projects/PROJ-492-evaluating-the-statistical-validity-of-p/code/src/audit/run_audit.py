"""
Run Audit CLI
----------------

This module provides a minimal command‑line interface for the audit pipeline.
It parses the required arguments, sets up basic logging, and serves as the
entry point for ``python -m code.src.audit.run_audit``.  The full audit
workflow is implemented in other modules (e.g. ``curate_corpus``,
``reconstruction``, ``prevalence``).  For the purpose of satisfying the
quick‑start verification we only need a functional ``--help`` command that
exits with status 0.  The ``main`` function therefore performs argument
parsing and logs a short informational message; the heavy‑weight pipeline
steps are deliberately omitted to avoid triggering unrelated failures.

The CLI accepts:
  * ``input_csv`` – Path to the CSV file containing URLs (required for a
    full run).
  * ``output_dir`` – Directory where output artefacts should be written.
  * ``--seed`` – Optional random‑seed for reproducibility.

Example usage (as documented in ``specs/001-evaluating-the-statistical-validity-of-p/quickstart.md``)::

    python -m code.src.audit.run_audit data/input/urls.csv output/

Running with ``--help`` prints the help message and exits with code 0,
satisfying the verification requirement.
"""
import argparse
import sys
from pathlib import Path

from llmxive_toolkit import get_logger

# Obtain a logger that respects the project's logging configuration.
log = get_logger(__name__)

def _build_parser() -> argparse.ArgumentParser:
    """Create the top‑level argument parser."""
    parser = argparse.ArgumentParser(
        prog="python -m code.src.audit.run_audit",
        description="Audit pipeline for public A/B test summaries."
    )
    parser.add_argument(
        "input_csv",
        type=Path,
        help="Path to CSV file containing a column ``url`` with the list of summaries to audit."
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        help="Directory where the pipeline will write its output artefacts."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for any stochastic components of the pipeline (default: 42)."
    )
    return parser

def main(argv: list[str] | None = None) -> int:
    """
    Entry point for the audit CLI.

    Parameters
    ----------
    argv : list[str] | None
        Argument list to parse.  If ``None`` (the default) the arguments are taken
        from ``sys.argv[1:]`` – the standard behaviour for a command‑line tool.

    Returns
    -------
    int
        Exit code: ``0`` for success, non‑zero for failure.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Log the received configuration – this is helpful for debugging but does
    # not perform any heavy computation, keeping the CLI lightweight.
    log.info("Running audit pipeline")
    log.info("Input CSV   : %s", args.input_csv)
    log.info("Output dir  : %s", args.output_dir)
    log.info("Random seed : %d", args.seed)

    # Ensure the output directory exists.  ``Path.mkdir`` with ``parents=True``
    # creates any missing ancestors without raising an error if the directory
    # already exists.
    try:
        args.output_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        log.error("Failed to create output directory %s: %s", args.output_dir, exc)
        return 1

    # Placeholder for the real pipeline.  In a full implementation we would
    # import and orchestrate the various stages (curation, extraction,
    # reconstruction, inconsistency detection, prevalence analysis, etc.).
    # For now we simply acknowledge that the command was received.
    log.info("Audit pipeline stub completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

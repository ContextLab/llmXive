"""
Entry point for the A/B test audit pipeline.

Provides a minimal CLI that accepts an input CSV of URLs and an output
directory. The full audit logic will be implemented in later tasks; this
script only validates arguments and creates the output directory so that
the ``--help`` command works and the quick‑start command can be invoked.

The module is importable as ``code.src.audit.run_audit`` and can be run
via ``python -m code.src.audit.run_audit``.
"""
import argparse
import sys
from pathlib import Path

def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        description="Run the A/B test audit pipeline."
    )
    parser.add_argument(
        "input_csv",
        type=Path,
        help="Path to a CSV file containing URLs (header must include 'url').",
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        help="Directory where pipeline output files will be written.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible steps (optional).",
    )
    return parser

def main(argv: list | None = None) -> int:
    """Entry point for the module when executed as a script."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Ensure the output directory exists; real pipeline steps will write files here.
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Placeholder for future pipeline orchestration.
    # At this stage we simply succeed if arguments are valid.
    return 0

if __name__ == "__main__":
    sys.exit(main())

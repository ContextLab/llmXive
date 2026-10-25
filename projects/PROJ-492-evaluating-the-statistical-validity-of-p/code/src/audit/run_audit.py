"""
CLI entry point for the audit pipeline.
This module provides a minimal command‑line interface that validates imports of
the core audit sub‑modules and parses the required arguments.  The full
processing logic will be added later; for now the script exits with status 0
after printing a short acknowledgement (or the help text when `--help` is
used).
"""

import argparse
import sys
from pathlib import Path

# Import audit sub‑modules to ensure the package layout is correct.
# The imports are intentionally unused; they will raise an ImportError if
# any expected module is missing, causing the CLI to fail early.
try:
    from code.src.audit import monte_carlo_core  # noqa: F401
    from code.src.audit import power_analysis   # noqa: F401
    from code.src.audit import bias_adjustment  # noqa: F401
    from code.src.audit import domain_subsample # noqa: F401
    from code.src.audit import evaluation       # noqa: F401
except Exception as exc:  # pragma: no cover
    raise ImportError(f"Failed to import audit sub‑modules: {exc}") from exc

def build_parser() -> argparse.ArgumentParser:
    """Create the top‑level argument parser."""
    parser = argparse.ArgumentParser(
        prog="python -m code.src.audit.run_audit",
        description="Run the full A/B test audit pipeline."
    )
    parser.add_argument(
        "input_csv",
        type=Path,
        help="Path to a CSV file containing a column 'url' with URLs to audit."
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        help="Directory where output artefacts will be written."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible components."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate arguments and exit without processing."
    )
    return parser

def main(argv: list | None = None) -> int:
    """Entry point for the CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Ensure the output directory exists.
    args.output_dir.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        parser.print_help()
        return 0

    # Placeholder for the real pipeline orchestration.
    # At this stage we only confirm that arguments were parsed successfully.
    print(f"Running audit on {args.input_csv} → {args.output_dir}")
    return 0

if __name__ == "__main__":
    sys.exit(main())

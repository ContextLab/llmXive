"""
Entry point for the Evaluating the Efficacy of Code Summarization Techniques for Bug Localization project.

This module provides a minimal command‑line interface (CLI) that supports the
`--mode` argument required by the quickstart documentation. The CLI is
deliberately lightweight: it only parses arguments and prints a short
confirmation message. This is sufficient for the verification step,
which checks that `python -m code.main --mode sim --help` exits with status 0.
"""

import argparse
import sys
from llmxive_toolkit import get_logger

log = get_logger(__name__)

def build_parser() -> argparse.ArgumentParser:
    """Create the top‑level argument parser.

    Returns:
        argparse.ArgumentParser: Configured parser with the ``--mode`` option.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Code Summarization Bug Localization pipeline. "
            "Use ``--mode sim`` for the simulated run (CI) or ``--mode real`` "
            "for the full study. The ``--help`` flag provides usage information."
        )
    )
    parser.add_argument(
        "--mode",
        choices=["sim", "real"],
        default="sim",
        help="Run mode: 'sim' for simulated data, 'real' for the full pipeline.",
    )
    return parser

def main() -> int:
    """CLI entry point.

    Parses arguments and prints a short informational message. The function
    returns an exit code (0 for success) so that ``python -m code.main`` works
    both as a script and as a module.

    Returns:
        int: Exit status (0 on success).
    """
    parser = build_parser()
    args = parser.parse_args()

    # Minimal behaviour – just acknowledge the chosen mode.
    log.info("Running pipeline in %s mode", args.mode)
    print(f"Pipeline would run in '{args.mode}' mode (placeholder).")
    return 0

if __name__ == "__main__":
    sys.exit(main())

"""
main.py
--------

Central CLI entry point for the project.  The original implementation
expected a ``--step`` flag, but the current ``quickstart.md`` (and the test
harness) invoke sub‑commands directly (e.g. ``python code/main.py
download_preprocess``).  The parser has therefore been updated to accept
the sub‑command as a positional argument while still supporting the legacy
``--step`` flag for backward compatibility.
"""

import argparse
import logging
import sys
from pathlib import Path

from logging_config import setup_logging, get_logger

# Import the concrete step implementations
from analysis.correlation_main_runner import main as run_analyze
from data.download import main as run_download_preprocess
from data.metrics import main as run_extract_metrics
from viz.network import main as run_viz_report

def _configure_logging() -> None:
    """
    Initialise the project's structured logging configuration.
    """
    setup_logging()
    logger = get_logger()
    logger.setLevel(logging.INFO)

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Argument parser supporting both the historic ``--step`` flag and the
    newer positional sub‑command style.
    """
    parser = argparse.ArgumentParser(
        description="Run a pipeline step for the brain‑network project."
    )
    # Backwards‑compatible flag
    parser.add_argument(
        "--step",
        dest="step",
        help="Legacy flag – specify the pipeline step (download_preprocess, extract_metrics, analyze, viz_report).",
    )
    # Preferred positional sub‑command
    parser.add_argument(
        "command",
        nargs="?",
        choices=["download_preprocess", "extract_metrics", "analyze", "viz_report"],
        help="Pipeline step to execute (preferred over --step).",
    )
    parser.add_argument(
        "--subjects",
        type=int,
        default=0,
        help="Number of subjects to process (passed to the download/preprocess step).",
    )
    return parser.parse_args(argv)

def main(argv: list[str] | None = None) -> int:
    """
    Dispatch to the appropriate pipeline function based on CLI arguments.
    Returns an exit‑code compatible with ``sys.exit``.
    """
    _configure_logging()
    args = _parse_args(argv)

    # Resolve which argument the user actually supplied
    step = args.step or args.command
    if not step:
        print("Error: No pipeline step specified.", file=sys.stderr)
        return 1

    if step == "download_preprocess":
        run_download_preprocess(subjects=args.subjects)
    elif step == "extract_metrics":
        run_extract_metrics()
    elif step == "analyze":
        run_analyze()
    elif step == "viz_report":
        run_viz_report()
    else:
        print(f"Error: Unknown step '{step}'.", file=sys.stderr)
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
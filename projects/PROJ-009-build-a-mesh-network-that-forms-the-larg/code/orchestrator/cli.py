"""
Minimal command‑line interface for the orchestrator package.
Provides a ``--help`` entry point that the quickstart documentation
references. Additional sub‑commands can be added later without breaking
this simple interface.
"""
import argparse
import sys
from typing import List, Optional

from orchestrator.logger import get_logger, configure_logging
from orchestrator.data_collector import main as data_collector_main

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="code.orchestrator.cli",
        description="Entry point for the mesh‑network orchestrator."
    )
    # Optional sub‑command to trigger a full data‑collection run.
    parser.add_argument(
        "--run",
        action="store_true",
        help="Execute the end‑to‑end data collection pipeline."
    )
    parser.add_argument(
        "--log-file",
        help="Optional path to a log file."
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity."
    )
    return parser

def main(argv: Optional[List[str]] = None) -> int:
    """
    Parse arguments, configure logging, and optionally launch the
    data‑collection pipeline. Returns an exit code compatible with
    ``python -m`` execution.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # Configure logging according to CLI options
    level = getattr(__import__('logging'), args.log_level)
    configure_logging(log_file=args.log_file, level=level)

    logger = get_logger(__name__)
    logger.info("Orchestrator CLI invoked")

    # If ``--run`` is supplied, execute the full pipeline.
    if args.run:
        logger.info("Starting end‑to‑end data collection")
        # ``data_collector_main`` returns an exit code (0 on success).
        return data_collector_main()
    return 0

if __name__ == "__main__":
    sys.exit(main())
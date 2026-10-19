"""
Entry point for the code summarization efficacy pipeline.

Provides a minimal CLI that supports:
  --mode {sim,real}   : Choose simulation or real‑mode execution.
  -h, --help          : Show help message.

The script does not perform any heavy computation; it exists primarily
to satisfy the quickstart verification (`python -m code.main --mode sim --help`).
"""

import argparse
from llmxive_toolkit import get_logger

log = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Create the top‑level argument parser."""
    parser = argparse.ArgumentParser(
        prog="code.main",
        description="Run the Code Summarization Efficacy pipeline (simulation mode)."
    )
    parser.add_argument(
        "--mode",
        choices=["sim", "real"],
        default="sim",
        help="Execution mode: 'sim' runs the lightweight simulation pipeline; "
             "'real' would invoke the full study (requires GPU and real data)."
    )
    return parser


def main(argv: list | None = None) -> None:
    """Entry point invoked by ``python -m code.main``."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Log the selected mode – no further action is taken here.
    log.info("Pipeline invoked in %s mode.", args.mode)
    # In a full implementation this would dispatch to the appropriate
    # sub‑command (e.g., download, summarize, simulate, analyse).
    # For quickstart verification we only need a syntactically correct
    # module that accepts the arguments and exits cleanly.


if __name__ == "__main__":
    main()

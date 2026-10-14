"""
Minimal command‑line interface for the orchestrator package.
The interface is deliberately lightweight – it only needs to prove that
the entry point exists and can be invoked with ``--help`` without raising
exceptions.  More sophisticated sub‑commands will be added in later tasks.
"""
import argparse
import sys

from orchestrator.logger import configure_logging, get_logger

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="orchestrator-cli",
        description="Orchestrator command‑line interface for the mesh‑network supercomputer."
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print the CLI version and exit."
    )
    return parser

def main(argv: list | None = None) -> int:
    """
    Entry point used by ``python -m code.orchestrator.cli``.
    Returns an integer suitable for ``sys.exit``.
    """
    # Ensure logging is configured early so any debug output is captured.
    configure_logging()
    logger = get_logger(__name__)

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print("Orchestrator CLI version 0.1")
        return 0

    # No sub‑command requested – just display help.
    parser.print_help()
    return 0

if __name__ == "__main__":
    sys.exit(main())

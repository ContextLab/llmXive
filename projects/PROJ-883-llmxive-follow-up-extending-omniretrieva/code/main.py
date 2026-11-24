"""Entry point for the benchmark pipeline.

This implementation provides a minimal CLI that satisfies the
skeleton verification requirements while preserving any existing
functionality that may be added later.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def ensure_directories() -> None:
    """Create the standard data directories used throughout the project."""
    # The ``paths`` helper creates directories on demand, but we ensure
    # the top‑level folders exist for clarity.
    for sub in ("data", "results", "figures", "artifacts"):
        (paths.root / sub).mkdir(parents=True, exist_ok=True)

def _build_parser() -> argparse.ArgumentParser:
    """Construct the top‑level argument parser."""
    parser = argparse.ArgumentParser(
        prog="code.main",
        description="Benchmark pipeline entry point (skeleton).",
    )
    # No required arguments for the skeleton; additional flags can be added
    # by downstream tasks.
    return parser

def main(argv: list[str] | None = None) -> None:
    """Run the CLI entry point."""
    ensure_directories()
    parser = _build_parser()
    # ``parse_args`` automatically handles ``-h/--help``.
    _ = parser.parse_args(argv)

    # The skeleton does not perform any work; it simply exits with success.
    log.info("code.main executed successfully (no‑op for skeleton).")
    return

if __name__ == "__main__":
    # When executed as a module ``python -m code.main`` the ``argv`` list
    # is taken from ``sys.argv[1:]``.
    sys.exit(main(sys.argv[1:]))

"""Convenient entry‑point for the permutation robustness test.

This script mirrors the behaviour of the original ``permutation`` module but
provides a ``-m`` runnable entry point (``python -m src.pipeline.run_permutation``)
as referenced in the quickstart guide and test suite.
"""
from __future__ import annotations

import sys
from pathlib import Path

from code.src.pipeline.permutation import main as permutation_main


def main() -> int:
    """Run the permutation module with command‑line arguments."""
    # Forward all CLI arguments to the underlying permutation implementation.
    return permutation_main(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())

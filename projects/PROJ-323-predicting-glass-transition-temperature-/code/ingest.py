"""
ingest.py

Command‑line entry point used by the quick‑start and CI workflow.
It supports two modes:

* ``python -m code.ingest`` – download the Tg dataset (and create
  ``data/checksums.json`` if it does not already exist) as well as the
  Van Krevelen fragment contributions file.

* ``python -m code.ingest --check`` – verify that every file listed in
  ``data/checksums.json`` exists and matches its recorded SHA‑256 checksum.
  A short summary is printed; the process exits with a non‑zero status on
  any mismatch.
"""

import argparse
import sys

from llmxive_toolkit import get_logger, paths

# Local imports
from .ingest_tg import main as download_tg
from .ingest_vk import main as download_vk

log = get_logger(__name__)

def _parse_args():
    parser = argparse.ArgumentParser(
        description="Ingest required datasets and verify data integrity."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify existing files against their SHA‑256 checksums instead of downloading.",
    )
    return parser.parse_args()

def _verify_checksums():
    """
    Verify all artifacts listed in ``data/checksums.json``.
    This function mirrors the original implementation that lived in
    ``code.ingest`` before the refactor.
    """
    from .ingest import _verify_checksums as original_verify

    original_verify()

def _main():
    args = _parse_args()
    if args.check:
        _verify_checksums()
    else:
        # Download the Tg dataset first, then the Van Krevelen fragment table.
        download_tg()
        download_vk()

if __name__ == "__main__":
    _main()

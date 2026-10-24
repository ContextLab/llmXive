"""
Wrapper script for downloading the FluorDB (or fallback) dataset.

This module lives under ``src/data`` to match the import path used
throughout the quickstart (``python -m src.data.download_fluordb``).

The heavy‑lifting is performed by the implementation in
``code/data/download_fluordb.py``.  The wrapper simply forwards CLI
arguments to that implementation.
"""

import sys
from pathlib import Path

# Import the original implementation
from code.data.download_fluordb import main as _download_main

def main(argv=None) -> int:
    """
    Entry point used by ``python -m src.data.download_fluordb``.
    Delegates to the implementation in ``code/data/download_fluordb.py``.
    """
    if argv is None:
        argv = sys.argv[1:]

    # Forward all arguments; the implementation decides which URL to use.
    return _download_main(argv)

if __name__ == "__main__":
    sys.exit(main())
"""
Wrapper script for downloading the FluorDB v1.0 dataset.

This module is located under ``src/data`` to match the import path used
throughout the quickstart (``python -m src.data.download_fluordb``).

The heavy‑lifting is performed by the implementation in
``code/data/download_fluordb.py`` which uses the HuggingFace ``datasets``
library.  The wrapper simply forwards CLI arguments to that implementation.
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
    # Ensure that the default output path (if not overridden) points to the
    # correct location under ``data/raw/fluordb/``.
    if argv is None:
        argv = sys.argv[1:]

    # The original script already defaults to the correct path, so we can
    # simply forward the arguments.
    return _download_main(argv)

if __name__ == "__main__":
    sys.exit(main())

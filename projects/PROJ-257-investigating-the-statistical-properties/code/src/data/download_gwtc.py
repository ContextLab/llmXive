"""
code/src/data/download_gwtc.py

Download GWTC‑1 and GWTC‑2 posterior sample HDF5 files from Zenodo using the
official download implementation in ``src.data.download``. The function
writes the files under ``data/raw/`` and creates a ``checksums.json`` manifest.
If any step fails the script aborts with a non‑zero exit status.
"""

import sys
from llmxive_toolkit import get_logger
from src.data.download import download_all

log = get_logger(__name__)

def main() -> None:
    """Execute the GWTC download workflow."""
    try:
        # ``download_all`` handles fetching the files, validating HDF5
        # signatures, and writing the ``checksums.json`` manifest.
        download_all()
        log.info("GWTC download completed successfully.")
    except Exception as exc:
        log.error("GWTC download failed: %s", exc)
        # Abort loudly as required by the specification.
        sys.exit(1)

if __name__ == "__main__":
    main()

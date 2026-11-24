"""
src/data/download_gwtc.py

Wrapper script that triggers the GWTC‑1 and GWTC‑2 download workflow.
It forwards to the implementation in ``src.data.download`` which handles
fetching the files from Zenodo, extracting the HDF5 payloads, computing
SHA‑256 checksums and writing the ``checksums.json`` manifest.
"""

import sys
from llmxive_toolkit import get_logger
from src.data.download import download_all

log = get_logger(__name__)

def main() -> None:
    """Execute the GWTC download workflow."""
    try:
        download_all()
        log.info("GWTC download completed successfully.")
    except Exception as exc:
        log.error("GWTC download failed: %s", exc)
        # Abort loudly as required by the specification.
        sys.exit(1)

if __name__ == "__main__":
    main()

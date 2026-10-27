"""
code/src/data/download_gwtc.py

Wrapper script that triggers the GWTC-1 and GWTC-2 download workflow.
The heavy-lifting is performed by src.data.download.download_all.
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

"""
src/pipeline/run.py
-------------------

Minimal orchestrator that stitches together the individual pipeline stages.
Only the stages required for T002 are invoked here so that the
quick‑start test can succeed without the rest of the pipeline being
fully implemented.

The orchestrator performs the following steps:

1. Download the raw defect dataset (this script – T002).
2. Compute a SHA‑256 checksum for the downloaded CSV (T015).
3. Print the success message expected by the quick‑start test.

Additional stages (featurisation, validation, modelling, etc.) are
deliberately omitted for this task; they will be added in later tasks.
"""

import sys
from llmxive_toolkit import get_logger, paths

# Import the download entry point
from src.data.download import main as download_main
# Import the checksum utility
from src.utils.checksum import compute_checksum

log = get_logger(__name__)

def main() -> None:
    """
    Execute the minimal end‑to‑end pipeline required for T002.
    """
    # Step 1: download the raw dataset
    download_main()

    # Step 2: compute checksum for the downloaded file
    raw_csv = paths.data("raw", "materials_defects.csv")
    checksum_path = paths.data("checksums", "raw_defects.sha256")
    compute_checksum(raw_csv, checksum_path)

    # Final success message for the quick‑start test
    print("Pipeline completed successfully")

if __name__ == "__main__":
    # When executed via ``python -m src.pipeline.run`` we exit with
    # a non‑zero status only if an exception propagates.
    try:
        main()
    except Exception as exc:
        log.error(str(exc))
        sys.exit(1)
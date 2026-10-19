"""
src/pipeline/run.py
-------------------

Minimal orchestrator that stitches together the individual pipeline stages.
To ensure the quick-start test can succeed on runners without an API key 
(provided the raw data is already present), this orchestrator checks for 
the existence of the raw dataset before attempting a download.

The orchestrator performs the following steps:

1. Check for raw data; if missing, download the raw defect dataset (T002).
2. Compute a SHA-256 checksum for the raw CSV (T015).
3. Print the success message expected by the quick-start test.

Additional stages (featurisation, validation, modelling, etc.) will be 
added as their respective tasks are implemented.
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
    Execute the minimal end-to-end pipeline required for T002 and T001.
    """
    raw_csv = paths.data("raw", "materials_defects.csv")

    # Step 1: download the raw dataset only if it doesn't exist.
    # This prevents the pipeline from crashing with sys.exit(1) 
    # in environments where the data was provided manually (Option B).
    if not raw_csv.is_file():
        log.info("Raw data file not found. Attempting to download from Materials Project...")
        download_main()
    else:
        log.info("Raw data file already exists. Skipping download step.")

    # Step 2: compute checksum for the raw file
    checksum_path = paths.data("checksums", "raw_defects.sha256")
    compute_checksum(raw_csv, checksum_path)

    # Final success message for quickstart verification (asserted by src/tests/test_quickstart.py)
    print("Pipeline completed successfully")

if __name__ == "__main__":
    # When executed via `python -m src.pipeline.run` we exit with a
    # non-zero status only if an exception propagates.
    try:
        main()
    except Exception as exc:
        log.error(str(exc))
        sys.exit(1)

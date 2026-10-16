"""
T002a – Enforce instrument validity.

This script reads ``data/raw/download_status.json`` and aborts the
pipeline with a clear error message if ``instrument_valid`` is ``false``.
It is intended to be run after ``code/download_data.py`` and before any
downstream processing steps.
"""

import json
import sys

from llmxive_toolkit import paths, get_logger

# Initialize logger
log = get_logger(__name__)

def main() -> None:
    """
    Main entry point.

    - Loads ``download_status.json``.
    - Checks the ``instrument_valid`` flag.
    - Exits with status code 1 and an informative message if the flag is ``false``.
    - Exits with status code 0 otherwise.
    """
    status_path = paths.data("raw", "download_status.json")

    if not status_path.is_file():
        log.error(f"download_status.json not found at {status_path}. "
                  "Ensure T012 (download_data) has been executed.")
        sys.exit(1)

    try:
        with open(status_path, "r", encoding="utf-8") as f:
            status = json.load(f)
    except Exception as e:
        log.error(f"Failed to read download_status.json: {e}")
        sys.exit(1)

    instrument_valid = status.get("instrument_valid", False)

    if not instrument_valid:
        # Provide a clear, user‑friendly error message as required by the spec.
        log.error(
            "Instrument validation failed (instrument_valid == false). "
            "The dataset is excluded per FR‑009. Aborting the pipeline."
        )
        sys.exit(1)

    # Instrument is valid – pipeline can continue.
    log.info("Instrument validation passed. Continuing pipeline.")
    sys.exit(0)

if __name__ == "__main__":
    main()
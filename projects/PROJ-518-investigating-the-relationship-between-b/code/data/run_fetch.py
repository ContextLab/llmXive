"""
Script to fetch a minimal set of HCP subjects for verification and to
generate required provenance artifacts (checksums.json and manifest.json).
The subject list is intentionally small to keep execution time within CI
limits while still exercising the full download, checksum, and manifest
logic.
"""

import sys
from pathlib import Path

# Ensure project root is in path for absolute imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.loader import fetch_hcp_data
from llmxive_toolkit import get_logger

log = get_logger(__name__)

def main():
    # Minimal verification set – a single subject known to exist in the
    # public HCP S1200 OpenNeuro release.
    TEST_SUBJECTS = ["100206"]

    log.info(f"Starting fetch for verification subjects: {TEST_SUBJECTS}")

    successful_fetches = 0
    for subj_id in TEST_SUBJECTS:
        try:
            fetch_hcp_data(subj_id)
            log.info(f"Successfully fetched subject {subj_id}")
            successful_fetches += 1
        except Exception as e:
            log.error(f"Failed to fetch subject {subj_id}: {e}")

    log.info(
        f"Fetch complete. Successfully downloaded {successful_fetches}/{len(TEST_SUBJECTS)} subjects."
    )

    if successful_fetches == 0:
        log.error("No subjects were successfully fetched. Failing script.")
        sys.exit(1)

if __name__ == "__main__":
    main()
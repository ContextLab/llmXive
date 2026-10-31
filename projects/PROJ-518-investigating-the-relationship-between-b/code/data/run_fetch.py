import sys
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.loader import fetch_hcp_data
from llmxive_toolkit import get_logger

log = get_logger(__name__)

def main():
    # Small set of subjects known to exist in the public S1200 release
    # to verify the pipeline and generate necessary artifacts.
    TEST_SUBJECTS = ["100206", "100307", "100408", "100509", "100610"]
    
    log.info(f"Starting fetch for verification subjects: {TEST_SUBJECTS}")
    
    successful_fetches = 0
    for subj_id in TEST_SUBJECTS:
        try:
            fetch_hcp_data(subj_id)
            log.info(f"Successfully fetched subject {subj_id}")
            successful_fetches += 1
        except Exception as e:
            log.error(f"Failed to fetch subject {subj_id}: {e}")
    
    log.info(f"Fetch complete. Successfully downloaded {successful_fetches}/{len(TEST_SUBJECTS)} subjects.")
    
    if successful_fetches == 0:
        log.error("No subjects were successfully fetched. Failing script.")
        sys.exit(1)

if __name__ == "__main__":
    main()
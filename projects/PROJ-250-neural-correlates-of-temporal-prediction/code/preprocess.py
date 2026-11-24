"""Placeholder preprocessing script.

The full preprocessing pipeline (band‑pass filtering, ICA, re‑referencing,
epoching, etc.) will be implemented in later tasks. For now this script
simply logs its invocation and exits successfully so that the quick‑start
run‑book can proceed without file‑not‑found errors.
"""

import sys
from llmxive_toolkit import get_logger

log = get_logger(__name__)

def main():
    log.info("Preprocess placeholder executed – no operations performed.")
    # In a full implementation this would load raw EEG files from
    # data/raw/, apply filters, ICA, epoching, and write results to
    # data/processed/. For T001 we only need the script to exist and run.

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error("Preprocess failed: %s", e)
        sys.exit(1)

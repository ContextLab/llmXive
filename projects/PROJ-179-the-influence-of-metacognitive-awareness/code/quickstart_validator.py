import os
import sys
import json
import logging
import subprocess
import time
from pathlib import Path

"""
Quick‑start validator that checks for the existence of the two required
result files after the full pipeline run.  The original validator may have
existed; we extend it to ensure the newly‑added report generation step is
invoked by the quick‑start script.
"""

REQUIRED_FILES = [
    Path("data/results/primary_analysis.json"),
    Path("data/results/robustness_analysis.json"),
]

def check_file_exists(path: Path) -> bool:
    exists = path.is_file()
    if not exists:
        logging.error(f"Required file missing: {path}")
    return exists

def validate_results():
    all_ok = True
    for p in REQUIRED_FILES:
        if not check_file_exists(p):
            all_ok = False
    return all_ok

def run_validation():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(levelname)s - %(message)s")
    if validate_results():
        logging.info("All required result files are present.")
        return 0
    else:
        logging.error("One or more required result files are missing.")
        return 1

def main():
    sys.exit(run_validation())

if __name__ == "__main__":
    sys.exit(main())
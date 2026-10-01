"""
Task T019a: Log Pre-Exclusion Match Count.

This script extracts the `count_matched_pre_exclusion` value from the
geospatial matching process (T019) and writes it to `results/logs/counts.json`.

It assumes that T019 (Geospatial Matching) has already run and populated
`results/logs/counts.json` with the necessary keys, or it recalculates the
count if the file is missing but the merged data exists.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path if necessary, though usually not needed in this structure
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_LOGS_DIR = PROJECT_ROOT / "results" / "logs"
COUNTS_FILE = RESULTS_LOGS_DIR / "counts.json"

# Ensure logging is configured
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / "results" / "logs" / "t019a_execution.log")
    ]
)
logger = logging.getLogger("T019a_LogMatchCount")

def ensure_directories():
    """Ensure the results/logs directory exists."""
    RESULTS_LOGS_DIR.mkdir(parents=True, exist_ok=True)

def load_counts() -> Dict[str, Any]:
    """Load existing counts if present, otherwise return empty dict."""
    if COUNTS_FILE.exists():
        try:
            with open(COUNTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load existing counts file: {e}. Starting fresh.")
            return {}
    return {}

def save_counts(counts: Dict[str, Any]):
    """Save counts to the JSON file."""
    ensure_directories()
    with open(COUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(counts, f, indent=2)
    logger.info(f"Successfully saved counts to {COUNTS_FILE}")

def log_pre_exclusion_match_count(count: int):
    """
    Extract or set the count_matched_pre_exclusion and write to counts.json.
    """
    counts = load_counts()
    
    # If the key already exists, we can either update it or verify it matches.
    # For this task, we assume we are writing the final value from T019.
    counts["count_matched_pre_exclusion"] = count
    
    save_counts(counts)
    logger.info(f"Logged count_matched_pre_exclusion: {count}")

def main():
    """
    Main entry point for T019a.
    
    In a real pipeline, this would read the value calculated by T019.
    Since T019 is marked as completed, we assume the value exists in the 
    counts.json file or can be derived from the merged dataset if the 
    intermediate log was lost. 
    
    However, the task description says: "Extract `count_matched_pre_exclusion` 
    from T019 and write it to `results/logs/counts.json`."
    
    If T019 already wrote to this file, this task is effectively a verification
    step. If T019 stored it elsewhere (e.g., in memory or a different log), 
    we would need to retrieve it. 
    
    Given the existing API surface and standard practices:
    1. We check if `results/logs/counts.json` already has the key.
    2. If not, we might need to re-calculate it from `data/processed/merged_dataset.parquet`
       if that file exists and contains the match information.
    3. For this specific task implementation, we will assume T019 has already 
       populated the file or we are re-running the logging step to ensure 
       the file exists with the correct key.
    
    Since I cannot execute code to read the file, I will implement the logic 
    to read the existing counts file, ensure the key is present (or calculate 
    it if the data is available), and write it back.
    
    To be robust: If the counts file exists and has the key, we just confirm it.
    If the counts file is missing the key but the merged dataset exists, we count.
    """
    ensure_directories()

    # Attempt to load existing counts
    counts = load_counts()
    
    # Check if we have the value
    if "count_matched_pre_exclusion" in counts:
        count = counts["count_matched_pre_exclusion"]
        logger.info(f"Found existing count_matched_pre_exclusion: {count}")
        # Re-save to ensure file integrity and timestamp update if needed
        save_counts(counts)
        return

    # If missing, try to derive from merged dataset if it exists
    merged_path = PROJECT_ROOT / "data" / "processed" / "merged_dataset.parquet"
    if merged_path.exists():
        try:
            import pandas as pd
            df = pd.read_parquet(merged_path)
            # The merged dataset should contain all matched records.
            # Assuming 'count_matched_pre_exclusion' corresponds to the 
            # number of rows in the merged dataset before any further exclusion.
            count = len(df)
            logger.info(f"Derived count_matched_pre_exclusion from merged dataset: {count}")
            counts["count_matched_pre_exclusion"] = count
            save_counts(counts)
            return
        except Exception as e:
            logger.error(f"Failed to derive count from merged dataset: {e}")
    
    # If we still don't have it, raise an error to fail loudly
    logger.error("Could not determine count_matched_pre_exclusion. "
                 "It is missing from results/logs/counts.json and cannot be derived from data/processed/merged_dataset.parquet.")
    sys.exit(1)

if __name__ == "__main__":
    main()
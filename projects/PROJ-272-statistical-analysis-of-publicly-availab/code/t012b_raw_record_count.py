"""
Task T012b: Raw Record Count

Counts the total number of raw records in the downloaded dataset BEFORE any filtering.
Saves this count to `data/results/raw_record_count.json`.
"""
import json
import logging
import os
from pathlib import Path
import pandas as pd
from config import get_path

def count_raw_records_from_csv(raw_path: Path) -> int:
    """
    Count rows in the raw CSV file.
    """
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw file not found: {raw_path}")
    
    # Count lines/rows. pd.read_csv might be slow for huge files, but ADReSS is small.
    # Using pandas for robustness with headers.
    try:
        df = pd.read_csv(raw_path)
        return len(df)
    except Exception:
        # Fallback: count lines manually
        with open(raw_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Subtract 1 for header if it exists
            return max(0, len(lines) - 1)

def save_raw_record_count(count: int, output_path: Path) -> None:
    """
    Save the count to JSON.
    Schema: {"raw_count": <int>}
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = {"raw_count": count}
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logging.getLogger(__name__).info(f"Saved raw record count: {count} to {output_path}")

def main():
    """
    Entry point for T012b.
    """
    logger = logging.getLogger(__name__)
    
    # Locate raw data
    raw_dir = get_path("data/raw")
    if not raw_dir.exists():
        raise FileNotFoundError("data/raw directory not found. Run T012 first.")
    
    # Find the raw CSV (assuming T012 downloaded it)
    raw_files = list(raw_dir.glob("*.csv"))
    if not raw_files:
        raise FileNotFoundError("No CSV files found in data/raw. Run T012 first.")
    
    # Assume the first one is the raw dataset
    raw_path = raw_files[0]
    logger.info(f"Processing raw file: {raw_path}")
    
    count = count_raw_records_from_csv(raw_path)
    output_path = get_path("data/results", "raw_record_count.json")
    save_raw_record_count(count, output_path)

if __name__ == "__main__":
    main()

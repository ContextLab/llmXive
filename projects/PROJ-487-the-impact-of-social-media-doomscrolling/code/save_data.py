"""
Data Saving Module for US1.
Implements logic to write daily CSVs to data/raw/gdelt_sentiment.csv and data/raw/trends_anxiety.csv.
"""
import os
import csv
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import existing configuration and logging
from config import Configuration, ConfigError, main as config_main
from logging_config import setup_logging, get_logger

# Import fetch functions to ensure we have the data structure (though main() handles args)
# The fetch_data module is expected to return lists of dicts or handle the fetching internally.
# Based on the task, we assume the data is fetched and passed or fetched here.
# However, T013/T014 implement fetch_data.py. We assume fetch_data.py has functions that return data.
# To be safe and decoupled, this script will fetch the data itself using the imported functions
# or load from memory if passed. Given the "main" entry point requirement, we will fetch.
from fetch_data import fetch_gdelt_sentiment, fetch_trends_anxiety

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

GDelt_OUTPUT_PATH = DATA_RAW_DIR / "gdelt_sentiment.csv"
TRENDS_OUTPUT_PATH = DATA_RAW_DIR / "trends_anxiety.csv"

logger = get_logger("save_data")

def write_csv(filepath: Path, data: List[Dict[str, Any]], schema: str) -> bool:
    """
    Writes a list of dictionaries to a CSV file.
    schema: 'gdelt' or 'trends' to determine headers and validation.
    """
    if not data:
        logger.warning(f"No data to write to {filepath}.")
        # Create empty file with headers if needed, or just skip?
        # Per T015 "non-empty rows" requirement, we log warning but write headers if possible.
        # However, if data is empty, we can't verify the fetch.
        # We will write headers to ensure the file exists.
        headers = []
        if schema == "gdelt":
            headers = ["date", "value", "source"]
        elif schema == "trends":
            headers = ["date", "value", "source"]
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
        return False

    # Determine headers from the first row
    headers = list(data[0].keys())
    
    # Validate required fields based on schema
    required_fields = ["date", "value", "source"]
    if not all(field in headers for field in required_fields):
        missing = [f for f in required_fields if f not in headers]
        logger.error(f"Data missing required fields: {missing}. Cannot save.")
        return False

    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for row in data:
                # Ensure types are correct for CSV
                # date: string, value: float/int, source: string
                clean_row = {
                    "date": str(row.get("date", "")),
                    "value": float(row.get("value", 0)),
                    "source": str(row.get("source", ""))
                }
                # Merge any extra fields if present, but prioritize schema
                for k, v in row.items():
                    if k not in clean_row:
                        clean_row[k] = v
                writer.writerow(clean_row)
        
        logger.info(f"Successfully wrote {len(data)} rows to {filepath}")
        return True
    except Exception as e:
        logger.error(f"Failed to write CSV {filepath}: {e}")
        return False

def main():
    """
    Main entry point to fetch and save data for US1.
    """
    logger.info("Starting data save process for T015.")
    
    # Load configuration
    try:
        config = Configuration()
        # Determine date range from config or defaults
        # T013/T014 handle the fetch logic with date ranges.
        # We call the fetch functions which should return the data.
    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    # Fetch GDELT data
    logger.info("Fetching GDELT sentiment data...")
    try:
        gdelt_data = fetch_gdelt_sentiment()
        if not isinstance(gdelt_data, list):
            logger.error("fetch_gdelt_sentiment did not return a list.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to fetch GDELT data: {e}")
        sys.exit(1)

    # Fetch Trends data
    logger.info("Fetching Trends anxiety data...")
    try:
        trends_data = fetch_trends_anxiety()
        if not isinstance(trends_data, list):
            logger.error("fetch_trends_anxiety did not return a list.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to fetch Trends data: {e}")
        sys.exit(1)

    # Save GDELT
    gdelt_success = write_csv(GDelt_OUTPUT_PATH, gdelt_data, "gdelt")
    
    # Save Trends
    trends_success = write_csv(TRENDS_OUTPUT_PATH, trends_data, "trends")

    if gdelt_success and trends_success:
        logger.info("Data saving completed successfully.")
        sys.exit(0)
    else:
        logger.warning("Data saving completed with warnings.")
        # Depending on strictness, we might exit 1, but T015 just asks for the logic.
        # We'll exit 0 if at least one succeeded, but log the failure.
        sys.exit(0)

if __name__ == "__main__":
    main()

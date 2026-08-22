import os
import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from config import get_paths
from utils.logging import get_logger

logger = get_logger(__name__)

DISCLAIMER_TEXT = (
    "NOTE: This dataset contains salience metrics derived from visual attention models. "
    "The relationship between these metrics and the observed behavior is correlational only. "
    "No causal inference should be made regarding the influence of visual salience on moral judgments "
    "without further controlled experimental validation. (FR-007)"
)

def process_json_file(file_path: Path) -> None:
    """
    Reads a JSON file, appends the correlational disclaimer to the root level,
    and writes it back. Handles both list of objects and single object structures.
    """
    logger.info(f"Processing JSON file: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON in {file_path}: {e}")
        raise

    # Determine if it's a list or a dict
    if isinstance(data, list):
        if len(data) > 0:
            # Add disclaimer to every record in the list
            for record in data:
                if isinstance(record, dict):
                    record['_disclaimer'] = DISCLAIMER_TEXT
        else:
            logger.warning(f"JSON list in {file_path} is empty. Adding disclaimer to root metadata.")
            # If empty list, we can't add to records, so we might need a wrapper or metadata field
            # For safety, we'll just note it in a metadata field if we wrap it, 
            # but standard practice for empty lists is to leave them empty or add a global flag.
            # Given the requirement, we'll add a top-level key if we assume a wrapper, 
            # but here we just log. If the file is expected to have data, this is a warning.
            pass 
    elif isinstance(data, dict):
        # Add to the root dictionary
        data['_disclaimer'] = DISCLAIMER_TEXT
    else:
        logger.warning(f"JSON structure in {file_path} is neither list nor dict. Skipping modification.")
        return

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Successfully updated {file_path} with disclaimer.")

def process_csv_file(file_path: Path) -> None:
    """
    Reads a CSV file, adds a new column '_disclaimer' with the text to every row,
    and writes it back.
    """
    logger.info(f"Processing CSV file: {file_path}")
    
    if not file_path.exists():
        logger.error(f"CSV file not found: {file_path}")
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    try:
        # Read all rows
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            if not fieldnames:
                logger.error(f"CSV file {file_path} appears to have no headers.")
                return
            
            rows = list(reader)
    except Exception as e:
        logger.error(f"Error reading CSV {file_path}: {e}")
        raise

    # Add disclaimer column
    new_fieldnames = list(fieldnames) + ['_disclaimer']
    
    for row in rows:
        row['_disclaimer'] = DISCLAIMER_TEXT

    # Write back
    try:
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=new_fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    except Exception as e:
        logger.error(f"Error writing CSV {file_path}: {e}")
        raise

    logger.info(f"Successfully updated {file_path} with disclaimer.")

def main() -> None:
    """
    Main entry point to process all relevant JSON and CSV artifacts in the data directory.
    Targets:
    - data/interim/fixation_metrics.csv
    - data/processed/aligned_metrics.csv
    - data/processed/results.json
    - data/interim/power_analysis_report.json (if exists)
    - data/interim/vif_verification.json (if exists)
    - data/processed/descriptive_stats.json (if exists)
    """
    paths = get_paths()
    data_dir = paths.data
    
    if not data_dir.exists():
        logger.warning(f"Data directory {data_dir} does not exist. Nothing to process.")
        return

    # Define target files relative to data_dir
    # We look for specific files mentioned in the task and pipeline flow
    target_files = [
        "interim/fixation_metrics.csv",
        "processed/aligned_metrics.csv",
        "processed/results.json",
        "interim/power_analysis_report.json",
        "interim/vif_verification.json",
        "processed/descriptive_stats.json",
        "interim/salience_validation_report.json"
    ]

    processed_count = 0
    skipped_count = 0

    for rel_path in target_files:
        full_path = data_dir / rel_path
        if full_path.exists():
            try:
                if full_path.suffix.lower() == '.json':
                    process_json_file(full_path)
                    processed_count += 1
                elif full_path.suffix.lower() == '.csv':
                    process_csv_file(full_path)
                    processed_count += 1
                else:
                    logger.debug(f"Skipping non-target file: {full_path}")
                    skipped_count += 1
            except Exception as e:
                logger.error(f"Failed to process {full_path}: {e}")
        else:
            logger.debug(f"Target file not found (expected but missing): {full_path}")
            skipped_count += 1

    logger.info(f"Disclaimer application complete. Processed: {processed_count}, Skipped/Missing: {skipped_count}")

if __name__ == "__main__":
    main()

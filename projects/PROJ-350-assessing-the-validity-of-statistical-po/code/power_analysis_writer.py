"""
T026 Implementation: Write final analysis dataset to data/derived/power_analysis.csv

This script reads the processed study records (from T023 power_calc.py),
calculates the power_gap, and writes the final analysis dataset.

It assumes that T023 (process_study_records) has already been run to generate
the intermediate data, or it runs that logic inline if the intermediate file
doesn't exist yet.

Output: data/derived/power_analysis.csv
"""
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.power_calc import process_study_records, calculate_power_gap
from code.utils.data_hygiene import ensure_directory

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
RAW_RECORDS_PATH = PROJECT_ROOT / "data" / "derived" / "study_records_raw.json"
PROCESSED_RECORDS_PATH = PROJECT_ROOT / "data" / "derived" / "study_records_processed.json"
OUTPUT_CSV_PATH = PROJECT_ROOT / "data" / "derived" / "power_analysis.csv"

def load_study_records() -> List[Dict[str, Any]]:
    """Load study records from the raw JSON file."""
    if not RAW_RECORDS_PATH.exists():
        raise FileNotFoundError(
            f"Raw study records not found at {RAW_RECORDS_PATH}. "
            "Run extraction tasks (T016) first."
        )
    
    with open(RAW_RECORDS_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data

def process_and_write_analysis():
    """
    Main execution function for T026.
    
    1. Loads raw study records.
    2. Processes them (calculates sensitivity power and power gap) using code.power_calc.
    3. Writes the final analysis dataset to data/derived/power_analysis.csv.
    """
    logger.info(f"Starting T026: Writing final analysis dataset to {OUTPUT_CSV_PATH}")
    
    # Ensure output directory exists
    ensure_directory(OUTPUT_CSV_PATH.parent)
    
    # Load raw records
    logger.info(f"Loading raw study records from {RAW_RECORDS_PATH}")
    try:
        raw_records = load_study_records()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    if not raw_records:
        logger.warning("No study records found in raw data.")
        # Create empty CSV with headers
        with open(OUTPUT_CSV_PATH, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'study_id', 'osf_id', 'field', 'effect_size_domain',
                'planned_power', 'target_n', 'effect_size_assumption',
                'actual_sample_size', 'sensitivity_power', 'power_gap',
                'missing_planned_data', 'missing_actual_data', 'validation_flags'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
        logger.info(f"Created empty analysis file at {OUTPUT_CSV_PATH}")
        return

    # Process records: calculate sensitivity power and power gap
    logger.info(f"Processing {len(raw_records)} study records...")
    
    # Use the process_study_records function from power_calc.py
    # This function should handle the power calculation logic
    processed_records = process_study_records(raw_records)
    
    # Save processed records for debugging/inspection (optional but helpful)
    with open(PROCESSED_RECORDS_PATH, 'w', encoding='utf-8') as f:
        json.dump(processed_records, f, indent=2, default=str)
    logger.info(f"Saved processed records to {PROCESSED_RECORDS_PATH}")
    
    # Write to CSV
    logger.info(f"Writing analysis dataset to {OUTPUT_CSV_PATH}")
    
    # Define CSV fieldnames based on FR-004 and FR-006 requirements
    fieldnames = [
        'study_id', 'osf_id', 'field', 'effect_size_domain',
        'planned_power', 'target_n', 'effect_size_assumption',
        'actual_sample_size', 'sensitivity_power', 'power_gap',
        'missing_planned_data', 'missing_actual_data', 'validation_flags'
    ]
    
    with open(OUTPUT_CSV_PATH, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        written_count = 0
        for record in processed_records:
            # Ensure all fields are present, fill with None if missing
            row = {field: record.get(field) for field in fieldnames}
            writer.writerow(row)
            written_count += 1
    
    logger.info(f"Successfully wrote {written_count} records to {OUTPUT_CSV_PATH}")
    
    # Log summary statistics
    valid_records = [r for r in processed_records if r.get('power_gap') is not None]
    if valid_records:
        power_gaps = [r['power_gap'] for r in valid_records]
        logger.info(f"Power Gap Statistics (n={len(valid_records)}):")
        logger.info(f"  Mean: {sum(power_gaps)/len(power_gaps):.4f}")
        logger.info(f"  Min: {min(power_gaps):.4f}")
        logger.info(f"  Max: {max(power_gaps):.4f}")
    
    return written_count

def main():
    """Entry point for the script."""
    try:
        count = process_and_write_analysis()
        logger.info(f"T026 completed successfully. Wrote {count} records.")
    except Exception as e:
        logger.error(f"T026 failed with error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

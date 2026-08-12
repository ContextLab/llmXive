"""
Validation module for User Story 1: Matched Dataset Construction.

This script validates the `data/processed/matched_pairs.csv` file to ensure
that every included row contains at least one p-value and one effect size
for both the pre-print and the journal versions.

It flags rows that do not meet these criteria and generates a validation report.
"""
import os
import sys
import csv
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.pdf_parser import is_valid_p_value_range

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'data' / 'logs' / 'validation_log.txt')
    ]
)
logger = logging.getLogger(__name__)

# Constants
INPUT_FILE = project_root / 'data' / 'processed' / 'matched_pairs.csv'
OUTPUT_REPORT = project_root / 'data' / 'results' / 'validation_report.json'
OUTPUT_VALIDATED_CSV = project_root / 'data' / 'processed' / 'matched_pairs_validated.csv'

# Columns to check (expected from previous tasks)
# Based on T017 and T016, we expect columns like:
# preprint_p_value, preprint_effect_size, journal_p_value, journal_effect_size
# We will look for columns containing these keywords or exact names if defined.
# Assuming standard naming convention from extraction:
P_VALUE_COLUMNS = ['preprint_p_value', 'journal_p_value']
EFFECT_SIZE_COLUMNS = ['preprint_effect_size', 'journal_effect_size']

def has_valid_p_value(value_str):
    """
    Checks if a string represents a valid p-value.
    Handles exact values (0.03) and inequalities (< 0.05, > 0.1).
    Returns True if it's a valid representation of a p-value found in the text.
    """
    if not value_str or value_str.strip() == '':
        return False
    try:
        # Try to parse as float first
        val = float(value_str)
        return 0.0 <= val <= 1.0
    except ValueError:
        # Check if it's an inequality handled by the parser
        # The parser usually stores inequalities as strings like "<0.05" or "0.05"
        # or specific markers. We assume if it's not empty and not obviously invalid,
        # it was extracted.
        # However, for strict validation of "at least one", we need to ensure it's not a placeholder.
        val = value_str.strip()
        if val.startswith('<') or val.startswith('>') or val.startswith('='):
            return True
        if val.replace('.', '', 1).isdigit():
            return True
        return False

def has_valid_effect_size(value_str):
    """
    Checks if a string represents a valid effect size (e.g., 0.5, -1.2).
    """
    if not value_str or value_str.strip() == '':
        return False
    try:
        val = float(value_str)
        # Effect sizes can be any real number, but usually within a reasonable range
        # We just check if it's a valid number
        return True
    except ValueError:
        return False

def validate_row(row):
    """
    Validates a single row against the requirements.
    Returns (is_valid, reasons_list)
    """
    reasons = []
    is_valid = True

    # Check Pre-print P-value
    pre_p = row.get('preprint_p_value', '').strip()
    if not has_valid_p_value(pre_p):
        reasons.append("Missing or invalid pre-print p-value")
        is_valid = False

    # Check Journal P-value
    jour_p = row.get('journal_p_value', '').strip()
    if not has_valid_p_value(jour_p):
        reasons.append("Missing or invalid journal p-value")
        is_valid = False

    # Check Pre-print Effect Size
    pre_es = row.get('preprint_effect_size', '').strip()
    if not has_valid_effect_size(pre_es):
        reasons.append("Missing or invalid pre-print effect size")
        is_valid = False

    # Check Journal Effect Size
    jour_es = row.get('journal_effect_size', '').strip()
    if not has_valid_effect_size(jour_es):
        reasons.append("Missing or invalid journal effect size")
        is_valid = False

    return is_valid, reasons

def main():
    logger.info(f"Starting validation for {INPUT_FILE}")

    if not INPUT_FILE.exists():
        logger.error(f"Input file not found: {INPUT_FILE}")
        sys.exit(1)

    validated_rows = []
    failed_rows = []
    total_rows = 0
    valid_count = 0

    with open(INPUT_FILE, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames

        if not fieldnames:
            logger.error("CSV file is empty or has no headers.")
            sys.exit(1)

        # Log available columns for debugging
        logger.info(f"Available columns: {fieldnames}")

        for row in reader:
            total_rows += 1
            is_valid, reasons = validate_row(row)

            if is_valid:
                valid_count += 1
                validated_rows.append(row)
            else:
                failed_rows.append({
                    'row': row,
                    'reasons': reasons
                })

    # Write validated CSV
    if validated_rows:
        with open(OUTPUT_VALIDATED_CSV, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(validated_rows)
        logger.info(f"Validated CSV written to: {OUTPUT_VALIDATED_CSV}")
    else:
        logger.warning("No valid rows found. Validated CSV not created.")

    # Generate Report
    report = {
        "timestamp": datetime.now().isoformat(),
        "input_file": str(INPUT_FILE),
        "total_rows_scanned": total_rows,
        "valid_rows": valid_count,
        "invalid_rows": len(failed_rows),
        "validation_rate": valid_count / total_rows if total_rows > 0 else 0.0,
        "failed_rows_details": [
            {
                "preprint_id": item['row'].get('preprint_id', 'N/A'),
                "journal_id": item['row'].get('journal_id', 'N/A'),
                "reasons": item['reasons']
            }
            for item in failed_rows
        ]
    }

    # Ensure results directory exists
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)

    import json
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation report written to: {OUTPUT_REPORT}")
    logger.info(f"Summary: {valid_count}/{total_rows} rows passed validation.")

    if len(failed_rows) > 0:
        logger.warning(f"Found {len(failed_rows)} rows with missing/invalid data.")
    else:
        logger.info("All rows passed validation.")

    # Exit with non-zero if no valid data found (critical failure for pipeline)
    if valid_count == 0:
        logger.error("Validation failed: No valid data rows found.")
        sys.exit(1)

if __name__ == "__main__":
    main()
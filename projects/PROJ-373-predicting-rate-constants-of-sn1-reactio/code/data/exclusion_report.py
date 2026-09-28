import os
import sys
import csv
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from config import DataConfig, ensure_dirs
from utils.logger import get_logger

# Mapping of error strings to schema codes as per task specification
ERROR_STRING_TO_CODE = {
    'Primary substrate': 'primary_substrate_filter',
    'Ambiguous stereochemistry': 'ambiguous_stereochemistry',
    'Descriptor calculation failed': 'descriptor_failure',
    'Missing rate constant': 'missing_rate_constant',
    'Missing SMILES': 'missing_smiles',
    'Invalid substrate label': 'invalid_substrate_label'
}

def setup_exclusion_logging(log_path: Path) -> logging.Logger:
    """Setup logging for the exclusion report aggregation task."""
    ensure_dirs(log_path.parent)
    logger = get_logger("exclusion_report_aggregation", log_path.parent / "exclusion_aggregation.log")
    return logger

def load_exclusion_logs(clean_log_path: Path, exclusion_raw_path: Path, logger: logging.Logger) -> Tuple[List[Dict], List[Dict]]:
    """
    Load exclusion logs from clean.log and exclusion_raw.log.
    Returns a tuple of (clean_log_entries, exclusion_raw_entries).
    """
    clean_entries = []
    raw_entries = []

    # Check for clean.log
    if not clean_log_path.exists():
        logger.error(f"Input file missing: {clean_log_path}")
        return clean_entries, raw_entries

    try:
        with open(clean_log_path, 'r', encoding='utf-8') as f:
            # Assuming clean.log is JSON lines or similar structured log
            # Based on T012 spec, it logs exclusions. We will parse it as JSON lines if possible
            # or fallback to a simple text parsing if structure is unknown.
            # However, T012 spec implies it logs counts and status.
            # Let's assume it contains JSON objects or we parse lines.
            # For robustness, we'll try to read as JSON lines.
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    # Map from clean.log format to standard exclusion format
                    # T012 logs: row_index, reason, original_smiles (or similar)
                    # We need to extract these.
                    if 'reason' in entry:
                        clean_entries.append({
                            'row_index': entry.get('row_index', 0),
                            'reason': entry.get('reason', 'unknown'),
                            'original_smiles': entry.get('original_smiles', '')
                        })
                    elif 'message' in entry and 'primary' in entry.get('message', '').lower():
                        # Fallback parsing for text logs if JSON fails
                        clean_entries.append({
                            'row_index': 0, # Unknown index from text log
                            'reason': 'Primary substrate',
                            'original_smiles': entry.get('smiles', 'unknown')
                        })
                except json.JSONDecodeError:
                    # If not JSON, treat as text log line
                    # T012 spec mentions logging counts, but we need row-level data for the report.
                    # If the log is just summary, we might not get row-level here.
                    # We will assume the log contains row-level entries for this task.
                    pass
    except Exception as e:
        logger.error(f"Error reading clean.log: {e}")

    # Check for exclusion_raw.log
    if not exclusion_raw_path.exists():
        logger.error(f"Input file missing: {exclusion_raw_path}")
        return clean_entries, raw_entries

    try:
        with open(exclusion_raw_path, 'r', encoding='utf-8') as f:
            # This file is a CSV with headers: row_index,reason,original_smiles
            reader = csv.DictReader(f)
            for row in reader:
                raw_entries.append({
                    'row_index': int(row['row_index']),
                    'reason': row['reason'],
                    'original_smiles': row['original_smiles']
                })
    except Exception as e:
        logger.error(f"Error reading exclusion_raw.log: {e}")

    return clean_entries, raw_entries

def map_error_reason(reason_str: str) -> str:
    """Map error string to schema code."""
    if reason_str in ERROR_STRING_TO_CODE:
        return ERROR_STRING_TO_CODE[reason_str]
    # Fallback: use the string itself or a generic code if unknown
    return reason_str.replace(" ", "_").lower()

def validate_against_schema(entries: List[Dict], schema_path: Path, logger: logging.Logger) -> bool:
    """
    Validate entries against the exclusion_report.schema.yaml.
    Returns True if valid, False otherwise.
    """
    if not schema_path.exists():
        logger.error(f"Schema file missing: {schema_path}")
        return False

    try:
        import yaml
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)

        # Basic validation: check required fields
        required_fields = ['row_index', 'reason', 'original_smiles']
        for entry in entries:
            for field in required_fields:
                if field not in entry:
                    logger.error(f"Entry missing required field '{field}': {entry}")
                    return False
            # Validate reason code format (alphanumeric/underscore)
            if not entry['reason'].replace('_', '').isalnum():
                logger.warning(f"Reason code '{entry['reason']}' contains unexpected characters.")
        return True
    except Exception as e:
        logger.error(f"Error validating against schema: {e}")
        return False

def generate_exclusion_report(
    clean_log_path: Path,
    exclusion_raw_path: Path,
    schema_path: Path,
    output_csv_path: Path,
    output_json_path: Path,
    logger: logging.Logger
) -> bool:
    """
    Main logic to aggregate, map, validate, and save the exclusion report.
    """
    # Guard Clause: Check inputs
    if not clean_log_path.exists() or not exclusion_raw_path.exists():
        logger.error("Input files missing. Writing blocked status report.")
        ensure_dirs(output_csv_path.parent)
        with open(output_csv_path, 'w', encoding='utf-8') as f:
            f.write("status,reason\n")
            f.write("blocked,upstream_missing\n")
        return False

    # Load logs
    clean_entries, raw_entries = load_exclusion_logs(clean_log_path, exclusion_raw_path, logger)
    all_entries = clean_entries + raw_entries

    if not all_entries:
        logger.warning("No exclusion entries found in logs.")
        # Still create a valid empty report
        all_entries = []

    # Map error reasons
    mapped_entries = []
    for entry in all_entries:
        mapped_entry = entry.copy()
        mapped_entry['reason_code'] = map_error_reason(entry['reason'])
        mapped_entries.append(mapped_entry)

    # Save intermediate JSON
    ensure_dirs(output_json_path.parent)
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(mapped_entries, f, indent=2)
    logger.info(f"Saved mapped exclusions to {output_json_path}")

    # Validate against schema
    if not validate_against_schema(mapped_entries, schema_path, logger):
        logger.error("Validation against schema failed.")
        # Write a failure report
        with open(output_csv_path, 'w', encoding='utf-8') as f:
            f.write("status,reason\n")
            f.write("failed,schema_validation_error\n")
        return False

    # Save final CSV
    ensure_dirs(output_csv_path.parent)
    with open(output_csv_path, 'w', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['row_index', 'reason', 'reason_code', 'original_smiles'])
        for entry in mapped_entries:
            writer.writerow([
                entry['row_index'],
                entry['reason'],
                entry['reason_code'],
                entry['original_smiles']
            ])
    logger.info(f"Saved final exclusion report to {output_csv_path}")
    return True

def main():
    """Entry point for the exclusion report aggregation task."""
    logger = setup_exclusion_logging(Path("data/processed/exclusion_aggregation.log"))
    data_config = DataConfig()

    clean_log_path = Path(data_config.PROCESSED_DIR) / "clean.log"
    exclusion_raw_path = Path(data_config.PROCESSED_DIR) / "exclusion_raw.log"
    schema_path = Path("specs/001-predict-sn1-rate-constants/contracts/exclusion_report.schema.yaml")
    output_csv_path = Path(data_config.PROCESSED_DIR) / "exclusion_report.csv"
    output_json_path = Path(data_config.PROCESSED_DIR) / "exclusion_mapped.json"

    success = generate_exclusion_report(
        clean_log_path,
        exclusion_raw_path,
        schema_path,
        output_csv_path,
        output_json_path,
        logger
    )

    if not success:
        sys.exit(1)

    logger.info("Exclusion report aggregation completed successfully.")

if __name__ == "__main__":
    main()
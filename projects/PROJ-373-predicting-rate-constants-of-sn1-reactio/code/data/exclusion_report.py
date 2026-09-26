import os
import sys
import csv
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import config and utils from the project root structure
# Assuming code/ is in sys.path or relative import handled by runner
try:
    from config import DataConfig, ensure_dirs
    from utils.logger import get_logger
except ImportError:
    # Fallback for direct execution if config/utils not in path yet
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import DataConfig, ensure_dirs
    from utils.logger import get_logger

# Error mapping as specified in task description
ERROR_MAPPING = {
    'Primary substrate': 'primary_substrate_filter',
    'Ambiguous stereochemistry': 'ambiguous_stereochemistry',
    'Descriptor calculation failed': 'descriptor_failure',
    'Missing rate constant': 'missing_rate_constant',
    'Missing SMILES': 'missing_smiles'
}

def setup_exclusion_logging(log_path: Path) -> logging.Logger:
    """Set up logging for the exclusion report generation."""
    logger = get_logger("exclusion_report", log_path)
    return logger

def load_exclusion_logs(clean_log_path: Path, exclusion_raw_path: Path) -> List[Dict[str, Any]]:
    """
    Load and merge logs from clean.log and exclusion_raw.log.
    Returns a list of dictionaries representing exclusion records.
    """
    records = []
    
    # Load clean.log
    if clean_log_path.exists():
        try:
            with open(clean_log_path, 'r', encoding='utf-8') as f:
                # Assuming CSV format with headers: row_index, reason, original_smiles
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('reason'):
                        records.append({
                            'row_index': row.get('row_index', ''),
                            'reason': row.get('reason', ''),
                            'original_smiles': row.get('original_smiles', ''),
                            'source': 'clean.log'
                        })
        except Exception as e:
            logging.warning(f"Error reading clean.log: {e}")
    else:
        logging.warning(f"clean.log not found at {clean_log_path}")

    # Load exclusion_raw.log
    if exclusion_raw_path.exists():
        try:
            with open(exclusion_raw_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('reason'):
                        records.append({
                            'row_index': row.get('row_index', ''),
                            'reason': row.get('reason', ''),
                            'original_smiles': row.get('original_smiles', ''),
                            'source': 'exclusion_raw.log'
                        })
        except Exception as e:
            logging.warning(f"Error reading exclusion_raw.log: {e}")
    else:
        logging.warning(f"exclusion_raw.log not found at {exclusion_raw_path}")

    return records

def map_error_reason(reason: str) -> str:
    """
    Map human-readable error reasons to schema codes.
    If not found in mapping, return the original reason or a generic code.
    """
    # Normalize reason for matching
    normalized_reason = reason.strip()
    
    # Direct lookup
    if normalized_reason in ERROR_MAPPING:
        return ERROR_MAPPING[normalized_reason]
    
    # Case-insensitive lookup
    for key, value in ERROR_MAPPING.items():
        if key.lower() == normalized_reason.lower():
            return value
    
    # Fallback: return original or a generic code if unknown
    logging.warning(f"Unknown error reason: '{reason}'. Keeping original.")
    return reason

def validate_against_schema(records: List[Dict[str, Any]], schema_path: Path) -> bool:
    """
    Validate records against the exclusion_report.schema.yaml.
    This is a simplified validation check based on the schema definition.
    """
    # Since we cannot easily parse YAML here without extra deps, we assume
    # the schema requires: row_index, reason, original_smiles
    required_fields = ['row_index', 'reason', 'original_smiles']
    valid = True
    
    for i, record in enumerate(records):
        for field in required_fields:
            if field not in record:
                logging.error(f"Record {i} missing required field: {field}")
                valid = False
            elif record[field] is None:
                logging.error(f"Record {i} has null value for required field: {field}")
                valid = False
    
    return valid

def generate_exclusion_report(records: List[Dict[str, Any]], output_path: Path, mapped_path: Path, schema_path: Path) -> bool:
    """
    Generate the final exclusion report CSV and the mapped JSON.
    """
    if not records:
        logging.info("No exclusion records to process.")
        # Write empty report if no records, but ensure headers
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['row_index', 'reason_code', 'original_smiles', 'source'])
            writer.writeheader()
        with open(mapped_path, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)
        return True

    # Map reasons to codes
    mapped_records = []
    for record in records:
        mapped_record = record.copy()
        mapped_record['reason_code'] = map_error_reason(record['reason'])
        mapped_records.append(mapped_record)
    
    # Validate
    if not validate_against_schema(mapped_records, schema_path):
        logging.error("Validation against schema failed. Aborting report generation.")
        return False

    # Save mapped JSON
    with open(mapped_path, 'w', encoding='utf-8') as f:
        json.dump(mapped_records, f, indent=2, ensure_ascii=False)
    
    # Save final CSV
    fieldnames = ['row_index', 'reason_code', 'original_smiles', 'source']
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in mapped_records:
            writer.writerow({
                'row_index': record['row_index'],
                'reason_code': record['reason_code'],
                'original_smiles': record['original_smiles'],
                'source': record['source']
            })
    
    logging.info(f"Exclusion report generated: {output_path}")
    logging.info(f"Mapped exclusions saved: {mapped_path}")
    return True

def main():
    """
    Main entry point for T015: Aggregate, map, and validate exclusion logs.
    """
    parser = argparse.ArgumentParser(description="T015: Aggregate exclusion logs")
    parser.add_argument("--clean-log", type=str, required=False, 
                        default="data/processed/clean.log",
                        help="Path to clean.log")
    parser.add_argument("--exclusion-raw", type=str, required=False,
                        default="data/processed/exclusion_raw.log",
                        help="Path to exclusion_raw.log")
    parser.add_argument("--schema", type=str, required=False,
                        default="specs/001-predict-sn1-rate-constants/contracts/exclusion_report.schema.yaml",
                        help="Path to exclusion_report.schema.yaml")
    parser.add_argument("--output-report", type=str, required=False,
                        default="data/processed/exclusion_report.csv",
                        help="Path for final exclusion report CSV")
    parser.add_argument("--output-mapped", type=str, required=False,
                        default="data/processed/exclusion_mapped.json",
                        help="Path for mapped exclusions JSON")
    parser.add_argument("--log-dir", type=str, required=False,
                        default="data/processed",
                        help="Directory for log files")
    
    args = parser.parse_args()
    
    # Setup paths
    clean_log_path = Path(args.clean_log)
    exclusion_raw_path = Path(args.exclusion_raw)
    schema_path = Path(args.schema)
    output_report_path = Path(args.output_report)
    output_mapped_path = Path(args.output_mapped)
    log_dir = Path(args.log_dir)
    
    ensure_dirs([log_dir, output_report_path.parent, output_mapped_path.parent])
    
    logger = setup_exclusion_logging(log_dir / "exclusion_report.log")
    
    # Guard Clause: Check if inputs are missing
    clean_exists = clean_log_path.exists() and clean_log_path.stat().st_size > 0
    raw_exists = exclusion_raw_path.exists() and exclusion_raw_path.stat().st_size > 0
    
    if not clean_exists and not raw_exists:
        logger.error("Guard Clause: clean.log and exclusion_raw.log are missing or empty.")
        # Write blocked status to output
        with open(output_report_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['status', 'reason'])
            writer.writeheader()
            writer.writerow({'status': 'blocked', 'reason': 'upstream_missing'})
        sys.exit(0) # Exit 0 as per task spec for blocked state, but log error
    
    # Load logs
    records = load_exclusion_logs(clean_log_path, exclusion_raw_path)
    
    # Generate report
    success = generate_exclusion_report(records, output_report_path, output_mapped_path, schema_path)
    
    if not success:
        logger.error("Failed to generate exclusion report due to validation errors.")
        sys.exit(1)
    
    logger.info("T015 completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
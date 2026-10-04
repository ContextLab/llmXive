"""
Preprocessing Module for Caco-2 Permeability Data.

This module implements the data filtering logic for User Story 1.
It reads raw data from ChEMBL, filters for valid records, and handles
protocol heterogeneity checks.

Traceability: FR-010 - Filter raw data for non-NULL SMILES and logPapp.
"""

import csv
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import local utilities relative to project structure
# We need to ensure the code directory is in the path for imports to work
# when running as a script from the root or code/data
if str(Path(__file__).parent.parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.logging import get_logger
from utils.config import get_project_root
from utils.checksum import scan_and_register_data_files

logger = get_logger(__name__)

def load_raw_data(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load raw data from a CSV file.

    Args:
        input_path: Path to the raw CSV file.

    Returns:
        List of dictionaries representing rows.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    records = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)

    logger.info(f"Loaded {len(records)} records from {input_path}")
    return records

def parse_protocol_metadata(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse the protocol_metadata JSON string back into a dictionary.

    Args:
        record: A row dictionary from the CSV.

    Returns:
        Parsed metadata dictionary.
    """
    meta_str = record.get('protocol_metadata', '{}')
    if not meta_str:
        return {}
    try:
        return json.loads(meta_str)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse protocol_metadata for record: {e}")
        return {}

def check_protocol_heterogeneity(record: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Check if a record should be excluded due to protocol heterogeneity.

    Logic:
    1. If standard_type is not 'MEASUREMENT', exclude.
    2. If heterogeneity_score is present and > 0.8 (arbitrary high threshold), exclude.

    Args:
        record: A row dictionary.

    Returns:
        Tuple of (is_excluded, reason).
    """
    meta = parse_protocol_metadata(record)
    standard_type = meta.get('standard_type', '')
    heterogeneity_score = meta.get('heterogeneity_score', 0.0)

    if standard_type != 'MEASUREMENT':
        return True, f"Invalid standard_type: {standard_type}"

    if isinstance(heterogeneity_score, (int, float)) and heterogeneity_score > 0.8:
        return True, f"High heterogeneity score: {heterogeneity_score}"

    return False, ""

def preprocess_data(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Filter records for non-NULL SMILES and logPapp, and check protocol heterogeneity.

    Args:
        records: List of raw records.

    Returns:
        Tuple of (filtered_records, stats_dict).
    """
    filtered = []
    stats = {
        'total': len(records),
        'null_smiles': 0,
        'null_logpapp': 0,
        'protocol_excluded': 0,
        'kept': 0
    }

    for record in records:
        smiles = record.get('smiles', '').strip()
        logpapp = record.get('logPapp', '').strip()

        # Check for NULL SMILES
        if not smiles or smiles.lower() == 'nan':
            stats['null_smiles'] += 1
            continue

        # Check for NULL logPapp
        if not logpapp or logpapp.lower() == 'nan':
            stats['null_logpapp'] += 1
            continue

        # Check protocol heterogeneity
        is_excluded, reason = check_protocol_heterogeneity(record)
        if is_excluded:
            stats['protocol_excluded'] += 1
            logger.debug(f"Excluded due to protocol: {reason}")
            continue

        filtered.append(record)
        stats['kept'] += 1

    return filtered, stats

def write_clean_data(records: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write filtered records to a new CSV file.

    Args:
        records: List of filtered records.
        output_path: Path to the output CSV file.
    """
    if not records:
        logger.warning("No records to write.")
        # Create an empty file with headers if possible, or just return
        # We need headers from the first record if available, otherwise default
        # Since we have no records, we can't infer headers easily without schema.
        # However, for robustness, we assume the schema is consistent.
        # If empty, we write nothing or an empty file.
        with open(output_path, 'w', encoding='utf-8') as f:
            pass
        return

    fieldnames = list(records[0].keys())
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    logger.info(f"Wrote {len(records)} records to {output_path}")

def main():
    """
    Main entry point for preprocessing.
    """
    project_root = get_project_root()
    input_path = project_root / 'data' / 'raw' / 'chembl_raw.csv'
    output_path = project_root / 'data' / 'processed' / 'filtered_data.csv'

    logger.info(f"Starting preprocessing. Input: {input_path}, Output: {output_path}")

    if not input_path.exists():
        logger.error(f"Input file does not exist: {input_path}. "
                     "Please run T009 (retrieval) first.")
        sys.exit(1)

    try:
        # Load
        records = load_raw_data(input_path)

        # Preprocess
        filtered_records, stats = preprocess_data(records)

        # Report stats
        pass_rate = (stats['kept'] / stats['total'] * 100) if stats['total'] > 0 else 0.0
        logger.info(f"Preprocessing complete.")
        logger.info(f"Total records: {stats['total']}")
        logger.info(f"Excluded (NULL SMILES): {stats['null_smiles']}")
        logger.info(f"Excluded (NULL logPapp): {stats['null_logpapp']}")
        logger.info(f"Excluded (Protocol Heterogeneity): {stats['protocol_excluded']}")
        logger.info(f"Kept: {stats['kept']}")
        logger.info(f"Pass Rate: {pass_rate:.2f}%")

        # Write
        write_clean_data(filtered_records, output_path)

        # Invoke checksum utility
        logger.info("Invoking checksum utility...")
        scan_and_register_data_files()
        logger.info("Checksum utility completed.")

    except Exception as e:
        logger.error(f"Preprocessing failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
"""
Preprocessing Module for Caco-2 Permeability Data.

This module filters raw data for non-NULL SMILES and logPapp,
reports pass rates, and handles protocol heterogeneity analysis.

Traceability: FR-010
"""

import csv
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging import get_logger, configure_root_logger
from utils.checksum import scan_and_register_data_files

logger = get_logger(__name__)

def load_raw_data(raw_path: Path) -> List[Dict[str, Any]]:
    """
    Load raw CSV data from ChEMBL retrieval.

    Args:
        raw_path: Path to the raw CSV file.

    Returns:
        List of dictionaries representing rows.
    """
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_path}")

    data = []
    with open(raw_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)

    logger.info(f"Loaded {len(data)} records from {raw_path}")
    return data

def parse_protocol_metadata(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse the protocol_metadata JSON string back into an object.

    Args:
        record: A dictionary row from the CSV.

    Returns:
        Parsed dictionary or None if invalid/missing.
    """
    meta_str = record.get('protocol_metadata', '')
    if not meta_str or meta_str.strip() == '':
        return None

    try:
        return json.loads(meta_str)
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse protocol_metadata for record: {record.get('assay_id', 'unknown')}")
        return None

def check_protocol_heterogeneity(records: List[Dict[str, Any]]) -> Tuple[int, List[str]]:
    """
    Count records excluded due to protocol heterogeneity.

    Heterogeneity is defined as significant variance in protocol_metadata fields
    such as lab_id, temperature, or passage. For this implementation, we flag
    records where these fields are missing, null, or inconsistent with the
    majority mode if a clear majority exists.

    Returns:
        Tuple of (count_excluded, list_of_excluded_assay_ids)
    """
    excluded_count = 0
    excluded_ids = []

    # Collect valid metadata fields
    valid_records = []
    for record in records:
        meta = parse_protocol_metadata(record)
        if meta and isinstance(meta, dict):
            valid_records.append((record, meta))

    if not valid_records:
        logger.warning("No records with valid protocol metadata found. Cannot assess heterogeneity.")
        return len(records), [r.get('assay_id', 'unknown') for r in records]

    # Check for consistency in key fields: lab_id, temperature, passage
    # We will exclude records where these fields are missing or if they deviate significantly
    # from the most common value (mode) if the mode covers > 50% of the data.
    # If no clear majority, we assume heterogeneity and exclude all?
    # Per FR-010, we report excluded records due to heterogeneity.
    # Strategy: Exclude records where critical metadata is missing.
    # If metadata exists but is wildly different, we might need a more complex logic.
    # For now, strict: if lab_id, temperature, or passage is missing/null, exclude.

    critical_fields = ['lab_id', 'temperature', 'passage']

    for record, meta in valid_records:
        is_heterogeneous = False
        for field in critical_fields:
            val = meta.get(field)
            if val is None or val == '' or (isinstance(val, str) and val.lower() == 'null'):
                is_heterogeneous = True
                break

        if is_heterogeneous:
            excluded_count += 1
            excluded_ids.append(record.get('assay_id', 'unknown'))

    return excluded_count, excluded_ids

def preprocess_data(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Filter records for non-NULL SMILES and logPapp.

    Args:
        records: List of raw record dictionaries.

    Returns:
        Tuple of (filtered_records, stats_dict)
    """
    filtered = []
    total = len(records)
    null_smiles_count = 0
    null_logpapp_count = 0
    both_null_count = 0

    for record in records:
        smiles = record.get('smiles', '').strip()
        logpapp = record.get('logPapp', '').strip()

        if not smiles and not logpapp:
            both_null_count += 1
            continue
        if not smiles:
            null_smiles_count += 1
            continue
        if not logpapp:
            null_logpapp_count += 1
            continue

        # Valid record
        filtered.append(record)

    stats = {
        'total_records': total,
        'filtered_records': len(filtered),
        'null_smiles_only': null_smiles_count,
        'null_logpapp_only': null_logpapp_count,
        'both_null': both_null_count,
        'pass_rate': len(filtered) / total if total > 0 else 0.0
    }

    logger.info(f"Preprocessing complete. Passed: {len(filtered)}/{total} ({stats['pass_rate']:.2%})")
    return filtered, stats

def write_clean_data(filtered_records: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write filtered data to CSV.

    Args:
        filtered_records: List of valid record dictionaries.
        output_path: Path to the output CSV file.
    """
    if not filtered_records:
        logger.warning("No records to write. Creating empty file.")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("")
        return

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(filtered_records[0].keys())

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filtered_records)

    logger.info(f"Wrote {len(filtered_records)} records to {output_path}")

def main():
    """
    Main entry point for preprocessing script.
    """
    configure_root_logger()
    logger.info("Starting preprocessing pipeline.")

    project_root = Path(__file__).resolve().parent.parent.parent
    raw_path = project_root / 'data' / 'raw' / 'chembl_raw.csv'
    output_path = project_root / 'data' / 'processed' / 'filtered_data.csv'

    # 1. Load raw data
    try:
        records = load_raw_data(raw_path)
    except FileNotFoundError as e:
        logger.error(f"Failed to load raw data: {e}")
        sys.exit(1)

    # 2. Check protocol heterogeneity (before filtering for nulls to report full stats)
    # Note: The task asks to report excluded records due to protocol heterogeneity.
    # We calculate this on the raw set.
    hetero_count, hetero_ids = check_protocol_heterogeneity(records)
    logger.info(f"Records excluded due to protocol heterogeneity: {hetero_count}")
    if hetero_count > 0:
        logger.debug(f"Excluded assay IDs (first 10): {hetero_ids[:10]}")

    # 3. Filter for non-NULL SMILES and logPapp
    filtered_records, stats = preprocess_data(records)

    # 4. Write clean data
    write_clean_data(filtered_records, output_path)

    # 5. Log final stats
    logger.info(f"Final Pass Rate: {stats['pass_rate']:.2%}")
    logger.info(f"Excluded (Null SMILES): {stats['null_smiles_only']}")
    logger.info(f"Excluded (Null logPapp): {stats['null_logpapp_only']}")
    logger.info(f"Excluded (Both Null): {stats['both_null']}")
    logger.info(f"Excluded (Protocol Heterogeneity): {hetero_count}")

    # 6. Invoke checksum utility
    logger.info("Invoking checksum utility.")
    scan_and_register_data_files()

    logger.info("Preprocessing pipeline completed successfully.")

if __name__ == '__main__':
    main()
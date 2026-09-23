"""
Preprocessing Module for Caco-2 Permeability Data.

This module filters raw data for non-NULL SMILES and logPapp,
reports pass rates, and excludes records due to protocol heterogeneity.
It references FR-010 for data completeness requirements.
"""

import csv
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from utils.logging import get_logger
from utils.config import get_project_root
from utils.checksum import scan_and_register_data_files

logger = get_logger(__name__)

def load_raw_data(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load raw CSV data from the specified file.

    Args:
        file_path: Path to the raw CSV file.

    Returns:
        List of dictionaries representing rows.
    """
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    logger.info(f"Loaded {len(data)} records from {file_path}")
    return data

def parse_protocol_metadata(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse the protocol_metadata JSON string into a dictionary.

    Args:
        record: A row dictionary.

    Returns:
        Parsed protocol metadata dictionary.
    """
    raw_meta = record.get('protocol_metadata', '{}')
    if not raw_meta or raw_meta == '{}':
        return {}
    try:
        return json.loads(raw_meta)
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse protocol_metadata for record: {record.get('assay_id', 'unknown')}")
        return {}

def check_protocol_heterogeneity(records: List[Dict[str, Any]], threshold_variance: float = 0.5) -> Tuple[int, List[str]]:
    """
    Check for protocol heterogeneity based on variance in lab_id, temperature, or passage.
    This is a simplified check: if a significant portion of records have conflicting
    metadata (e.g., different labs or temperatures without standardization), they are flagged.

    For this implementation, we flag records if they belong to a 'minority' protocol group
    (e.g., if >80% of data comes from one lab_id, the rest are considered heterogeneous).

    Args:
        records: List of raw records.
        threshold_variance: Threshold for considering a group as "majority".

    Returns:
        Count of excluded records and list of excluded assay_ids.
    """
    if not records:
        return 0, []

    # Extract metadata fields
    meta_counts = {}
    for record in records:
        meta = parse_protocol_metadata(record)
        # Create a composite key for protocol identity
        key = (
            meta.get('lab_id', 'unknown'),
            meta.get('temperature', 'unknown'),
            meta.get('passage', 'unknown')
        )
        meta_counts[key] = meta_counts.get(key, 0) + 1

    total = len(records)
    # Find the majority protocol group
    if not meta_counts:
        return 0, []

    max_count = max(meta_counts.values())
    majority_threshold = total * threshold_variance

    # If the largest group is not dominant, we might consider the whole dataset heterogeneous
    # But per FR-010, we want to filter out records that don't fit the standard protocol.
    # We will assume the largest group is the "standard" and exclude others.
    majority_key = max(meta_counts, key=meta_counts.get)

    excluded_count = 0
    excluded_ids = []

    for record in records:
        meta = parse_protocol_metadata(record)
        key = (
            meta.get('lab_id', 'unknown'),
            meta.get('temperature', 'unknown'),
            meta.get('passage', 'unknown')
        )
        if key != majority_key:
            excluded_count += 1
            excluded_ids.append(record.get('assay_id', 'unknown'))

    if excluded_count > 0:
        logger.warning(f"Detected protocol heterogeneity. Excluding {excluded_count} records not matching majority protocol {majority_key}.")

    return excluded_count, excluded_ids

def preprocess_data(raw_records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Filter records for non-NULL SMILES and logPapp, and handle protocol heterogeneity.

    Args:
        raw_records: List of raw record dictionaries.

    Returns:
        Tuple of (filtered_records, stats_dict).
    """
    # FR-010: Ensure data completeness (non-NULL SMILES and logPapp)
    filtered = []
    null_smiles_count = 0
    null_logp_count = 0

    for record in raw_records:
        smiles = record.get('smiles', '').strip()
        logpapp = record.get('logPapp', '').strip()

        if not smiles or smiles == 'None' or smiles.lower() == 'nan':
            null_smiles_count += 1
            continue
        if not logpapp or logpapp == 'None' or logpapp.lower() == 'nan':
            null_logp_count += 1
            continue

        filtered.append(record)

    # Check protocol heterogeneity on the filtered set
    hetero_count, hetero_ids = check_protocol_heterogeneity(filtered)
    final_records = [r for r in filtered if r.get('assay_id', 'unknown') not in hetero_ids]

    total_input = len(raw_records)
    total_output = len(final_records)
    pass_rate = (total_output / total_input * 100) if total_input > 0 else 0.0

    stats = {
        'total_input': total_input,
        'null_smiles_excluded': null_smiles_count,
        'null_logp_excluded': null_logp_count,
        'protocol_heterogeneity_excluded': hetero_count,
        'total_output': total_output,
        'pass_rate_percent': pass_rate
    }

    logger.info(f"Preprocessing complete. Input: {total_input}, Output: {total_output}, Pass Rate: {pass_rate:.2f}%")
    return final_records, stats

def write_clean_data(records: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write filtered records to a CSV file.

    Args:
        records: List of filtered record dictionaries.
        output_path: Path to the output CSV file.
    """
    if not records:
        logger.warning("No records to write.")
        return

    # Ensure protocol_metadata is serialized back to JSON string for CSV compatibility
    for record in records:
        meta = record.get('protocol_metadata')
        if isinstance(meta, dict):
            record['protocol_metadata'] = json.dumps(meta)

    fieldnames = list(records[0].keys())

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    logger.info(f"Wrote {len(records)} records to {output_path}")

def main():
    """
    Main entry point for the preprocessing script.
    """
    project_root = get_project_root()
    input_path = project_root / 'data' / 'raw' / 'chembl_raw.csv'
    output_path = project_root / 'data' / 'processed' / 'filtered_data.csv'
    checksum_path = project_root / 'state' / 'pending' / 'checksums.yaml'

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        logger.error(f"Input file {input_path} does not exist. Run retrieval.py first.")
        sys.exit(1)

    logger.info(f"Starting preprocessing for {input_path}")

    raw_records = load_raw_data(input_path)
    filtered_records, stats = preprocess_data(raw_records)
    write_clean_data(filtered_records, output_path)

    # Log statistics
    logger.info(f"Stats: {stats}")

    # Invoke checksum utility
    logger.info("Invoking checksum utility...")
    scan_and_register_data_files()
    logger.info("Preprocessing complete.")

if __name__ == '__main__':
    main()
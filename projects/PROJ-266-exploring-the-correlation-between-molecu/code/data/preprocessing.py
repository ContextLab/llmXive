"""
Preprocessing Module for Caco-2 Permeability Data.

This module filters raw ChEMBL data to ensure data completeness and protocol
consistency. It reads the raw CSV, parses JSON metadata, filters for valid
SMILES and logPapp values, and enforces the 'MEASUREMENT' standard type.

Traceability:
- FR-010: Filter raw data for non-NULL SMILES and logPapp.
- FR-002: Report pass‑rate and protocol heterogeneity count.
"""

import csv
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Project utilities
from utils.logging import get_logger, configure_root_logger
from utils.config import get_project_root
from utils.checksum import run_checksum_utility

# Configure logger for this module
logger = get_logger(__name__)

def load_raw_data(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load raw data from a CSV file.

    Args:
        file_path: Path to the raw CSV file.

    Returns:
        List of dictionaries representing the rows.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {file_path}")

    data: List[Dict[str, Any]] = []
    with file_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)

    logger.info(f"Loaded {len(data)} records from {file_path}")
    return data

def parse_protocol_metadata(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse the protocol_metadata JSON string back into a dictionary.

    Args:
        record: A dictionary representing a row from the raw CSV.

    Returns:
        Parsed dictionary or empty dict if parsing fails.
    """
    metadata_str = record.get("protocol_metadata", "{}")
    if not metadata_str or metadata_str == "{}":
        return {}

    try:
        return json.loads(metadata_str)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse protocol_metadata for record: {e}")
        return {}

def check_protocol_heterogeneity(records: List[Dict[str, Any]]) -> Tuple[int, int]:
    """
    Count records where ``standard_type`` is not ``MEASUREMENT``.

    Args:
        records: List of raw records.

    Returns:
        Tuple of (total_records, excluded_count).
    """
    excluded_count = 0
    for record in records:
        metadata = parse_protocol_metadata(record)
        if metadata.get("standard_type") != "MEASUREMENT":
            excluded_count += 1
    return len(records), excluded_count

def preprocess_data(
    raw_data: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], int, int]:
    """
    Filter raw data for non‑NULL SMILES, logPapp, and correct protocol
    ``standard_type``.

    Args:
        raw_data: List of raw records.

    Returns:
        Tuple of (filtered_data, total_excluded, excluded_due_to_protocol).
    """
    filtered_data: List[Dict[str, Any]] = []
    total_excluded = 0
    excluded_due_to_protocol = 0

    for record in raw_data:
        # SMILES must be present and non‑empty
        smiles = record.get("smiles")
        if not smiles or not smiles.strip():
            total_excluded += 1
            continue

        # logPapp must be present and not a null placeholder
        logpapp = record.get("logPapp")
        if logpapp is None or logpapp == "" or str(logpapp).upper() == "NULL":
            total_excluded += 1
            continue

        # Protocol must be MEASUREMENT
        metadata = parse_protocol_metadata(record)
        if metadata.get("standard_type") != "MEASUREMENT":
            excluded_due_to_protocol += 1
            total_excluded += 1
            continue

        # Normalise logPapp to string (CSV consistency)
        if isinstance(logpapp, (int, float)):
            record["logPapp"] = str(logpapp)

        filtered_data.append(record)

    return filtered_data, total_excluded, excluded_due_to_protocol

def write_clean_data(data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write the filtered data to a CSV file.

    Args:
        data: List of filtered records.
        output_path: Path to the output CSV file.
    """
    if not data:
        logger.warning("No data to write.")
        return

    # Ensure the directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(data[0].keys())
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    logger.info(f"Wrote {len(data)} records to {output_path}")

def main() -> None:
    """
    Main entry point for the preprocessing script.
    """
    configure_root_logger()
    logger.info("Starting data preprocessing.")

    project_root = get_project_root()
    # NOTE: the retrieval script writes to ``chembl_caco2_raw.csv``.
    raw_data_path = project_root / "data" / "raw" / "chembl_caco2_raw.csv"
    output_path = project_root / "data" / "processed" / "filtered_data.csv"

    # Load raw data
    try:
        raw_data = load_raw_data(raw_data_path)
    except FileNotFoundError as e:
        logger.error(f"Cannot proceed: {e}")
        sys.exit(1)

    # Protocol heterogeneity check (for reporting)
    total_records, protocol_excluded = check_protocol_heterogeneity(raw_data)
    logger.info(
        f"Protocol heterogeneity check: {protocol_excluded} records excluded out of {total_records}."
    )

    # Apply filtering
    filtered_data, total_excluded, _ = preprocess_data(raw_data)

    # Compute and report pass‑rate (as a proportion between 0 and 1)
    pass_rate = len(filtered_data) / len(raw_data) if raw_data else 0.0
    logger.info(f"Pass‑rate (valid / raw): {pass_rate:.4f} ({pass_rate * 100:.2f} %)")
    logger.info(f"Total records excluded (any reason): {total_excluded}")
    logger.info(f"Records excluded due to protocol heterogeneity: {protocol_excluded}")

    # Write the cleaned dataset
    write_clean_data(filtered_data, output_path)

    # Register new artefacts in the checksum manifest
    logger.info("Invoking checksum utility to register new artefacts.")
    run_checksum_utility()

    logger.info("Data preprocessing completed successfully.")

if __name__ == "__main__":
    main()
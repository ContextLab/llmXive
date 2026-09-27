"""
Preprocessing Module for Caco-2 Permeability Data.

This module implements User Story 1 (T010): filtering raw ChEMBL data for
non-NULL SMILES and logPapp, handling protocol heterogeneity, and producing
a clean dataset for downstream analysis.

Traceability: FR-010
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

def load_raw_data(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load raw CSV data from ChEMBL retrieval.

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

    logger.info(f"Loaded {len(records)} raw records from {input_path}")
    return records

def parse_protocol_metadata(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse the JSON string in 'protocol_metadata' column back to an object.

    Args:
        record: A row dictionary.

    Returns:
        Parsed dictionary or None if parsing fails.
    """
    meta_str = record.get('protocol_metadata', '')
    if not meta_str or meta_str.strip() == '':
        return None

    try:
        return json.loads(meta_str)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse protocol_metadata: {e}")
        return None

def check_protocol_heterogeneity(records: List[Dict[str, Any]]) -> Tuple[int, Dict[str, Any]]:
    """
    Analyze protocol metadata for heterogeneity.

    Counts records excluded due to significant variance in protocol fields
    (lab_id, temperature, passage).

    Args:
        records: List of parsed records with metadata.

    Returns:
        Tuple of (excluded_count, stats_dict).
    """
    excluded_count = 0
    stats = {
        'total_records': len(records),
        'unique_lab_ids': set(),
        'unique_temperatures': set(),
        'unique_passages': set(),
        'heterogeneous_records': 0
    }

    # Collect unique values to assess heterogeneity
    valid_records_with_meta = []
    for record in records:
        meta = record.get('_parsed_metadata')
        if meta:
            valid_records_with_meta.append(record)
            if 'lab_id' in meta:
                stats['unique_lab_ids'].add(meta['lab_id'])
            if 'temperature' in meta:
                stats['unique_temperatures'].add(meta['temperature'])
            if 'passage' in meta:
                stats['unique_passages'].add(meta['passage'])

    # Determine threshold for heterogeneity
    # If there are > 3 unique values for a critical field, we consider it heterogeneous
    # and flag those records for exclusion or reporting.
    # For this implementation, we count records that belong to "minority" protocols
    # if the total unique count is high, or simply report the variance.
    # Per task: "Count and report the number of records excluded due to protocol heterogeneity"
    # We will exclude records where the protocol metadata is missing OR
    # where the protocol is part of a set of > 5 distinct lab_ids (high heterogeneity).

    threshold_lab_ids = 5
    if len(stats['unique_lab_ids']) > threshold_lab_ids:
        # Exclude records that don't belong to the most common lab_id
        from collections import Counter
        lab_ids = [r['_parsed_metadata']['lab_id'] for r in valid_records_with_meta if 'lab_id' in r['_parsed_metadata']]
        if lab_ids:
            counter = Counter(lab_ids)
            most_common_lab = counter.most_common(1)[0][0]
            for record in valid_records_with_meta:
                meta = record['_parsed_metadata']
                if 'lab_id' in meta and meta['lab_id'] != most_common_lab:
                    excluded_count += 1
                    stats['heterogeneous_records'] += 1
            # We keep the records from the most common lab, exclude others
            # Note: This logic assumes we want a homogeneous subset.
            # If the task implies counting ALL records in heterogeneous batches as excluded,
            # and we have > threshold, then we exclude ALL.
            # Let's refine: If heterogeneity is detected (many labs), we exclude records
            # that are NOT from the dominant protocol to ensure homogeneity.
            # The count returned is the number of excluded records.
    else:
        # Low heterogeneity, no exclusions based on protocol variance
        pass

    # Convert sets to lists for JSON serializability in stats
    stats['unique_lab_ids'] = list(stats['unique_lab_ids'])
    stats['unique_temperatures'] = list(stats['unique_temperatures'])
    stats['unique_passages'] = list(stats['unique_passages'])

    return excluded_count, stats

def preprocess_data(raw_records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Filter raw data for non-NULL SMILES and logPapp.

    Args:
        raw_records: List of raw record dictionaries.

    Returns:
        Tuple of (filtered_records, statistics).
    """
    filtered = []
    stats = {
        'total_input': len(raw_records),
        'null_smiles': 0,
        'null_logpapp': 0,
        'protocol_missing': 0,
        'filtered_output': 0
    }

    for record in raw_records:
        smiles = record.get('smiles', '').strip()
        logpapp = record.get('logPapp', '').strip()

        if not smiles:
            stats['null_smiles'] += 1
            continue

        if not logpapp or logpapp.lower() == 'nan' or logpapp == '':
            stats['null_logpapp'] += 1
            continue

        # Parse metadata
        meta = parse_protocol_metadata(record)
        if meta:
            record['_parsed_metadata'] = meta
        else:
            stats['protocol_missing'] += 1
            # We do not exclude just for missing metadata, but we log it.
            # The heterogeneity check handles exclusion logic later.
            record['_parsed_metadata'] = {}

        filtered.append(record)

    stats['filtered_output'] = len(filtered)
    return filtered, stats

def write_clean_data(records: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write filtered records to CSV.

    Args:
        records: List of filtered record dictionaries.
        output_path: Path to the output CSV.
    """
    if not records:
        logger.warning("No records to write.")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Define fields, ensuring protocol_metadata is serialized back to string
    fieldnames = ['smiles', 'logPapp', 'mw', 'psa', 'assay_id', 'protocol_metadata']

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()

        for record in records:
            # Ensure protocol_metadata is a JSON string
            if '_parsed_metadata' in record:
                record['protocol_metadata'] = json.dumps(record['_parsed_metadata'])
                del record['_parsed_metadata']
            writer.writerow(record)

    logger.info(f"Wrote {len(records)} clean records to {output_path}")

def main():
    """
    Main entry point for preprocessing.
    """
    project_root = get_project_root()
    input_path = project_root / 'data' / 'raw' / 'chembl_raw.csv'
    output_path = project_root / 'data' / 'processed' / 'filtered_data.csv'

    logger.info("Starting preprocessing pipeline (T010).")

    try:
        # 1. Load
        raw_records = load_raw_data(input_path)

        # 2. Preprocess (Filter NULLs)
        filtered_records, filter_stats = preprocess_data(raw_records)
        logger.info(f"Filtering stats: {filter_stats}")

        # 3. Check Heterogeneity
        excluded_count, hetero_stats = check_protocol_heterogeneity(filtered_records)
        logger.info(f"Heterogeneity analysis: Excluded {excluded_count} records. Stats: {hetero_stats}")

        # Note: The task asks to "Count and report... excluded records due to protocol heterogeneity".
        # The logic in check_protocol_heterogeneity calculates this.
        # For this implementation, we will NOT remove the heterogeneous records from the output CSV
        # unless explicitly required to "filter" them out. The task says "Filter for non-NULL...
        # reporting pass rate and excluded records due to protocol heterogeneity".
        # Usually, "excluded" means they are not in the final dataset.
        # Let's refine: If we identified them as heterogeneous, we should probably exclude them
        # from the final clean data if the goal is a homogeneous dataset.
        # However, the primary filter is NULLs. The heterogeneity is a report metric.
        # To be safe and produce a "clean" dataset as per US1 goals, we will remove the
        # heterogeneous records identified in step 3 if the count is non-zero.

        final_records = filtered_records
        if excluded_count > 0:
            # Re-apply exclusion based on the logic used in check_protocol_heterogeneity
            # We need to re-identify which ones to drop.
            # Since check_protocol_heterogeneity didn't return the specific IDs,
            # we re-run the logic to filter.
            from collections import Counter

            valid_with_meta = [r for r in filtered_records if r.get('_parsed_metadata')]
            if valid_with_meta:
                lab_ids = [r['_parsed_metadata'].get('lab_id') for r in valid_with_meta if r['_parsed_metadata'].get('lab_id')]
                if lab_ids and len(set(lab_ids)) > 5:
                    counter = Counter(lab_ids)
                    most_common = counter.most_common(1)[0][0]
                    final_records = [r for r in filtered_records if r.get('_parsed_metadata', {}).get('lab_id') == most_common]
                    logger.info(f"Refined dataset to most common lab_id ({most_common}). New count: {len(final_records)}")

        # 4. Write
        write_clean_data(final_records, output_path)

        # 5. Checksum
        logger.info("Invoking checksum utility...")
        scan_and_register_data_files()

        # Report
        pass_rate = (len(final_records) / len(raw_records)) * 100 if raw_records else 0
        logger.info(f"Preprocessing complete. Pass rate: {pass_rate:.2f}%")
        logger.info(f"Output written to: {output_path}")

    except FileNotFoundError as e:
        logger.error(f"Critical error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during preprocessing: {e}")
        raise

if __name__ == '__main__':
    main()
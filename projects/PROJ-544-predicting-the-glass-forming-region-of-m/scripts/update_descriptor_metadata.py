"""
Script to update descriptor_vector.csv with the experimental_validation_status field.

This script reads the existing descriptor vector output, determines the validation status
based on available source metadata (defaulting to 'unknown' if XRD data is missing),
and writes the updated CSV to the derived directory.

It ensures compliance with the updated descriptor_vector.schema.json contract.
"""
import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/descriptor_update.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

DEFAULT_STATUS = "unknown"

def load_source_metadata(source_file: Path) -> dict:
    """
    Loads source metadata if available to determine validation status.
    In a real pipeline, this might query a database or read a manifest.
    For now, it checks for a specific marker in the sample_id or a sidecar file.
    """
    metadata = {}
    if not source_file.exists():
        logger.warning(f"Source metadata file not found at {source_file}. Defaulting to 'unknown'.")
        return metadata

    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            # Assuming a JSON format where keys are sample_ids
            metadata = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to parse source metadata: {e}")
    
    return metadata

def determine_status(sample_id: str, metadata: dict) -> str:
    """
    Determines the experimental_validation_status for a given sample_id.
    
    Logic:
    1. Check metadata for explicit 'validated' flag.
    2. Check if sample_id contains 'xrd' or 'validated' (heuristic for legacy data).
    3. Default to 'unknown'.
    """
    if sample_id in metadata:
        entry = metadata[sample_id]
        if isinstance(entry, dict):
            if entry.get('validated') is True:
                return 'yes'
            if entry.get('validated') is False:
                return 'no'
        
        # Check for string flags
        val_status = entry if isinstance(entry, str) else entry.get('status')
        if val_status in ['yes', 'no']:
            return val_status

    # Heuristic check on ID (optional, for backward compatibility with raw data naming)
    if 'xrd' in sample_id.lower() or 'validated' in sample_id.lower():
        return 'yes'
    
    return DEFAULT_STATUS

def update_descriptor_csv(input_path: Path, output_path: Path, metadata: dict):
    """
    Reads the input CSV, adds/updates the experimental_validation_status column,
    and writes to the output path.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input descriptor file not found: {input_path}")

    logger.info(f"Reading input file: {input_path}")
    
    rows = []
    fieldnames = None
    
    with open(input_path, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        
        if not fieldnames:
            raise ValueError("Input CSV has no headers.")

        # Ensure the new field is in the output headers
        if 'experimental_validation_status' not in fieldnames:
            fieldnames = list(fieldnames) + ['experimental_validation_status']

        for row in reader:
            sample_id = row.get('sample_id', 'UNKNOWN')
            status = determine_status(sample_id, metadata)
            row['experimental_validation_status'] = status
            rows.append(row)

    logger.info(f"Writing updated file: {output_path} with {len(rows)} rows.")
    
    with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def main():
    parser = argparse.ArgumentParser(
        description="Update descriptor_vector.csv with experimental_validation_status."
    )
    parser.add_argument(
        '--input', '-i',
        type=Path,
        default=Path('data/derived/descriptor_vector.csv'),
        help="Path to the input descriptor CSV."
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path('data/derived/descriptor_vector.csv'),
        help="Path to the output descriptor CSV (overwrites input if same)."
    )
    parser.add_argument(
        '--metadata', '-m',
        type=Path,
        default=Path('data/samples/source_metadata.json'),
        help="Path to JSON file containing validation status per sample_id."
    )

    args = parser.parse_args()

    # Load metadata
    metadata = load_source_metadata(args.metadata)

    try:
        update_descriptor_csv(args.input, args.output, metadata)
        logger.info("Successfully updated descriptor vector with validation status.")
    except Exception as e:
        logger.error(f"Failed to update descriptor vector: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
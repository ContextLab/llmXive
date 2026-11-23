"""
Kappa Ingestor Service (T057)

Implements ingestion of researcher-provided independent thermal conductivity (κ) values.
Validates independence against trajectory sources to prevent circular dependencies.
"""
import os
import sys
import csv
import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

from src.lib.config import get_config

# Constants
VALID_SOURCE_TYPES = {'experimental', 'distinct_simulation', 'literature'}
SOURCE_ID_REGEX = re.compile(r'^[a-z0-9_]+$')
EXIT_CODE_CIRCULAR_DEPENDENCY = 2
EXIT_CODE_INVALID_INPUT = 1
EXIT_CODE_SUCCESS = 0

# Logger setup
def setup_service_logger(name: str = "kappa_ingester") -> logging.Logger:
    """Setup service-specific logger."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    console_fmt = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(console_fmt)
    logger.addHandler(ch)

    # File handler
    config = get_config()
    log_dir = config.get_path("data_metadata")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "kappa_ingester.log"

    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(message)s')
    fh.setFormatter(file_fmt)
    logger.addHandler(fh)

    return logger

logger = setup_service_logger()

def load_trajectory_ids() -> Dict[str, Any]:
    """
    Load trajectory IDs from data/metadata/trajectory_ids.json.
    Must exist as per T056 dependency.
    """
    config = get_config()
    traj_path = config.get_path("data_metadata") / "trajectory_ids.json"

    if not traj_path.exists():
        logger.error(f"FATAL: Required file missing: {traj_path}")
        sys.exit(EXIT_CODE_INVALID_INPUT)

    try:
        with open(traj_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded trajectory IDs from {traj_path}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"FATAL: Invalid JSON in trajectory_ids.json: {e}")
        sys.exit(EXIT_CODE_INVALID_INPUT)

def load_valid_sources() -> Set[str]:
    """
    Load valid source IDs from data/metadata/valid_sources.json.
    Must exist as per T055b dependency.
    """
    config = get_config()
    valid_sources_path = config.get_path("data_metadata") / "valid_sources.json"

    if not valid_sources_path.exists():
        logger.error(f"FATAL: Required file missing: {valid_sources_path}")
        sys.exit(EXIT_CODE_INVALID_INPUT)

    try:
        with open(valid_sources_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Expecting a list of IDs or a dict with an 'ids' key
        if isinstance(data, list):
            valid_ids = set(data)
        elif isinstance(data, dict) and 'ids' in data:
            valid_ids = set(data['ids'])
        else:
            logger.error(f"FATAL: Invalid structure in valid_sources.json: {data}")
            sys.exit(EXIT_CODE_INVALID_INPUT)

        logger.info(f"Loaded {len(valid_ids)} valid source IDs")
        return valid_ids
    except json.JSONDecodeError as e:
        logger.error(f"FATAL: Invalid JSON in valid_sources.json: {e}")
        sys.exit(EXIT_CODE_INVALID_INPUT)

def validate_kappa_entry(
    row: Dict[str, str],
    valid_sources: Set[str],
    trajectory_ids: Dict[str, Any]
) -> Optional[str]:
    """
    Validate a single row of the kappa CSV.
    Returns an error message if invalid, None if valid.
    """
    required_cols = ['system_size', 'kappa', 'source_id', 'source_type', 'trajectory_id']
    for col in required_cols:
        if col not in row or not row[col]:
            return f"Missing or empty required column: {col}"

    # Validate source_id format
    source_id = row['source_id'].strip().lower()
    if not SOURCE_ID_REGEX.match(source_id):
        return f"Invalid source_id format: '{row['source_id']}'. Must match {SOURCE_ID_REGEX.pattern}"

    # Validate source_id is in valid_sources
    if source_id not in valid_sources:
        return f"source_id '{source_id}' not found in valid_sources.json"

    # Validate source_type
    source_type = row['source_type'].strip().lower()
    if source_type not in VALID_SOURCE_TYPES:
        return f"Invalid source_type: '{source_type}'. Must be one of {VALID_SOURCE_TYPES}"

    # Validate system_size is integer
    try:
        int(row['system_size'])
    except ValueError:
        return f"system_size must be an integer: '{row['system_size']}'"

    # Validate kappa is float
    try:
        float(row['kappa'])
    except ValueError:
        return f"kappa must be a float: '{row['kappa']}'"

    return None

def check_circular_dependency(
    kappa_source_ids: Set[str],
    trajectory_source: str
) -> bool:
    """
    Check if any kappa source_id matches the trajectory_source.
    Returns True if circular dependency detected (failure).
    """
    if trajectory_source in kappa_source_ids:
        logger.error(f"FATAL: Circular Dependency Detected. source_id '{trajectory_source}' matches trajectory source.")
        return True
    return False

def ingest_kappa_values(
    input_path: Path,
    valid_sources: Set[str],
    trajectory_ids: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Read, validate, and filter the input CSV.
    Raises SystemExit on fatal errors.
    """
    if not input_path.exists():
        logger.error(f"FATAL: Input file not found: {input_path}")
        sys.exit(EXIT_CODE_INVALID_INPUT)

    logger.info(f"Reading kappa values from {input_path}")

    valid_entries = []
    kappa_source_ids = set()

    try:
        with open(input_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader, start=1):
                error = validate_kappa_entry(row, valid_sources, trajectory_ids)
                if error:
                    logger.error(f"Row {row_num} validation failed: {error}")
                    # Continue to next row? Spec says "HALT with fatal error" if file is invalid.
                    # Interpret as: if ANY row is invalid, halt.
                    sys.exit(EXIT_CODE_INVALID_INPUT)

                entry = {
                    'system_size': int(row['system_size']),
                    'kappa': float(row['kappa']),
                    'source_id': row['source_id'].strip().lower(),
                    'source_type': row['source_type'].strip().lower(),
                    'trajectory_id': row['trajectory_id']
                }
                valid_entries.append(entry)
                kappa_source_ids.add(entry['source_id'])

    except csv.Error as e:
        logger.error(f"FATAL: CSV parsing error: {e}")
        sys.exit(EXIT_CODE_INVALID_INPUT)

    if not valid_entries:
        logger.error("FATAL: No valid entries found in input file.")
        sys.exit(EXIT_CODE_INVALID_INPUT)

    # Extract trajectory_source from trajectory_ids
    # Assuming trajectory_ids is a dict mapping size to source info, or a list.
    # T056 output format: usually a list of dicts or a mapping.
    # We need the 'trajectory_source' field from the metadata generated by T056.
    # Let's assume the structure from T056: `data/metadata/trajectory_ids.json`
    # contains a list of objects, each with 'trajectory_id' and 'trajectory_source'.
    # We need the source_id of the fetched data.
    
    # If trajectory_ids is a list of dicts:
    if isinstance(trajectory_ids, list):
        # Collect all sources from the fetched data
        fetched_sources = {item.get('trajectory_source') for item in trajectory_ids if item.get('trajectory_source')}
        trajectory_source = list(fetched_sources)[0] if len(fetched_sources) == 1 else None
        
        # If multiple sources, we check if ANY kappa source matches ANY fetched source?
        # The spec says: "compare it against trajectory_source".
        # If there are multiple realizations, they might have different sources or the same.
        # Usually, the dataset comes from one source. Let's assume one main source.
        # If multiple, we should check against all to be safe?
        # Spec: "If source_id == trajectory_source". Singular.
        # Let's assume the fetched data shares a common source_id or we check intersection.
        
        # If the fetched data has multiple distinct sources, and a kappa entry matches ANY of them, it's circular.
        if fetched_sources:
            if kappa_source_ids & fetched_sources:
                logger.error(f"FATAL: Circular Dependency Detected. kappa sources {kappa_source_ids & fetched_sources} match fetched data sources.")
                sys.exit(EXIT_CODE_CIRCULAR_DEPENDENCY)
    elif isinstance(trajectory_ids, dict):
        # If it's a dict, maybe keys are sizes, values are metadata
        # Check all values for 'trajectory_source'
        fetched_sources = set()
        for v in trajectory_ids.values():
            if isinstance(v, dict) and 'trajectory_source' in v:
                fetched_sources.add(v['trajectory_source'])
        
        if fetched_sources:
            if kappa_source_ids & fetched_sources:
                logger.error(f"FATAL: Circular Dependency Detected. kappa sources {kappa_source_ids & fetched_sources} match fetched data sources.")
                sys.exit(EXIT_CODE_CIRCULAR_DEPENDENCY)
    else:
        logger.warning("Unexpected trajectory_ids format, skipping circular dependency check.")

    logger.info(f"Successfully validated {len(valid_entries)} kappa entries.")
    return valid_entries

def write_output(entries: List[Dict[str, Any]], output_path: Path) -> None:
    """Write validated entries to the output CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ['system_size', 'kappa', 'source_id', 'source_type', 'trajectory_id']
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(entries)

    logger.info(f"Output written to {output_path}")

def main() -> int:
    """Main entry point for the kappa ingester."""
    import argparse

    parser = argparse.ArgumentParser(description="Ingest researcher-provided kappa values.")
    parser.add_argument(
        '--kappa-file',
        type=str,
        default=None,
        help="Path to input CSV with kappa values."
    )
    args = parser.parse_args()

    config = get_config()
    
    # Determine input path
    if args.kappa_file:
        input_path = Path(args.kappa_file)
    else:
        # Fallback to default path
        input_path = config.get_path("data_derived_reference") / "kappa_values.csv"

    # Load dependencies
    trajectory_ids = load_trajectory_ids()
    valid_sources = load_valid_sources()

    # Ingest and validate
    try:
        valid_entries = ingest_kappa_values(input_path, valid_sources, trajectory_ids)
    except SystemExit:
        return EXIT_CODE_INVALID_INPUT

    # Write output
    output_path = config.get_path("data_derived_reference") / "kappa_values.csv"
    write_output(valid_entries, output_path)

    return EXIT_CODE_SUCCESS

if __name__ == "__main__":
    sys.exit(main())

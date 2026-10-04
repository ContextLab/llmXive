"""
Kappa Ingestion Service

Ingests researcher-provided independent thermal conductivity (κ) values.
Validates against trajectory metadata to ensure statistical independence.
"""
import os
import sys
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.lib.config import get_config, setup_logger

# Constants
TRAJECTORY_IDS_PATH = PROJECT_ROOT / "data" / "metadata" / "trajectory_ids.json"
DEFAULT_KAPA_INPUT = PROJECT_ROOT / "data" / "derived" / "reference" / "kappa_values.csv"
OUTPUT_KAPA_PATH = PROJECT_ROOT / "data" / "derived" / "reference" / "kappa_values.csv"
REQUIRED_COLUMNS = {"system_size", "kappa", "source_id", "trajectory_id"}

def setup_service_logger(name: str = "kappa_ingester") -> logging.Logger:
    """Setup logger for the kappa ingestion service."""
    return setup_logger(name)

def load_trajectory_ids(logger: logging.Logger) -> Dict[str, Any]:
    """
    Load the verified trajectory IDs from the metadata file.
    
    Raises:
        FileNotFoundError: If the trajectory_ids.json file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not TRAJECTORY_IDS_PATH.exists():
        logger.error(f"Trajectory IDs file not found: {TRAJECTORY_IDS_PATH}")
        logger.error("T056 (Data Loader) must be executed successfully before T057.")
        raise FileNotFoundError(f"Missing dependency: {TRAJECTORY_IDS_PATH}")

    try:
        with open(TRAJECTORY_IDS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded {len(data.get('trajectory_ids', []))} trajectory IDs.")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in trajectory IDs file: {e}")
        raise

def validate_kappa_entry(
    row: Dict[str, str], 
    valid_trajectory_ids: set, 
    logger: logging.Logger
) -> bool:
    """
    Validate a single row of kappa data.
    
    Checks:
    1. Required columns present and non-empty.
    2. Trajectory ID exists in the verified metadata.
    3. Source ID is distinct from topology extraction source (basic check).
    4. Kappa value is a valid float.
    5. System size is a valid integer.
    
    Returns:
        bool: True if valid, False otherwise.
    """
    # Check required columns
    missing_cols = REQUIRED_COLUMNS - set(row.keys())
    if missing_cols:
        logger.error(f"Row missing required columns: {missing_cols}. Row: {row}")
        return False

    # Check empty values
    for col in REQUIRED_COLUMNS:
        if not row[col].strip():
            logger.error(f"Row has empty value for required column '{col}': {row}")
            return False

    # Validate Trajectory ID
    traj_id = row["trajectory_id"].strip()
    if traj_id not in valid_trajectory_ids:
        logger.error(
            f"Trajectory ID '{traj_id}' not found in verified metadata. "
            f"Ensure T056 has run and extracted this ID. Row: {row}"
        )
        return False

    # Validate Kappa value
    try:
        kappa_val = float(row["kappa"])
        if kappa_val <= 0:
            logger.error(f"Kappa value must be positive: {kappa_val}. Row: {row}")
            return False
    except ValueError:
        logger.error(f"Invalid kappa value (not a float): '{row['kappa']}'. Row: {row}")
        return False

    # Validate System Size
    try:
        sys_size = int(row["system_size"])
        if sys_size <= 0:
            logger.error(f"System size must be positive: {sys_size}. Row: {row}")
            return False
    except ValueError:
        logger.error(f"Invalid system size (not an int): '{row['system_size']}'. Row: {row}")
        return False

    # Basic Source ID check (ensure it's not 'internal_topology_extraction')
    source_id = row["source_id"].strip()
    if source_id.lower() == "internal_topology_extraction":
        logger.error(
            f"Source ID 'internal_topology_extraction' is reserved. "
            f"κ values must be from independent external sources. Row: {row}"
        )
        return False

    return True

def ingest_kappa_values(
    input_path: Optional[Path] = None,
    logger: Optional[logging.Logger] = None
) -> List[Dict[str, Any]]:
    """
    Ingest and validate kappa values from a CSV file.
    
    Args:
        input_path: Path to the input CSV. Defaults to DEFAULT_KAPA_INPUT.
        logger: Logger instance.
        
    Returns:
        List of validated dictionaries.
        
    Raises:
        FileNotFoundError: If input file missing.
        ValueError: If validation fails for any row or file structure is invalid.
    """
    if logger is None:
        logger = setup_service_logger()

    if input_path is None:
        input_path = DEFAULT_KAPA_INPUT

    if not input_path.exists():
        logger.error(f"Input κ file not found: {input_path}")
        logger.error("Please provide a valid file via --kappa-file or place it at the default location.")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Load verified trajectory IDs
    trajectory_data = load_trajectory_ids(logger)
    valid_traj_ids = set(trajectory_data.get("trajectory_ids", []))

    if not valid_traj_ids:
        logger.error("No valid trajectory IDs found in metadata. T056 must run first.")
        raise ValueError("No trajectory IDs available for validation.")

    validated_rows = []
    
    try:
        with open(input_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            
            # Check header
            if reader.fieldnames is None:
                logger.error("CSV file is empty or has no header.")
                raise ValueError("CSV file is empty.")
            
            header_set = set(reader.fieldnames)
            if not REQUIRED_COLUMNS.issubset(header_set):
                missing = REQUIRED_COLUMNS - header_set
                logger.error(f"CSV header missing required columns: {missing}")
                raise ValueError(f"Invalid CSV schema. Missing: {missing}")

            row_count = 0
            for row in reader:
                row_count += 1
                if validate_kappa_entry(row, valid_traj_ids, logger):
                    # Convert types for storage
                    validated_rows.append({
                        "system_size": int(row["system_size"]),
                        "kappa": float(row["kappa"]),
                        "source_id": row["source_id"].strip(),
                        "trajectory_id": row["trajectory_id"].strip()
                    })
                else:
                    logger.warning(f"Skipping invalid row {row_count}: {row}")

            if row_count == 0:
                logger.error("No data rows found in input file.")
                raise ValueError("Input file contains no data rows.")

    except csv.Error as e:
        logger.error(f"CSV parsing error: {e}")
        raise

    if not validated_rows:
        logger.error("No valid rows found in input file after validation.")
        raise ValueError("Validation failed for all rows in input file.")

    logger.info(f"Successfully validated {len(validated_rows)} κ entries.")
    return validated_rows

def write_output(
    validated_rows: List[Dict[str, Any]], 
    output_path: Path,
    logger: logging.Logger
) -> None:
    """Write validated kappa values to the output CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["system_size", "kappa", "source_id", "trajectory_id"])
        writer.writeheader()
        writer.writerows(validated_rows)
    
    logger.info(f"Validated κ values written to: {output_path}")

def main() -> int:
    """Main entry point for the kappa ingester."""
    logger = setup_service_logger()
    logger.info("Starting Kappa Ingestion Service (T057)...")

    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description="Ingest researcher-provided independent κ values.")
    parser.add_argument(
        "--kappa-file", 
        type=str, 
        default=None,
        help="Path to the input CSV file containing κ values. "
             "Defaults to data/derived/reference/kappa_values.csv"
    )
    args = parser.parse_args()

    input_path = Path(args.kappa_file) if args.kappa_file else None

    try:
        # Ingest and validate
        validated_data = ingest_kappa_values(input_path=input_path, logger=logger)
        
        # Write output
        write_output(validated_data, OUTPUT_KAPA_PATH, logger)
        
        logger.info("Kappa ingestion completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.critical(f"Fatal Error: {e}")
        return 1
    except ValueError as e:
        logger.critical(f"Validation Error: {e}")
        return 1
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())

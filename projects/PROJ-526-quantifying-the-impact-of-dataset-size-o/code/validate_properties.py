"""
Validation logic to count distinct material properties and enforce the FR-001 constraint.

This module implements the hard constraint that at least 15 distinct properties
must be available in the processed dataset. If the count is less than 15, it raises
a critical ValueError and halts the pipeline immediately.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any

# Import logging configuration from existing utils
from utils.logging_config import setup_logging, get_logger
# Import config utilities
from config import get_config, require_state_dir

# Configure logging
logger = get_logger(__name__)

# Constants
MIN_PROPERTIES_REQUIRED = 15


def load_processed_data_path() -> Path:
    """
    Determine the path to the processed master dataset.
    
    Returns:
        Path: Path to materials_master.parquet or materials_master.csv
    """
    config = get_config()
    data_dir = Path(config.data_dir)
    processed_dir = data_dir / "processed"
    
    # Check for Parquet first (preferred)
    parquet_path = processed_dir / "materials_master.parquet"
    if parquet_path.exists():
        return parquet_path
    
    # Fallback to CSV if Parquet doesn't exist
    csv_path = processed_dir / "materials_master.csv"
    if csv_path.exists():
        return csv_path
    
    raise FileNotFoundError(
        f"Processed dataset not found. Expected either {parquet_path} or {csv_path}"
    )


def count_distinct_properties(data_path: Path) -> int:
    """
    Count the number of distinct material properties in the dataset.
    
    This function loads the processed dataset and counts the number of
    unique property columns (excluding metadata columns like 'material_id',
    'composition', etc.).
    
    Args:
        data_path: Path to the processed dataset (Parquet or CSV)
    
    Returns:
        int: Number of distinct properties found
    
    Raises:
        FileNotFoundError: If the data file doesn't exist
        ValueError: If the file format is not supported
    """
    import pandas as pd
    
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    logger.info(f"Loading dataset from {data_path}")
    
    # Load based on file extension
    if data_path.suffix == '.parquet':
        df = pd.read_parquet(data_path)
    elif data_path.suffix in ['.csv', '.tsv']:
        df = pd.read_csv(data_path)
    else:
        raise ValueError(f"Unsupported file format: {data_path.suffix}")
    
    logger.info(f"Dataset loaded with {len(df)} rows and {len(df.columns)} columns")
    
    # Define metadata columns to exclude from property count
    metadata_columns = {
        'material_id', 'materialIds', 'ids', 'composition', 'formula',
        'formula_pretty', 'elements', 'nsites', 'volume', 'density',
        'energy_per_atom', 'formation_energy_per_atom', 'band_gap',
        'structure', 'cif', 'json', 'metadata', 'source', 'timestamp'
    }
    
    # Identify property columns (columns not in metadata set)
    property_columns = [col for col in df.columns if col.lower() not in metadata_columns]
    
    property_count = len(property_columns)
    logger.info(f"Found {property_count} distinct properties: {property_columns}")
    
    return property_count


def update_properties_status(property_count: int, success: bool) -> None:
    """
    Update the properties status JSON file with the validation result.
    
    This function writes the validation result to state/properties_status.json
    ONLY if the count is sufficient (success=True). If validation fails,
    no status file is updated to prevent downstream tasks from proceeding.
    
    Args:
        property_count: The number of distinct properties found
        success: Whether the validation passed (count >= MIN_PROPERTIES_REQUIRED)
    """
    config = get_config()
    state_dir = Path(config.state_dir)
    
    # Ensure state directory exists
    state_dir.mkdir(parents=True, exist_ok=True)
    
    status_file = state_dir / "properties_status.json"
    
    status_data = {
        "validation_timestamp": str(pd.Timestamp.now()),
        "property_count": property_count,
        "minimum_required": MIN_PROPERTIES_REQUIRED,
        "validation_passed": success,
        "message": f"Validation {'PASSED' if success else 'FAILED'}: Found {property_count} properties (required: {MIN_PROPERTIES_REQUIRED})"
    }
    
    if success:
        with open(status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
        logger.info(f"Updated status file: {status_file}")
    else:
        logger.warning(f"Validation FAILED. Not updating {status_file}.")
        logger.warning(f"Gap: {MIN_PROPERTIES_REQUIRED - property_count} properties missing.")

def validate_property_count() -> bool:
    """
    Main validation function that enforces the FR-001 constraint.
    
    This function:
    1. Loads the processed dataset
    2. Counts distinct properties
    3. Raises ValueError if count < 15
    4. Updates status file only if count >= 15
    
    Returns:
        bool: True if validation passed (only reached if count >= 15)
    
    Raises:
        ValueError: If property count is less than 15 (critical failure)
        FileNotFoundError: If processed dataset not found
    """
    import pandas as pd  # Import here to avoid if not used warnings
    
    try:
        data_path = load_processed_data_path()
        property_count = count_distinct_properties(data_path)
        
        if property_count < MIN_PROPERTIES_REQUIRED:
            gap = MIN_PROPERTIES_REQUIRED - property_count
            error_msg = (
                f"CRITICAL: Property count ({property_count}) is below required minimum ({MIN_PROPERTIES_REQUIRED}). "
                f"Gap: {gap} properties. Pipeline halted per FR-001 constraint."
            )
            logger.error(error_msg)
            update_properties_status(property_count, success=False)
            raise ValueError(error_msg)
        
        # If we reach here, validation passed
        logger.info(f"Validation PASSED: {property_count} properties found (>= {MIN_PROPERTIES_REQUIRED})")
        update_properties_status(property_count, success=True)
        return True
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        raise


def main():
    """
    Entry point for the validation script.
    
    This function is called when the script is executed directly.
    It performs the property count validation and exits with appropriate
    exit codes.
    """
    setup_logging(level=logging.INFO)
    logger.info("Starting property count validation...")
    
    try:
        success = validate_property_count()
        if success:
            logger.info("Validation completed successfully. Pipeline can proceed to US2/US3.")
            sys.exit(0)
    except ValueError as e:
        logger.error(f"Validation failed: {e}")
        logger.error("Pipeline halted. Do not proceed to User Story 2 or 3.")
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"Data file error: {e}")
        logger.error("Cannot validate without processed dataset. Run US1 tasks first.")
        sys.exit(2)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()

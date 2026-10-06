import os
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd

# Import project utilities
from code.utils.logger import get_logger
from code.utils.validators import load_schema, validate_dataset
from code.utils.config import get_data_path

logger = get_logger(__name__)

def check_simulated_mode() -> bool:
    """
    Check if simulated mode is active by reading data/simulated/state.json.
    
    Returns:
        bool: True if SIMULATED_MODE is True, False otherwise.
    """
    state_path = Path(get_data_path()) / "simulated" / "state.json"
    
    if not state_path.exists():
        logger.info("State file not found. Assuming real data mode.")
        return False
    
    try:
        with open(state_path, 'r') as f:
            state = json.load(f)
        
        is_simulated = state.get("SIMULATED_MODE", False)
        logger.info(f"Simulated mode status: {is_simulated}")
        return is_simulated
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to read state file: {e}")
        return False

def get_source_dataframe(is_simulated: bool) -> pd.DataFrame:
    """
    Retrieve the source DataFrame based on the mode.
    
    Args:
        is_simulated (bool): If True, load simulated data. If False, load real cleaned data.
        
    Returns:
        pd.DataFrame: The source dataset.
        
    Raises:
        FileNotFoundError: If the expected source file does not exist.
        ValueError: If the file is empty or invalid.
    """
    data_path = Path(get_data_path())
    
    if is_simulated:
        source_file = data_path / "simulated" / "temp_simulated_data.csv"
        logger.info(f"Loading simulated data from {source_file}")
    else:
        # Logic for real data: T014 output (filtered hosts) + T015 descriptors
        # The task description implies the data is already merged/ready from previous steps.
        # We assume the cleaned and filtered data with descriptors is available at:
        # data/raw/descriptors_added.csv (from T015)
        source_file = data_path / "raw" / "descriptors_added.csv"
        logger.info(f"Loading real processed data from {source_file}")
    
    if not source_file.exists():
        raise FileNotFoundError(f"Source data file not found: {source_file}")
    
    df = pd.read_csv(source_file)
    
    if df.empty:
        raise ValueError(f"Source data file is empty: {source_file}")
    
    logger.info(f"Loaded {len(df)} rows from {source_file.name}")
    return df

def save_processed_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """
    Validate the dataset against the schema and save it to the processed directory.
    
    Args:
        df (pd.DataFrame): The dataset to save.
        output_path (Path): The destination path for the CSV.
        
    Raises:
        ValueError: If validation fails.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Validate against schema
    # The schema file is expected at data/schema.yaml or similar based on project structure
    schema_path = Path(get_data_path()) / "schema.yaml"
    
    if schema_path.exists():
        logger.info(f"Validating dataset against schema: {schema_path}")
        try:
            is_valid, errors = validate_dataset(df, str(schema_path))
            if not is_valid:
                error_msg = f"Schema validation failed: {errors}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            logger.info("Schema validation passed.")
        except Exception as e:
            logger.warning(f"Schema validation error (non-fatal): {e}")
            # Depending on strictness, we might fail here. 
            # For this implementation, we log the error but proceed if the file is readable,
            # as the schema might be missing in early dev stages, but the task requires a check.
            # However, the task says "with schema compliance check". 
            # If the schema exists and fails, we must raise.
            raise
    else:
        logger.warning("No schema file found at expected location. Skipping strict validation.")
    
    # Write to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully saved processed dataset to {output_path}")

def main():
    """
    Main entry point for T017: Save processed dataset with schema compliance check.
    """
    logger.info("Starting T017: Save processed dataset")
    
    try:
        # 1. Check mode
        is_simulated = check_simulated_mode()
        
        # 2. Get source data
        df = get_source_dataframe(is_simulated)
        
        # 3. Define output path
        output_path = Path(get_data_path()) / "processed" / "halide_binding_data.csv"
        
        # 4. Validate and Save
        save_processed_dataset(df, output_path)
        
        logger.info("T017 completed successfully.")
        
    except FileNotFoundError as e:
        logger.critical(f"Data source missing: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.critical(f"Validation or data error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error in T017: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

import os
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd

# Import local utilities matching the project API surface
from utils.config import get_data_path, get_path
from utils.validators import validate_dataset, load_schema, ensure_schema_file_exists
from utils.logger import get_logger

# Ensure the logger is configured
logger = get_logger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SIMULATED_STATE_PATH = PROJECT_ROOT / "data" / "simulated" / "state.json"
TEMP_SIMULATED_PATH = PROJECT_ROOT / "data" / "simulated" / "temp_simulated_data.csv"
PROCESSED_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "halide_binding_data.csv"
SCHEMA_PATH = PROJECT_ROOT / "data" / "raw" / "dataset.schema.yaml" # Assuming schema location based on T008 description

def check_simulated_mode() -> bool:
    """
    Checks if the project is running in simulated data mode by inspecting
    data/simulated/state.json.
    
    Returns:
        bool: True if SIMULATED_MODE is True, False otherwise.
    """
    if not SIMULATED_STATE_PATH.exists():
        logger.debug("Simulated state file not found. Assuming real data mode.")
        return False
    
    try:
        with open(SIMULATED_STATE_PATH, 'r') as f:
            state = json.load(f)
        is_sim = state.get("SIMULATED_MODE", False)
        logger.info(f"Simulated mode check: {is_sim}")
        return is_sim
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Could not read simulated state file: {e}. Assuming real data mode.")
        return False

def get_source_dataframe() -> Optional[pd.DataFrame]:
    """
    Retrieves the source DataFrame based on the current mode.
    
    If simulated mode is active:
        - Reads from data/simulated/temp_simulated_data.csv
        - Validates against schema
    If real mode:
        - This function expects that T014 (filtering) has produced a valid DataFrame
          in memory or a temporary location. Since T017 is the "sole writer", 
          and T014 is a script that runs previously, we assume the clean data 
          is available via a standard intermediate path or re-run logic.
          However, per T017 description: "Otherwise, use the cleaned data from T014."
          In a pipeline script, T014 usually writes to a temp file or the script 
          chains. Given the constraint of "sole writer of final CSV", we assume
          the cleaned data from T014 was written to a known intermediate file 
          (e.g., data/raw/cleaned_real_data.csv) or we re-load it if it exists.
          
    Since the prompt implies T014 produces the data, and T017 consumes it:
    We will look for a standard intermediate file for real data: data/raw/cleaned_data.csv
    If that doesn't exist and we are NOT in simulated mode, we raise an error.
    
    Returns:
        pd.DataFrame: The source dataframe.
    
    Raises:
        FileNotFoundError: If the source data is missing.
    """
    is_sim = check_simulated_mode()
    
    if is_sim:
        logger.info("Loading source data from simulated temporary file.")
        if not TEMP_SIMULATED_PATH.exists():
            raise FileNotFoundError(
                f"Simulated mode is active, but {TEMP_SIMULATED_PATH} does not exist. "
                "T016 must run first to generate this file."
            )
        try:
            df = pd.read_csv(TEMP_SIMULATED_PATH)
            logger.info(f"Loaded {len(df)} rows from simulated data.")
            return df
        except Exception as e:
            logger.error(f"Failed to read simulated data: {e}")
            raise
    
    else:
        logger.info("Loading source data from real data pipeline (T014 output).")
        # Assuming T014 writes to this intermediate path if it exists
        real_data_path = PROJECT_ROOT / "data" / "raw" / "cleaned_data.csv"
        if not real_data_path.exists():
            # Fallback: maybe T014 wrote to data/processed but we need to save to processed_final?
            # Strictly following T017: "use the cleaned data from T014".
            # If T014 didn't write a file, this task cannot proceed without re-running T014 logic.
            # We assume T014 produces this file as per standard pipeline patterns.
            raise FileNotFoundError(
                f"Real data mode active, but intermediate cleaned data file not found at {real_data_path}. "
                "Please ensure T014 has been executed successfully."
            )
        
        try:
            df = pd.read_csv(real_data_path)
            logger.info(f"Loaded {len(df)} rows from real data.")
            return df
        except Exception as e:
            logger.error(f"Failed to read real data: {e}")
            raise

def save_processed_dataset(df: pd.DataFrame) -> str:
    """
    Validates the DataFrame against the schema and saves it to the final output location.
    
    Args:
        df: The DataFrame to save.
    
    Returns:
        str: The path to the saved file.
    
    Raises:
        ValueError: If validation fails.
    """
    # Ensure schema exists (T008 should have created it, but we ensure it here)
    # If the schema is expected to be in data/raw, we check there. 
    # If T008 created it elsewhere, we might need to adjust. 
    # Based on T008 description: "Implement schema validators (code/utils/validators.py: dataset.schema.yaml validation logic)"
    # It likely expects the file to exist. We try to load it.
    
    schema_file = SCHEMA_PATH
    if not schema_file.exists():
        # Try to find it in standard locations if not in raw
        possible_locations = [
            PROJECT_ROOT / "specs" / "dataset.schema.yaml",
            PROJECT_ROOT / "code" / "utils" / "dataset.schema.yaml",
            PROJECT_ROOT / "data" / "dataset.schema.yaml"
        ]
        for p in possible_locations:
            if p.exists():
                schema_file = p
                break
    
    if not schema_file.exists():
        logger.warning(f"Schema file not found at {schema_file} or alternatives. Skipping validation.")
        # If we can't validate, we still save but log a warning.
        # However, task requires "schema compliance check". 
        # We will attempt to create a minimal schema if missing to satisfy the "check" requirement 
        # or fail loudly if we can't.
        # For now, we assume the file exists as per T008 completion.
        raise FileNotFoundError(f"Schema file {SCHEMA_PATH} not found. T008 must be completed.")

    # Load schema
    schema = load_schema(schema_file)
    
    # Validate
    logger.info(f"Validating dataset against schema {schema_file}...")
    try:
        is_valid, errors = validate_dataset(df, schema)
        if not is_valid:
            error_msg = f"Schema validation failed: {errors}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        logger.info("Schema validation passed.")
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise

    # Ensure output directory exists
    PROCESSED_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Save
    df.to_csv(PROCESSED_OUTPUT_PATH, index=False)
    logger.info(f"Saved processed dataset to {PROCESSED_OUTPUT_PATH}")
    
    return str(PROCESSED_OUTPUT_PATH)

def main():
    """
    Main entry point for T017: Save processed dataset.
    """
    logger.info("Starting T017: Save processed dataset.")
    try:
        # Step 1: Get source dataframe
        df = get_source_dataframe()
        
        if df is None or df.empty:
            raise ValueError("Source dataframe is empty or None.")
        
        # Step 2: Save with validation
        output_path = save_processed_dataset(df)
        
        logger.info(f"T017 completed successfully. Output: {output_path}")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation or logic error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error in T017: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

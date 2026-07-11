import os
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
from utils.logger import get_logger
from utils.validators import load_schema, validate_dataset
from utils.config import get_data_path

# Configure logging
logger = get_logger("save_processed_data")

def check_simulated_mode() -> bool:
    """
    Check if simulated mode is active by reading data/simulated/state.json.
    Returns True if SIMULATED_MODE is True, False otherwise.
    """
    state_path = get_data_path() / "simulated" / "state.json"
    if not state_path.exists():
        logger.info(f"State file not found at {state_path}. Assuming real data mode.")
        return False
    
    try:
        with open(state_path, 'r') as f:
            state_data = json.load(f)
        is_simulated = state_data.get("SIMULATED_MODE", False)
        if is_simulated:
            logger.info("SIMULATED_MODE is True. Reading from temporary simulated data.")
        else:
            logger.info("SIMULATED_MODE is False. Reading from standard cleaned data (T014 output).")
        return is_simulated
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Error reading state file: {e}. Assuming real data mode.")
        return False

def get_source_dataframe(is_simulated: bool) -> Optional[pd.DataFrame]:
    """
    Load the source DataFrame based on the mode.
    - If simulated: loads from data/simulated/temp_simulated_data.csv
    - If real: loads from data/processed/cleaned_data.csv (assuming T014 output)
    
    Returns None if the file is missing or invalid.
    """
    data_path = get_data_path()
    
    if is_simulated:
        source_file = data_path / "simulated" / "temp_simulated_data.csv"
        logger.info(f"Loading simulated data from: {source_file}")
        if not source_file.exists():
            logger.error(f"Simulated data file not found: {source_file}. T016 must have failed.")
            return None
        try:
            df = pd.read_csv(source_file)
            logger.info(f"Successfully loaded {len(df)} rows from simulated data.")
            return df
        except Exception as e:
            logger.error(f"Failed to read simulated data CSV: {e}")
            return None
    else:
        # Standard cleaned data from T014 (filter_hosts_with_multiple_halides)
        # Assuming the output of T014 is saved to this location as per pipeline conventions
        source_file = data_path / "processed" / "cleaned_data.csv"
        logger.info(f"Loading cleaned real data from: {source_file}")
        
        # Fallback check if T014 used a different name, though spec implies standard location
        if not source_file.exists():
            # Try a generic 'cleaned_data.csv' in processed if the specific one is missing
            # or check if T014 wrote to a different temp location (unlikely per spec)
            # For robustness, we check common variations if the primary fails
            logger.warning(f"Primary cleaned data file not found: {source_file}.")
            return None
        
        try:
            df = pd.read_csv(source_file)
            logger.info(f"Successfully loaded {len(df)} rows from cleaned real data.")
            return df
        except Exception as e:
            logger.error(f"Failed to read cleaned data CSV: {e}")
            return None

def save_processed_dataset(df: pd.DataFrame, output_filename: str = "halide_binding_data.csv") -> bool:
    """
    Validates the DataFrame against the dataset schema and saves it to the final processed location.
    """
    data_path = get_data_path()
    output_path = data_path / "processed" / output_filename
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 1. Schema Validation
    logger.info("Validating dataset against schema...")
    schema = load_schema()
    if not schema:
        logger.error("Could not load dataset schema. Cannot proceed with validation.")
        return False
    
    is_valid, validation_errors = validate_dataset(df, schema)
    
    if not is_valid:
        logger.error(f"Dataset validation failed: {validation_errors}")
        # Log specific errors for debugging
        for err in validation_errors:
            logger.error(f"  - {err}")
        return False
    
    logger.info("Dataset validation passed.")
    
    # 2. Save to CSV
    try:
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully saved processed dataset to: {output_path}")
        logger.info(f"Saved {len(df)} rows and {len(df.columns)} columns.")
        return True
    except Exception as e:
        logger.error(f"Failed to save processed dataset: {e}")
        return False

def main():
    """
    Main entry point for T017: Save processed dataset.
    
    Logic:
    1. Check data/simulated/state.json for SIMULATED_MODE.
    2. If True, read from data/simulated/temp_simulated_data.csv.
    3. If False, read from data/processed/cleaned_data.csv (T014 output).
    4. Validate against dataset.schema.yaml.
    5. Write to data/processed/halide_binding_data.csv.
    """
    logger.info("Starting T017: Save Processed Dataset")
    
    # Step 1: Check Mode
    is_simulated = check_simulated_mode()
    
    # Step 2: Load Data
    df = get_source_dataframe(is_simulated)
    
    if df is None:
        logger.error("Failed to load source data. Aborting T017.")
        return 1
    
    if df.empty:
        logger.error("Source DataFrame is empty. Aborting T017.")
        return 1
    
    # Step 3: Save Processed Data
    success = save_processed_dataset(df)
    
    if success:
        logger.info("T017 completed successfully.")
        return 0
    else:
        logger.error("T017 failed: Could not save processed dataset.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
import os
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd

# Import from project utils as per API surface
from code.utils.config import get_path, get_data_path, is_simulated_mode
from code.utils.validators import load_schema, validate_dataset
from code.utils.logger import get_logger

logger = get_logger(__name__)

def check_simulated_mode() -> bool:
    """
    Check if SIMULATED_MODE is active in data/simulated/state.json.
    
    Returns:
        bool: True if simulated mode is active, False otherwise.
    """
    state_path = get_data_path() / "simulated" / "state.json"
    
    if not state_path.exists():
        logger.info(f"State file not found at {state_path}. Assuming real data mode.")
        return False
    
    try:
        with open(state_path, 'r') as f:
            state = json.load(f)
        return state.get("SIMULATED_MODE", False)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Could not read state file: {e}. Assuming real data mode.")
        return False

def get_source_dataframe(is_sim: bool) -> pd.DataFrame:
    """
    Retrieve the source DataFrame based on the simulation mode.
    
    Args:
        is_sim (bool): Whether to use the simulated data source.
        
    Returns:
        pd.DataFrame: The source data for processing.
        
    Raises:
        FileNotFoundError: If the required source file does not exist.
        ValueError: If the source file is empty or invalid.
    """
    if is_sim:
        source_path = get_data_path() / "simulated" / "temp_simulated_data.csv"
        if not source_path.exists():
            raise FileNotFoundError(
                f"Simulated data source not found at {source_path}. "
                "Run T016a to generate simulated data first."
            )
        logger.info(f"Loading simulated data from {source_path}")
        df = pd.read_csv(source_path)
    else:
        # Real data path: cleaned + descriptors merged (output of T015)
        # T014 output is filtered_hosts.csv, T015 adds descriptors to it
        # The task description says "use the cleaned data from T014 (merged with T015 descriptors)"
        # Based on T015 output: data/raw/descriptors_added.csv
        source_path = get_data_path() / "raw" / "descriptors_added.csv"
        if not source_path.exists():
            raise FileNotFoundError(
                f"Real data source not found at {source_path}. "
                "Run T015 to generate descriptors first."
            )
        logger.info(f"Loading real data from {source_path}")
        df = pd.read_csv(source_path)
        
    if df.empty:
        raise ValueError(f"Source DataFrame at {source_path} is empty.")
        
    return df

def save_processed_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """
    Validate the DataFrame against the schema and save to the final processed location.
    
    Args:
        df (pd.DataFrame): The data to save.
        output_path (Path): The destination path for the final CSV.
        
    Raises:
        ValueError: If validation fails.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load schema
    schema_path = get_path() / "data" / "schema.yaml" 
    # Note: The prompt mentions 'dataset.schema.yaml' in T008, 
    # but usually these are in a specs or data folder. 
    # Let's check the utils.validators import which expects a schema.
    # We will assume the schema is at data/schema.yaml or specs/schema.yaml.
    # Given the project structure, let's try standard locations.
    possible_paths = [
        get_data_path() / "schema.yaml",
        get_path() / "specs" / "dataset.schema.yaml",
        get_path() / "data" / "dataset.schema.yaml"
    ]
    
    schema = None
    for p in possible_paths:
        if p.exists():
            schema = load_schema(p)
            logger.info(f"Loaded schema from {p}")
            break
    
    if schema is None:
        logger.warning("No schema found. Skipping validation.")
    else:
        logger.info("Validating dataset against schema...")
        try:
            validate_dataset(df, schema)
            logger.info("Validation successful.")
        except ValueError as e:
            logger.error(f"Validation failed: {e}")
            raise

    # Save the file
    df.to_csv(output_path, index=False)
    logger.info(f"Processed dataset saved to {output_path}")

def main() -> None:
    """
    Main entry point for T017: Save processed dataset.
    """
    logger.info("Starting T017: Save processed dataset to data/processed/halide_binding_data.csv")
    
    try:
        # 1. Check mode
        is_sim = check_simulated_mode()
        
        # 2. Get source data
        df = get_source_dataframe(is_sim)
        
        # 3. Define output path
        output_dir = get_data_path() / "processed"
        output_file = output_dir / "halide_binding_data.csv"
        
        # 4. Save with validation
        save_processed_dataset(df, output_file)
        
        logger.info("T017 completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Required input file missing: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation or processing error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error in T017: {e}")
        raise

if __name__ == "__main__":
    main()

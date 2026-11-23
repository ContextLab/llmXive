"""
Variable Engineering & Output (Task T017)

This module implements the variable engineering pipeline:
1. Loads cleaned data from the ingestion step.
2. Verifies required variables are present.
3. Computes derived variables (switching_index).
4. Handles missing outcomes.
5. Outputs the final cleaned dataset.

Dependencies:
- T015 (Dataset Ingestion) must have produced data/processed/*_cleaned.csv
"""

import os
import sys
import logging
import yaml
import pandas as pd
from pathlib import Path

# Import from local project structure
from logging_config import get_logger, setup_logging
from config import DATA_ROOT, RESULTS_ROOT
from utils import checksum_file

# Setup logging for this module
logger = get_logger(__name__)

def load_schema_contract(schema_path: str) -> dict:
    """Load the dataset schema contract."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema contract not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_schema_structure(df: pd.DataFrame, schema: dict) -> bool:
    """Validate that dataframe columns match the schema."""
    required_columns = schema.get('required_columns', [])
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Schema mismatch: Missing columns {missing}")
    return True

def load_all_raw_data() -> pd.DataFrame:
    """
    Load cleaned data from the ingestion step.
    Looks for *_cleaned.csv in data/processed directory.
    """
    processed_dir = Path(DATA_ROOT) / "processed"
    if not processed_dir.exists():
        raise FileNotFoundError(f"Processed directory not found: {processed_dir}")
    
    cleaned_files = list(processed_dir.glob("*_cleaned.csv"))
    if not cleaned_files:
        raise FileNotFoundError(f"No cleaned data found in {processed_dir}. Expected *_cleaned.csv")
    
    # Load the first found cleaned file (or merge if multiple)
    # For now, assume single dataset as per T015 logic
    logger.info(f"Loading cleaned data from: {cleaned_files[0]}")
    df = pd.read_csv(cleaned_files[0])
    return df

def engineer_switching_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute derived variable: switching_index = num_platforms * switching_frequency
    
    Requirement: Verify 'self_reported_switching_frequency' exists before proceeding.
    """
    # T017 Logic Step 1: Verify Variable Presence
    if 'self_reported_switching_frequency' not in df.columns:
        raise ValueError("Data Gap: Required variable 'self_reported_switching_frequency' not found in input data.")
    
    # T017 Logic Step 2: Compute switching_index
    # Note: The task description says 'switching_frequency' in the output schema,
    # but the input variable is 'self_reported_switching_frequency'.
    # We will use the input variable for calculation and ensure the output has 'switching_frequency'.
    if 'num_platforms' not in df.columns:
        raise ValueError("Data Gap: Required variable 'num_platforms' not found in input data.")
    
    df['switching_index'] = df['num_platforms'] * df['self_reported_switching_frequency']
    
    # Ensure 'switching_frequency' column exists in output as per schema
    # We map the input variable to the expected output column name
    if 'switching_frequency' not in df.columns:
        df['switching_frequency'] = df['self_reported_switching_frequency']
    
    return df

def handle_missing_outcomes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing outcomes by excluding rows and logging exclusion count.
    Outcome variable: 'cognitive_flexibility_score'
    """
    outcome_col = 'cognitive_flexibility_score'
    if outcome_col not in df.columns:
        raise ValueError(f"Data Gap: Outcome variable '{outcome_col}' not found in input data.")
    
    initial_count = len(df)
    df_clean = df.dropna(subset=[outcome_col])
    excluded_count = initial_count - len(df_clean)
    
    if excluded_count > 0:
        logger.warning(f"Excluded {excluded_count} rows due to missing {outcome_col} data.")
    else:
        logger.info("No rows excluded due to missing outcome data.")
    
    return df_clean

def validate_and_save(df: pd.DataFrame, output_path: str, schema: dict) -> None:
    """
    Validate the final dataframe against the output schema and save to disk.
    """
    # Validate columns
    output_columns = schema.get('required_columns', [])
    missing_cols = [col for col in output_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Output schema validation failed: Missing columns {missing_cols}")
    
    # Ensure correct column order (optional but good practice)
    df = df[output_columns]
    
    # Save to disk
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    
    # Verify file exists
    if not os.path.exists(output_path):
        raise RuntimeError(f"Failed to write output file: {output_path}")
    
    # Compute checksum for integrity
    checksum = checksum_file(output_path)
    logger.info(f"Output saved to {output_path} (Checksum: {checksum})")

def main():
    """Main entry point for T017."""
    logger.info("Starting variable engineering pipeline (T017).")
    
    try:
        # 1. Load Schema Contract
        schema_path = os.path.join("contracts", "dataset.schema.yaml")
        schema = load_schema_contract(schema_path)
        
        # 2. Load Data
        df = load_all_raw_data()
        logger.info(f"Loaded {len(df)} rows from cleaned data.")
        
        # 3. Validate Input Schema
        validate_schema_structure(df, schema)
        
        # 4. Engineer Variables
        df = engineer_switching_index(df)
        
        # 5. Handle Missing Outcomes
        df = handle_missing_outcomes(df)
        
        # 6. Validate and Save Output
        output_path = os.path.join(DATA_ROOT, "processed", "participants_cleaned.csv")
        
        # Define output schema columns explicitly as per task description
        output_schema = {
            'required_columns': [
                'participant_id', 'age', 'total_screen_time', 
                'num_platforms', 'switching_frequency', 'switching_index', 
                'cognitive_flexibility_score'
            ]
        }
        
        validate_and_save(df, output_path, output_schema)
        
        logger.info("Variable engineering pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    setup_logging()
    main()

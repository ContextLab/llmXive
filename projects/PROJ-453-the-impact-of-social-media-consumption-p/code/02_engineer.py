import os
import sys
import logging
import yaml
from pathlib import Path
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np

from logging_config import setup_logging, get_logger
from config import DATA_ROOT, RESULTS_ROOT

# Setup logging
logger = get_logger("engineer")

def load_schema_contract(schema_path: Path) -> Dict[str, Any]:
    """Load the schema contract from YAML."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_schema_structure(data: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """Validate that the dataframe matches the schema structure."""
    required_columns = list(schema.get("columns", {}).keys())
    missing = [col for col in required_columns if col not in data.columns]
    if missing:
        raise ValueError(f"Schema validation failed: Missing columns {missing}")
    return True

def load_all_raw_data(raw_dir: Path) -> List[pd.DataFrame]:
    """Load all raw CSV files from the data/raw directory."""
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")
    
    csv_files = list(raw_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No raw CSV files found in {raw_dir}")
    
    dfs = []
    for file in csv_files:
        logger.info(f"Loading raw data from {file}")
        df = pd.read_csv(file)
        dfs.append(df)
    return dfs

def engineer_switching_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute derived variables.
    switching_index = num_platforms * self_reported_switching_frequency
    """
    logger.info("Engineering switching index...")
    
    # Verify required source variables exist
    required_source_vars = ['num_platforms', 'self_reported_switching_frequency']
    missing_vars = [v for v in required_source_vars if v not in df.columns]
    if missing_vars:
        raise ValueError(f"Missing required source variables for engineering: {missing_vars}")
    
    # Compute switching_index
    # Handle potential non-numeric values or NaNs by coercing to float
    df['num_platforms'] = pd.to_numeric(df['num_platforms'], errors='coerce')
    df['self_reported_switching_frequency'] = pd.to_numeric(df['self_reported_switching_frequency'], errors='coerce')
    
    df['switching_index'] = df['num_platforms'] * df['self_reported_switching_frequency']
    
    # Standardize column names for output
    # Map 'self_reported_switching_frequency' to 'switching_frequency' if present
    if 'self_reported_switching_frequency' in df.columns:
        df['switching_frequency'] = df['self_reported_switching_frequency']
    
    logger.info(f"Switching index computed. Range: [{df['switching_index'].min():.2f}, {df['switching_index'].max():.2f}]")
    return df

def handle_missing_outcomes(df: pd.DataFrame, outcome_col: str = 'cognitive_flexibility_score') -> pd.DataFrame:
    """
    Handle missing outcome values by excluding rows.
    """
    if outcome_col not in df.columns:
        raise ValueError(f"Outcome column '{outcome_col}' not found in dataframe")
    
    initial_count = len(df)
    df_clean = df.dropna(subset=[outcome_col])
    excluded_count = initial_count - len(df_clean)
    
    if excluded_count > 0:
        logger.warning(f"Excluded {excluded_count} rows due to missing {outcome_col} data.")
    else:
        logger.info("No rows excluded due to missing outcome data.")
        
    return df_clean

def validate_and_save(df: pd.DataFrame, output_path: Path, schema: Dict[str, Any]) -> None:
    """
    Validate the final dataframe against the output schema and save to CSV.
    """
    logger.info(f"Valid and saving output to {output_path}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check required output columns based on task description
    required_output_cols = [
        'participant_id', 'age', 'total_screen_time', 'num_platforms',
        'switching_frequency', 'switching_index', 'cognitive_flexibility_score'
    ]
    
    # Map input columns to output columns if names differ
    # Ensure 'participant_id' exists, otherwise create a dummy one if not present
    if 'participant_id' not in df.columns:
        logger.warning("participant_id column not found. Creating default index-based IDs.")
        df['participant_id'] = range(len(df))
    
    # Ensure all required columns exist
    for col in required_output_cols:
        if col not in df.columns:
            # Try to find a similar column if exact match fails
            possible_matches = [c for c in df.columns if col in c or c in col]
            if possible_matches:
                logger.warning(f"Column '{col}' not found. Using '{possible_matches[0]}' instead.")
                df[col] = df[possible_matches[0]]
            else:
                raise ValueError(f"Required output column '{col}' missing and no substitute found.")
    
    # Select and order columns
    final_df = df[required_output_cols]
    
    # Save to CSV
    final_df.to_csv(output_path, index=False)
    logger.info(f"Successfully saved processed data to {output_path}")
    logger.info(f"Output shape: {final_df.shape}")

def main():
    """Main entry point for variable engineering pipeline."""
    logger.info("Starting variable engineering pipeline.")
    
    # Paths
    schema_path = Path("contracts/dataset.schema.yaml")
    raw_dir = Path(DATA_ROOT) / "raw"
    output_path = Path(DATA_ROOT) / "processed" / "participants_cleaned.csv"
    
    # Load Schema
    schema = load_schema_contract(schema_path)
    
    # Load Raw Data
    dfs = load_all_raw_data(raw_dir)
    
    # Combine if multiple files
    if len(dfs) > 1:
        combined_df = pd.concat(dfs, ignore_index=True)
        logger.info(f"Combined {len(dfs)} raw files into one dataframe.")
    else:
        combined_df = dfs[0]
        
    # Validate Input Schema
    validate_schema_structure(combined_df, schema)
    
    # Engineer Variables
    engineered_df = engineer_switching_index(combined_df)
    
    # Handle Missing Outcomes
    cleaned_df = handle_missing_outcomes(engineered_df, 'cognitive_flexibility_score')
    
    # Validate and Save
    validate_and_save(cleaned_df, output_path, schema)
    
    logger.info("Variable engineering pipeline completed successfully.")

if __name__ == "__main__":
    setup_logging()
    main()

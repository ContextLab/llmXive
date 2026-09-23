"""
Task T014a: Generate Cleaned Dataset

Reads the intermediate dataset (cleaned_score_filtered.csv), applies MMSE exclusion
logic based on data/processed/mmse_flag.json (if MMSE is present and valid),
and writes the final cleaned dataset to data/processed/cleaned_dataset.csv.

Also generates data/processed/cleaned_dataset_no_mmse.csv for robustness analysis.

Output Columns:
- participant_id
- stimulus_type
- perseverative_errors
- categories_completed
- age
"""

import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

from utils import setup_logging, log_info, log_warning, log_error, get_timestamp
from config import get_config, get_mmse_threshold

# Configure logging
logger = setup_logging(__name__)

def load_exclusion_log() -> Dict[str, Any]:
    """Load the exclusion log from data/processed/exclusion_log.json."""
    config = get_config()
    log_path = Path(config["paths"]["processed"]) / "exclusion_log.json"
    
    if not log_path.exists():
        log_error(f"Exclusion log not found: {log_path}")
        raise FileNotFoundError(f"Exclusion log not found: {log_path}")
    
    with open(log_path, 'r') as f:
        return json.load(f)

def load_mmse_flag() -> bool:
    """Load the MMSE flag from data/processed/mmse_flag.json."""
    config = get_config()
    flag_path = Path(config["paths"]["processed"]) / "mmse_flag.json"
    
    if not flag_path.exists():
        log_warning(f"MMSE flag not found: {flag_path}. Assuming no MMSE filtering.")
        return False
    
    with open(flag_path, 'r') as f:
        data = json.load(f)
        return data.get("has_mmse", False)

def load_intermediate_dataset() -> pd.DataFrame:
    """Load the score-filtered dataset."""
    config = get_config()
    input_path = Path(config["paths"]["processed"]) / "cleaned_score_filtered.csv"
    
    if not input_path.exists():
        log_error(f"Intermediate dataset not found: {input_path}")
        raise FileNotFoundError(f"Intermediate dataset not found: {input_path}")
    
    return pd.read_csv(input_path)

def create_cleaned_dataset(df: pd.DataFrame, has_mmse: bool) -> pd.DataFrame:
    """
    Apply MMSE filtering if MMSE column is present and valid.
    
    If has_mmse is True:
      - Filter rows where MMSE >= 24 (or threshold from config)
      - Keep the MMSE column in the output
    If has_mmse is False:
      - Return the dataframe as-is (no MMSE filtering)
    
    Selects only the required columns for the final dataset.
    """
    config = get_config()
    mmse_threshold = get_mmse_threshold()
    
    df_cleaned = df.copy()
    
    if has_mmse and "MMSE" in df_cleaned.columns:
        log_info(f"Applying MMSE filter: MMSE >= {mmse_threshold}")
        # Filter out rows where MMSE is null or below threshold
        initial_count = len(df_cleaned)
        df_cleaned = df_cleaned[df_cleaned["MMSE"].notna() & (df_cleaned["MMSE"] >= mmse_threshold)]
        final_count = len(df_cleaned)
        excluded_count = initial_count - final_count
        
        if excluded_count > 0:
            log_info(f"Excluded {excluded_count} records due to MMSE < {mmse_threshold}")
        else:
            log_info("No records excluded based on MMSE threshold")
    else:
        log_info("MMSE flag is False or MMSE column missing. Skipping MMSE filter.")
    
    # Select required columns
    required_columns = [
        "participant_id",
        "stimulus_type",
        "perseverative_errors",
        "categories_completed",
        "age"
    ]
    
    # Check if all required columns exist
    missing_cols = [col for col in required_columns if col not in df_cleaned.columns]
    if missing_cols:
        log_error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    df_final = df_cleaned[required_columns].copy()
    
    log_info(f"Cleaned dataset created with {len(df_final)} records")
    return df_final

def create_no_mmse_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a version of the dataset without MMSE filtering for robustness analysis.
    This is simply the score-filtered dataset (pre-MMSE filter).
    """
    required_columns = [
        "participant_id",
        "stimulus_type",
        "perseverative_errors",
        "categories_completed",
        "age"
    ]
    
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        log_error(f"Missing required columns for no-MMSE dataset: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    df_no_mmse = df[required_columns].copy()
    log_info(f"No-MMSE dataset created with {len(df_no_mmse)} records")
    return df_no_mmse

def save_cleaned_dataset(df: pd.DataFrame, filename: str = "cleaned_dataset.csv") -> Path:
    """Save the cleaned dataset to the processed directory."""
    config = get_config()
    output_path = Path(config["paths"]["processed"]) / filename
    
    df.to_csv(output_path, index=False)
    log_info(f"Saved cleaned dataset to {output_path}")
    return output_path

def main():
    """Main entry point for T014a."""
    log_info("Starting T014a: Generate Cleaned Dataset")
    
    try:
        # Load dependencies
        exclusion_log = load_exclusion_log()
        has_mmse = load_mmse_flag()
        df_intermediate = load_intermediate_dataset()
        
        log_info(f"Loaded intermediate dataset with {len(df_intermediate)} records")
        log_info(f"MMSE flag: {has_mmse}")
        
        # Create cleaned dataset with MMSE filter if applicable
        df_cleaned = create_cleaned_dataset(df_intermediate, has_mmse)
        output_path = save_cleaned_dataset(df_cleaned)
        
        # Create no-MMSE dataset for robustness analysis
        df_no_mmse = create_no_mmse_dataset(df_intermediate)
        no_mmse_path = save_cleaned_dataset(df_no_mmse, "cleaned_dataset_no_mmse.csv")
        
        # Log summary
        log_info(f"Primary cleaned dataset: {output_path} ({len(df_cleaned)} records)")
        log_info(f"No-MMSE dataset: {no_mmse_path} ({len(df_no_mmse)} records)")
        
        log_info("T014a completed successfully")
        
    except FileNotFoundError as e:
        log_error(f"File not found: {e}")
        raise
    except ValueError as e:
        log_error(f"Validation error: {e}")
        raise
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()
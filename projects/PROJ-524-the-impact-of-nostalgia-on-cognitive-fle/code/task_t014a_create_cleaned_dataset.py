"""
Task T014a: Generate Cleaned Dataset

Reads the intermediate cleaned dataset produced by T012e, selects specific columns
required for downstream analysis, and writes the final cleaned dataset.

Columns selected:
- participant_id
- stimulus_type
- perseverative_errors
- categories_completed
- age

Output: data/processed/final_cleaned_dataset.csv
"""

import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_config_paths() -> Dict[str, Path]:
    """
    Construct paths based on project structure.
    Assumes execution from project root or code directory.
    """
    base_dir = Path(__file__).resolve().parent.parent
    processed_dir = base_dir / "data" / "processed"
    return {
        "input_path": processed_dir / "cleaned_dataset.csv",
        "output_path": processed_dir / "final_cleaned_dataset.csv",
        "mmse_flag_path": processed_dir / "mmse_flag.json"
    }

def load_exclusion_log(paths: Dict[str, Path]) -> Optional[Dict[str, Any]]:
    """Load exclusion log if it exists."""
    log_path = paths["input_path"].parent / "exclusion_log.json"
    if log_path.exists():
        try:
            with open(log_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load exclusion log: {e}")
    return None

def load_mmse_flag(paths: Dict[str, Path]) -> bool:
    """Load MMSE flag to confirm data handling context."""
    flag_path = paths["mmse_flag_path"]
    if flag_path.exists():
        try:
            with open(flag_path, 'r') as f:
                data = json.load(f)
                return data.get("has_mmse", False)
        except Exception as e:
            logger.warning(f"Could not load MMSE flag: {e}")
    return False

def load_intermediate_dataset(paths: Dict[str, Path]) -> pd.DataFrame:
    """
    Load the cleaned dataset from T012e.
    Raises FileNotFoundError if the file does not exist.
    """
    input_path = paths["input_path"]
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Ensure T012e (MMSE Exclusion) has completed successfully."
        )
    
    logger.info(f"Loading intermediate dataset from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} records.")
    return df

def create_cleaned_dataset(df: pd.DataFrame, required_columns: list) -> pd.DataFrame:
    """
    Select the required columns for the final dataset.
    Validates that all required columns are present.
    """
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing required columns in input dataset: {missing_cols}. "
            f"Available columns: {list(df.columns)}"
        )
    
    logger.info(f"Selecting columns: {required_columns}")
    final_df = df[required_columns].copy()
    
    # Ensure data types are consistent if necessary
    # e.g., ensure numeric columns are float
    numeric_cols = ['perseverative_errors', 'categories_completed', 'age']
    for col in numeric_cols:
        if col in final_df.columns:
            final_df[col] = pd.to_numeric(final_df[col], errors='coerce')
    
    return final_df

def save_cleaned_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """Save the final cleaned dataset to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Saving final cleaned dataset to {output_path}")
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} records to {output_path}")

def main() -> int:
    """Main entry point for T014a."""
    logger.info("Starting Task T014a: Generate Cleaned Dataset")
    
    try:
        paths = get_config_paths()
        required_columns = [
            'participant_id', 
            'stimulus_type', 
            'perseverative_errors', 
            'categories_completed', 
            'age'
        ]
        
        # Load intermediate data
        df = load_intermediate_dataset(paths)
        
        # Load context (optional but good for logging)
        exclusion_log = load_exclusion_log(paths)
        has_mmse = load_mmse_flag(paths)
        logger.info(f"MMSE Flag (has_mmse): {has_mmse}")
        
        # Create final dataset
        final_df = create_cleaned_dataset(df, required_columns)
        
        # Save output
        save_cleaned_dataset(final_df, paths["output_path"])
        
        logger.info("Task T014a completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during T014a: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())

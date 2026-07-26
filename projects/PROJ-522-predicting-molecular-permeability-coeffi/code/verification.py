"""
Verification script for User Story 1 (US1).

Task T017b: Implement verification logic to confirm the final dataset contains 
>= 500 unique compounds (or 2000 as per scenario) without triggering the fallback. 
If count < target, raise an error.

This script loads the deduplicated dataset produced by T013 and validates the 
unique compound count against the configured threshold.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DEFAULT_DATA_PATH = "data/processed/deduplicated.csv"
DEFAULT_MIN_COMPOUNDS = 500
TARGET_COMPOUNDS_SCENARIO = 2000

def load_deduplicated_dataset(file_path: str) -> pd.DataFrame:
    """
    Load the deduplicated dataset from disk.
    
    Args:
        file_path: Path to the deduplicated CSV file.
        
    Returns:
        DataFrame containing the deduplicated dataset.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or missing required columns.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Deduplicated dataset not found at: {file_path}")
    
    logger.info(f"Loading dataset from: {file_path}")
    df = pd.read_csv(path)
    
    if df.empty:
        raise ValueError("Dataset is empty after loading.")
    
    required_columns = ['smiles', 'target_mean', 'count', 'source_id']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset missing required columns: {missing_cols}")
    
    return df

def count_unique_compounds(df: pd.DataFrame) -> int:
    """
    Count the number of unique SMILES strings in the dataset.
    
    Args:
        df: DataFrame containing molecular data.
        
    Returns:
        Integer count of unique SMILES.
    """
    unique_smiles = df['smiles'].nunique()
    logger.info(f"Found {unique_smiles} unique compounds in dataset.")
    return unique_smiles

def verify_dataset_size(df: pd.DataFrame, min_threshold: int = DEFAULT_MIN_COMPOUNDS) -> bool:
    """
    Verify that the dataset meets the minimum unique compound requirement.
    
    This function implements the core logic for T017b:
    - Checks if unique compound count >= min_threshold
    - Raises a RuntimeError if the count is below the threshold
    - No fallback to synthetic data or random sampling is permitted.
    
    Args:
        df: DataFrame containing molecular data.
        min_threshold: Minimum number of unique compounds required.
        
    Returns:
        True if verification passes.
        
    Raises:
        RuntimeError: If the number of unique compounds is below the threshold.
    """
    unique_count = count_unique_compounds(df)
    
    logger.info(f"Verifying dataset size: {unique_count} >= {min_threshold}")
    
    if unique_count < min_threshold:
        error_msg = (
            f"VERIFICATION FAILED: Dataset contains {unique_count} unique compounds, "
            f"which is below the required minimum of {min_threshold}. "
            f"Pipeline must fail loudly; no synthetic fallback allowed."
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    logger.info("VERIFICATION PASSED: Dataset size requirement met.")
    return True

def main():
    """
    Main entry point for the verification script.
    
    Usage:
        python code/verification.py [--path <csv_path>] [--min <count>]
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify dataset size for US1")
    parser.add_argument(
        "--path", 
        type=str, 
        default=DEFAULT_DATA_PATH,
        help=f"Path to deduplicated CSV (default: {DEFAULT_DATA_PATH})"
    )
    parser.add_argument(
        "--min", 
        type=int, 
        default=DEFAULT_MIN_COMPOUNDS,
        help=f"Minimum unique compounds required (default: {DEFAULT_MIN_COMPOUNDS})"
    )
    args = parser.parse_args()
    
    try:
        # Load dataset
        df = load_deduplicated_dataset(args.path)
        
        # Verify size
        verify_dataset_size(df, args.min)
        
        logger.info("Verification completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Invalid dataset: {e}")
        return 1
    except RuntimeError as e:
        logger.error(f"Verification failed: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during verification: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
import os
import sys
import logging
from pathlib import Path
import pandas as pd

# Configure logging to match project standards
logger = logging.getLogger(__name__)

def load_deduplicated_dataset(file_path: str) -> pd.DataFrame:
    """
    Loads the deduplicated dataset from the specified CSV file.
    
    Args:
        file_path (str): Path to the deduplicated CSV file.
    
    Returns:
        pd.DataFrame: The loaded dataset.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        pd.errors.EmptyDataError: If the file is empty.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Deduplicated dataset not found at {file_path}")
    
    logger.info(f"Loading deduplicated dataset from {file_path}")
    df = pd.read_csv(path)
    
    if df.empty:
        raise ValueError("The deduplicated dataset is empty.")
    
    return df

def count_unique_compounds(df: pd.DataFrame, smiles_column: str = 'smiles') -> int:
    """
    Counts the number of unique compounds (SMILES) in the dataset.
    
    Args:
        df (pd.DataFrame): The dataset to analyze.
        smiles_column (str): The column name containing SMILES strings.
    
    Returns:
        int: The count of unique SMILES.
    """
    if smiles_column not in df.columns:
        raise KeyError(f"Column '{smiles_column}' not found in dataset.")
    
    unique_count = df[smiles_column].nunique()
    logger.info(f"Found {unique_count} unique compounds in the dataset.")
    return unique_count

def verify_dataset_size(df: pd.DataFrame, min_target: int = 500, smiles_column: str = 'smiles') -> bool:
    """
    Verifies that the dataset contains at least the minimum required number of unique compounds.
    
    This function implements the verification logic for T017b.
    It counts unique SMILES and raises a ValueError if the count is below the target.
    
    Args:
        df (pd.DataFrame): The dataset to verify.
        min_target (int): The minimum required number of unique compounds (default 500).
        smiles_column (str): The column name containing SMILES strings.
    
    Returns:
        bool: True if the dataset meets the requirement.
    
    Raises:
        ValueError: If the number of unique compounds is less than min_target.
    """
    unique_count = count_unique_compounds(df, smiles_column)
    
    if unique_count < min_target:
        error_msg = (
            f"Verification FAILED: Dataset contains only {unique_count} unique compounds, "
            f"which is less than the required minimum of {min_target}. "
            "The pipeline has not met the data volume requirement."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Verification PASSED: Dataset contains {unique_count} unique compounds (>= {min_target}).")
    return True

def main():
    """
    Main entry point for the verification script.
    
    Loads the deduplicated dataset, counts unique compounds, and verifies
    that the count meets the minimum threshold (500).
    
    Expects the deduplicated dataset to be at: data/processed/deduplicated.csv
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    dedup_file = project_root / "data" / "processed" / "deduplicated.csv"
    
    # Configuration
    MIN_COMPOUNDS = 500  # Target from task description
    
    try:
        logger.info("Starting dataset verification (T017b)...")
        
        # Load the dataset
        df = load_deduplicated_dataset(str(dedup_file))
        
        # Verify size
        verify_dataset_size(df, min_target=MIN_COMPOUNDS)
        
        logger.info("Verification completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        # This is the expected failure mode for T017b if data is insufficient
        logger.error(f"Verification failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
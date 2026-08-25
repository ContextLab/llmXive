import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import pandas as pd
from datasets import load_dataset
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure all required directories exist."""
    dirs = [
        "data/raw",
        "data/processed",
        "data/explanation_tiers",
        "data/simulation_results",
        "code",
        "tests",
        "docs"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory: {d}")

def load_assistments_dataset() -> Optional[pd.DataFrame]:
    """
    Load the ASSISTments dataset from HuggingFace.
    Returns a DataFrame or None if not available.
    """
    try:
        # Attempt to load a publicly available ASSISTments dataset
        # Using a specific subset or version that is known to exist
        dataset = load_dataset(" ASSISTments/2017", split="train", trust_remote_code=True)
        df = dataset.to_pandas()
        logger.info(f"Loaded ASSISTments dataset with shape: {df.shape}")
        return df
    except Exception as e:
        logger.warning(f"Could not load ASSISTments dataset: {e}")
        return None

def load_oulad_dataset() -> Optional[pd.DataFrame]:
    """
    Load the OULAD dataset from HuggingFace.
    Returns a DataFrame or None if not available.
    """
    try:
        # OULAD dataset on HuggingFace
        dataset = load_dataset("OUOpen/oulad", split="train", trust_remote_code=True)
        df = dataset.to_pandas()
        logger.info(f"Loaded OULAD dataset with shape: {df.shape}")
        return df
    except Exception as e:
        logger.warning(f"Could not load OULAD dataset: {e}")
        return None

def verify_features(df: pd.DataFrame, required_features: Set[str]) -> bool:
    """
    Verify that the DataFrame contains required features.
    Returns True if all required features are present.
    """
    missing = required_features - set(df.columns)
    if missing:
        logger.error(f"Missing required features: {missing}")
        return False
    return True

def save_dataset(df: pd.DataFrame, path: str):
    """Save a DataFrame to a CSV file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Saved dataset to {path}")

def load_and_verify_datasets() -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Load both ASSISTments and OULAD datasets and verify features.
    Returns tuple of (assistments_df, oulad_df).
    """
    ensure_directories()
    
    required_features = {'timestamp', 'error', 'hint', 'response_time', 'student_id', 'problem_id'}
    
    assistments_df = load_assistments_dataset()
    if assistments_df is not None:
        verify_features(assistments_df, required_features)
    
    oulad_df = load_oulad_dataset()
    if oulad_df is not None:
        verify_features(oulad_df, required_features)
        
    return assistments_df, oulad_df

def validate_golden_set(golden_set_path: str = "data/processed/golden_set.csv") -> bool:
    """
    Phase 0 "Golden Set" validation.
    Checks for the existence of `data/processed/golden_set.csv` containing
    either an `expert_load_score` column OR concurrent self-reports.
    Exits with a specific error if missing or invalid.
    
    Args:
        golden_set_path: Path to the golden set CSV file.
        
    Returns:
        bool: True if validation passes.
        
    Raises:
        SystemExit: If the file is missing or lacks required columns.
    """
    logger.info(f"Validating Golden Set at: {golden_set_path}")
    
    if not os.path.exists(golden_set_path):
        error_msg = (
            f"CRITICAL: Golden Set file not found at '{golden_set_path}'.\n"
            "The pipeline requires a validated expert-labeled dataset to proceed.\n"
            "Please ensure 'data/processed/golden_set.csv' exists with at least "
            "one of the following columns: 'expert_load_score' or 'self_report_load'.\n"
            "Refer to task T006a/T006b for instructions on obtaining or creating this file."
        )
        logger.error(error_msg)
        raise SystemExit(error_msg)
    
    try:
        df = pd.read_csv(golden_set_path)
        logger.info(f"Golden Set loaded with shape: {df.shape}")
        
        has_expert_score = 'expert_load_score' in df.columns
        has_self_report = 'self_report_load' in df.columns
        
        if not has_expert_score and not has_self_report:
            error_msg = (
                f"CRITICAL: Golden Set at '{golden_set_path}' is invalid.\n"
                "Missing required validation columns: 'expert_load_score' or 'self_report_load'.\n"
                f"Found columns: {list(df.columns)}\n"
                "The model training and validation pipeline cannot proceed without these labels."
            )
            logger.error(error_msg)
            raise SystemExit(error_msg)
        
        if has_expert_score:
            logger.info("Found 'expert_load_score' column. Validation PASSED.")
        elif has_self_report:
            logger.info("Found 'self_report_load' column. Validation PASSED.")
        
        return True
        
    except pd.errors.EmptyDataError:
        error_msg = f"CRITICAL: Golden Set file at '{golden_set_path}' is empty."
        logger.error(error_msg)
        raise SystemExit(error_msg)
    except Exception as e:
        error_msg = f"CRITICAL: Error reading Golden Set file: {e}"
        logger.error(error_msg)
        raise SystemExit(error_msg)

def main():
    """Main entry point for data loading and validation."""
    ensure_directories()
    
    # Perform Phase 0 Golden Set validation first
    # This is a blocking prerequisite for any model training
    try:
        validate_golden_set()
    except SystemExit as e:
        # Re-raise to stop execution if Golden Set is missing
        raise e
        
    # Proceed to load public datasets
    assistments_df, oulad_df = load_and_verify_datasets()
    
    if assistments_df is None and oulad_df is None:
        logger.warning("No public datasets were successfully loaded. "
                     "Proceed with caution if using existing processed data.")
    else:
        logger.info("Public datasets loaded successfully.")

if __name__ == "__main__":
    main()
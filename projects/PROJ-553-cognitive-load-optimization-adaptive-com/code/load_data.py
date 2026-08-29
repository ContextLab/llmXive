import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import pandas as pd
from datasets import load_dataset
import logging

# Ensure the code directory is in the path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))

def setup_logging():
    """Basic logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def ensure_directories():
    """Create necessary data directories."""
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

def load_assistments_dataset():
    """Load ASSISTments dataset from HuggingFace."""
    try:
        logger.info("Loading ASSISTments dataset...")
        dataset = load_dataset(" ASSISTments/2009-2010", split="train")
        return dataset
    except Exception as e:
        logger.error(f"Failed to load ASSISTments: {e}")
        raise

def load_oulad_dataset():
    """Load OULAD dataset from HuggingFace."""
    try:
        logger.info("Loading OULAD dataset...")
        dataset = load_dataset("openUniversity/oulad", split="train")
        return dataset
    except Exception as e:
        logger.error(f"Failed to load OULAD: {e}")
        raise

def verify_features(df: pd.DataFrame, required_features: Set[str]) -> bool:
    """Verify that required features exist in the dataframe."""
    missing = required_features - set(df.columns)
    if missing:
        logger.warning(f"Missing features in dataset: {missing}")
        return False
    return True

def save_dataset(df: pd.DataFrame, path: str):
    """Save dataframe to CSV."""
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Saved dataset to {path}")

def load_and_verify_datasets():
    """Load ASSISTments and OULAD, verify features, and save processed data."""
    ensure_directories()
    
    # Define required features for cognitive load estimation
    required_features = {
        'timestamp', 'response', 'error', 'hint_request', 
        'latency', 'session_id', 'user_id', 'item_id'
    }

    # Attempt to load ASSISTments
    try:
        assistments = load_assistments_dataset()
        assistments_df = assistments.to_pandas()
        if verify_features(assistments_df, required_features):
            save_dataset(assistments_df, "data/raw/assistments_raw.csv")
        else:
            logger.warning("ASSISTments missing required features, skipping.")
    except Exception as e:
        logger.error(f"Could not process ASSISTments: {e}")

    # Attempt to load OULAD
    try:
        oulad = load_oulad_dataset()
        oulad_df = oulad.to_pandas()
        # OULAD schema might differ, check for generic interaction columns
        if verify_features(oulad_df, {'timestamp', 'user_id', 'item_id'}):
            save_dataset(oulad_df, "data/raw/oulad_raw.csv")
        else:
            logger.warning("OULAD missing required features, skipping.")
    except Exception as e:
        logger.error(f"Could not process OULAD: {e}")

def validate_golden_set(golden_set_path: str = "data/processed/golden_set.csv") -> bool:
    """
    Validate the presence and integrity of the Golden Set.
    
    Checks:
    1. File exists at `data/processed/golden_set.csv`.
    2. Contains at least one of the required target columns:
       - 'expert_load_score' (numeric 0-100)
       - 'concurrent_self_report' (numeric or categorical mapped to score)
    
    If the file is missing or lacks required columns, the function logs a critical
    error and calls sys.exit(1) to halt the pipeline. No synthetic data is generated.
    """
    path = Path(golden_set_path)
    
    if not path.exists():
        error_msg = (
            "Validation Data Missing: Golden Set or required interaction features "
            "with concurrent self-reports not found. Cannot proceed with model training."
        )
        logger.critical(error_msg)
        logger.critical(f"Expected file at: {path.absolute()}")
        sys.exit(1)
    
    try:
        df = pd.read_csv(path)
    except Exception as e:
        error_msg = f"Validation Data Corrupted: Could not read {path}. Error: {e}"
        logger.critical(error_msg)
        sys.exit(1)

    required_targets = {'expert_load_score', 'concurrent_self_report'}
    available_targets = required_targets.intersection(df.columns)

    if not available_targets:
        error_msg = (
            "Validation Data Invalid: Golden Set exists but lacks required target columns. "
            f"Expected one of: {required_targets}. Found columns: {list(df.columns)}"
        )
        logger.critical(error_msg)
        sys.exit(1)

    # Check for at least one valid entry
    if len(df) == 0:
        error_msg = "Validation Data Invalid: Golden Set is empty."
        logger.critical(error_msg)
        sys.exit(1)

    logger.info(f"Golden Set validation passed. Found {len(df)} rows. Target column: {list(available_targets)[0]}")
    return True

def main():
    """Main entry point for data loading and validation."""
    logger.info("Starting data loading and validation pipeline.")
    
    # 1. Ensure directories exist
    ensure_directories()
    
    # 2. Load and verify public datasets (optional for T005, but good practice)
    # load_and_verify_datasets() 
    
    # 3. CRITICAL: Validate Golden Set (T005 Requirement)
    # This function will exit(1) if the golden set is missing or invalid.
    validate_golden_set()
    
    logger.info("Data loading and validation completed successfully.")

if __name__ == "__main__":
    main()
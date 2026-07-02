"""
T020: Implement test_split.py to partition a subset of full_pool_final.csv
into a Fixed Test Set for model evaluation.

Follows FR-009 and Plan Phase 0.5.
Uses a fixed random seed to ensure reproducibility.
"""
import os
import sys
import json
import hashlib
import argparse
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger
from utils.checksum_utils import compute_sha256, write_checksum_file
from config import load_env

# Initialize logger
logger = get_logger("test_split")

# Constants
TEST_SIZE = 0.20  # 20% for test set as per standard practice unless specified otherwise
RANDOM_SEED = 42  # Fixed seed for reproducibility
INPUT_FILE = project_root / "data" / "processed" / "full_pool_final.csv"
OUTPUT_DIR = project_root / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "test_set.csv"
METADATA_FILE = OUTPUT_DIR / "test_set_metadata.json"
CHECKSUM_SUFFIX = ".sha256"

def load_data(input_path: Path) -> pd.DataFrame:
    """Load the full pool final dataset."""
    logger.info(f"Loading data from {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def create_test_set(df: pd.DataFrame, test_size: float, seed: int) -> pd.DataFrame:
    """
    Partition the dataset into a fixed test set.
    We use train_test_split with stratification if a target column exists,
    otherwise simple random split. Here we assume 'formation_energy' is the target.
    """
    target_col = "formation_energy"
    if target_col not in df.columns:
        logger.warning(f"Target column '{target_col}' not found. Performing non-stratified split.")
        train, test = train_test_split(
            df, test_size=test_size, random_state=seed
        )
    else:
        # Stratify by formation_energy bins to preserve distribution
        # Create bins if necessary or just use the raw values if integer/low cardinality
        # For continuous values, we can stratify by binned values or just the column if pandas handles it
        # Pandas train_test_split supports stratifying on a continuous column directly in newer versions
        # but often it's safer to bin for continuous targets.
        # However, to keep it simple and robust for this task:
        try:
            train, test = train_test_split(
                df, test_size=test_size, random_state=seed, stratify=df[target_col]
            )
        except (ValueError, TypeError):
            # If stratification fails (e.g., too many unique values), fallback to non-stratified
            logger.warning("Stratification failed (likely continuous target). Falling back to random split.")
            train, test = train_test_split(
                df, test_size=test_size, random_state=seed
            )
    
    logger.info(f"Created test set with {len(test)} rows ({len(test)/len(df)*100:.2f}%)")
    return test

def save_test_set(test_df: pd.DataFrame, output_path: Path) -> str:
    """Save the test set to CSV and return its checksum."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    test_df.to_csv(output_path, index=False)
    logger.info(f"Saved test set to {output_path}")
    
    checksum = compute_sha256(output_path)
    checksum_file = str(output_path) + CHECKSUM_SUFFIX
    write_checksum_file(checksum_file, checksum)
    logger.info(f"Saved checksum to {checksum_file}")
    
    return checksum

def save_metadata(test_df: pd.DataFrame, checksum: str, seed: int, output_path: Path) -> None:
    """Save metadata about the test set."""
    metadata = {
        "row_count": len(test_df),
        "column_count": len(test_df.columns),
        "columns": list(test_df.columns),
        "checksum": checksum,
        "random_seed": seed,
        "test_size_ratio": TEST_SIZE,
        "source_file": str(INPUT_FILE),
        "generated_at": pd.Timestamp.now().isoformat()
    }
    
    with open(output_path, "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {output_path}")

def main():
    """Main entry point for T020."""
    logger.info("Starting T020: Test Set Partitioning")
    
    # Load environment configuration (validates MP_API_KEY presence if needed, though not strictly needed for this local task)
    try:
        load_env()
    except Exception as e:
        logger.warning(f"Environment config warning (non-fatal for this task): {e}")

    if not INPUT_FILE.exists():
        logger.error(f"Input file {INPUT_FILE} does not exist. Run T027 first.")
        sys.exit(1)

    try:
        # 1. Load Data
        df = load_data(INPUT_FILE)

        # 2. Create Test Set
        test_df = create_test_set(df, TEST_SIZE, RANDOM_SEED)

        # 3. Save Test Set and Checksum
        checksum = save_test_set(test_df, OUTPUT_FILE)

        # 4. Save Metadata
        save_metadata(test_df, checksum, RANDOM_SEED, METADATA_FILE)

        logger.info("T020 completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Error during test split: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
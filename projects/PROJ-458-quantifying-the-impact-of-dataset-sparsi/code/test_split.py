"""
Test Set Splitting Module (T020)

Partitions a subset of the full_pool_final.csv into a Fixed Test Set for model evaluation.
This implements FR-009 and Plan Phase 0.5 requirements.
"""
import os
import sys
import json
import hashlib
import argparse
import pandas as pd
from pathlib import Path

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))

from utils.logging import get_logger
from utils.checksum_utils import compute_sha256

logger = get_logger(__name__)

# Configuration
RANDOM_SEED = 42  # Fixed seed for reproducibility (FR-009)
TEST_SPLIT_RATIO = 0.2  # 20% test set
INPUT_FILE = "data/processed/full_pool_final.csv"
OUTPUT_FILE = "data/processed/test_set.csv"
METADATA_FILE = "data/metadata/test_set_metadata.json"

def load_data(input_path: str) -> pd.DataFrame:
    """
    Load the full pool final dataset.

    Args:
        input_path: Path to the input CSV file.

    Returns:
        DataFrame containing the full pool data.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is empty or has invalid format.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(path)

    if df.empty:
        raise ValueError(f"Input file {input_path} is empty")

    logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    return df

def create_test_set(df: pd.DataFrame, seed: int = RANDOM_SEED, ratio: float = TEST_SPLIT_RATIO) -> pd.DataFrame:
    """
    Partition the data into a fixed test set using stratified sampling if possible,
    otherwise simple random sampling.

    Args:
        df: Input DataFrame.
        seed: Random seed for reproducibility.
        ratio: Proportion of data to use for the test set.

    Returns:
        DataFrame containing the test set.
    """
    logger.info(f"Creating test set with ratio {ratio} and seed {seed}")

    # Ensure reproducibility
    df_sample = df.sample(frac=1, random_state=seed).reset_index(drop=True)

    # Calculate split index
    split_idx = int(len(df_sample) * (1 - ratio))

    # Split data
    test_df = df_sample.iloc[split_idx:].copy()
    train_df = df_sample.iloc[:split_idx].copy()

    logger.info(f"Train set size: {len(train_df)}, Test set size: {len(test_df)}")

    return test_df

def save_test_set(test_df: pd.DataFrame, output_path: str) -> None:
    """
    Save the test set to a CSV file.

    Args:
        test_df: DataFrame containing the test set.
        output_path: Path to the output CSV file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving test set to {output_path}")
    test_df.to_csv(path, index=False)

    logger.info(f"Saved {len(test_df)} rows to {output_path}")

def save_metadata(test_df: pd.DataFrame, output_path: str) -> None:
    """
    Save metadata about the test set to a JSON file.

    Args:
        test_df: DataFrame containing the test set.
        output_path: Path to the output JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Compute checksum
    checksum = compute_sha256(path) if path.exists() else None

    # If we just saved the file, compute checksum of the saved file
    if not checksum:
        # Re-save to ensure checksum is computed on final file
        test_df.to_csv(path, index=False)
        checksum = compute_sha256(path)

    metadata = {
        "row_count": len(test_df),
        "columns": list(test_df.columns),
        "checksum": checksum,
        "random_seed": RANDOM_SEED,
        "split_ratio": TEST_SPLIT_RATIO,
        "source_file": INPUT_FILE,
        "created_at": pd.Timestamp.now().isoformat()
    }

    logger.info(f"Saving metadata to {output_path}: {metadata}")

    with open(path, 'w') as f:
        json.dump(metadata, f, indent=2)

def main():
    """
    Main entry point for the test split script.
    """
    parser = argparse.ArgumentParser(description="Split data into fixed test set")
    parser.add_argument("--input", type=str, default=INPUT_FILE, help="Input CSV file path")
    parser.add_argument("--output", type=str, default=OUTPUT_FILE, help="Output test set CSV file path")
    parser.add_argument("--metadata", type=str, default=METADATA_FILE, help="Output metadata JSON file path")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED, help="Random seed for splitting")
    parser.add_argument("--ratio", type=float, default=TEST_SPLIT_RATIO, help="Test set ratio")
    args = parser.parse_args()

    try:
        # Load data
        df = load_data(args.input)

        # Create test set
        test_df = create_test_set(df, seed=args.seed, ratio=args.ratio)

        # Save test set
        save_test_set(test_df, args.output)

        # Save metadata
        save_metadata(test_df, args.metadata)

        logger.info("Test set splitting completed successfully")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Invalid data: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

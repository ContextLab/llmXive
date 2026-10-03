"""
Test Set Splitting Module (T020)

Partitions a stratified sample (5000 rows) from data/raw/raw_pool.csv into a Fixed Test Set.
Implements FR-009 and Plan Phase 0.5 requirements.
Uses pd.qcut on formation_energy to define strata, then samples stratified by these bins.
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
TEST_SIZE = 5000  # Exact number of rows for the test set
INPUT_FILE = "data/raw/raw_pool.csv"
OUTPUT_FILE = "data/processed/test_set.csv"
INDICES_FILE = "data/processed/test_set_indices.csv"
METADATA_FILE = "data/metadata/test_set_metadata.json"

def load_data(input_path: str) -> pd.DataFrame:
    """
    Load the raw pool dataset.

    Args:
        input_path: Path to the input CSV file.

    Returns:
        DataFrame containing the raw pool data.

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

    if 'formation_energy' not in df.columns:
        raise ValueError(f"Input file {input_path} missing required column 'formation_energy'")

    # Drop rows with null formation_energy for stratification
    df_clean = df.dropna(subset=['formation_energy'])
    if len(df_clean) < TEST_SIZE:
        raise ValueError(f"Not enough valid rows ({len(df_clean)}) to create test set of size {TEST_SIZE}")

    logger.info(f"Loaded {len(df)} rows total, {len(df_clean)} valid for stratification")
    return df, df_clean

def create_test_set(df_full: pd.DataFrame, df_valid: pd.DataFrame, seed: int = RANDOM_SEED, size: int = TEST_SIZE) -> tuple[pd.DataFrame, list[int]]:
    """
    Create a stratified test set based on formation_energy bins.

    Algorithm:
    1. Use pd.qcut on formation_energy to define strata.
    2. Sample a proportional number of rows from each stratum to reach total size.
    3. Return the test set and the list of original indices.

    Args:
        df_full: The full DataFrame (to retrieve original rows by index).
        df_valid: The DataFrame with valid formation_energy values.
        seed: Random seed for reproducibility.
        size: Target size of the test set.

    Returns:
        Tuple of (test_set_dataframe, list_of_indices)
    """
    logger.info(f"Creating stratified test set of size {size} with seed {seed}")

    # Define strata using qcut (quantile-based binning)
    # Use 10 bins to ensure good coverage across the energy distribution
    try:
        bins = 10
        # Ensure we don't try to create more bins than unique values
        unique_vals = df_valid['formation_energy'].nunique()
        if unique_vals < bins:
            bins = unique_vals
            logger.warning(f"Reducing bins to {bins} due to low unique values in formation_energy")

        df_valid = df_valid.copy()
        df_valid['strata'] = pd.qcut(df_valid['formation_energy'], q=bins, duplicates='drop')
    except ValueError as e:
        raise ValueError(f"Failed to create strata: {e}")

    # Calculate sample size per stratum (proportional)
    strata_counts = df_valid['strata'].value_counts()
    total_valid = len(df_valid)
    
    # Calculate proportional allocation
    sample_sizes = (strata_counts / total_valid * size).round().astype(int)
    
    # Adjust for rounding errors to ensure exact size
    current_total = sample_sizes.sum()
    if current_total < size:
        # Add remaining to the largest stratum
        sample_sizes[sample_sizes.idxmax()] += (size - current_total)
    elif current_total > size:
        # Subtract from the largest stratum
        sample_sizes[sample_sizes.idxmax()] -= (current_total - size)

    logger.info(f"Strata sample sizes: {sample_sizes.to_dict()}")

    # Perform stratified sampling
    test_indices = []
    for stratum, n in sample_sizes.items():
        stratum_df = df_valid[df_valid['strata'] == stratum]
        sampled = stratum_df.sample(n=n, random_state=seed)
        test_indices.extend(sampled.index.tolist())
    
    # Ensure we have exactly the requested size
    if len(test_indices) != size:
        logger.warning(f"Final size mismatch: {len(test_indices)} vs {size}, truncating/padding")
        test_indices = test_indices[:size]

    # Extract the test set from the FULL dataframe using the indices
    test_df = df_full.loc[test_indices].copy()
    
    # Reset index for clean output
    test_df = test_df.reset_index(drop=True)
    
    # Remove the temporary 'strata' column if it somehow got included
    if 'strata' in test_df.columns:
        test_df = test_df.drop(columns=['strata'])

    logger.info(f"Created test set with {len(test_df)} rows")
    return test_df, test_indices

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

def save_indices(indices: list[int], output_path: str) -> None:
    """
    Save the indices of the test set rows to a CSV file.
    This ensures strict independence for downstream tasks.

    Args:
        indices: List of integer indices.
        output_path: Path to the output CSV file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving test set indices to {output_path}")
    df_indices = pd.DataFrame({'index': indices})
    df_indices.to_csv(path, index=False)
    logger.info(f"Saved {len(indices)} indices to {output_path}")

def save_metadata(test_df: pd.DataFrame, indices: list[int], output_path: str) -> None:
    """
    Save metadata about the test set to a JSON file.

    Args:
        test_df: DataFrame containing the test set.
        indices: List of original indices.
        output_path: Path to the output JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Compute checksum of the saved test set file
    checksum = compute_sha256(Path(OUTPUT_FILE))

    metadata = {
        "row_count": len(test_df),
        "index_count": len(indices),
        "columns": list(test_df.columns),
        "checksum": checksum,
        "random_seed": RANDOM_SEED,
        "test_size": TEST_SIZE,
        "source_file": INPUT_FILE,
        "indices_file": INDICES_FILE,
        "created_at": pd.Timestamp.now().isoformat()
    }

    logger.info(f"Saving metadata to {output_path}: {metadata}")

    with open(path, 'w') as f:
        json.dump(metadata, f, indent=2)

def main():
    """
    Main entry point for the test split script.
    """
    parser = argparse.ArgumentParser(description="Split raw pool into stratified fixed test set")
    parser.add_argument("--input", type=str, default=INPUT_FILE, help="Input raw pool CSV file path")
    parser.add_argument("--output", type=str, default=OUTPUT_FILE, help="Output test set CSV file path")
    parser.add_argument("--indices", type=str, default=INDICES_FILE, help="Output test set indices CSV file path")
    parser.add_argument("--metadata", type=str, default=METADATA_FILE, help="Output metadata JSON file path")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED, help="Random seed for splitting")
    parser.add_argument("--size", type=int, default=TEST_SIZE, help="Target test set size")
    args = parser.parse_args()

    try:
        # Load data (verify existence of raw_pool.csv)
        df_full, df_valid = load_data(args.input)

        # Create stratified test set
        test_df, indices = create_test_set(df_full, df_valid, seed=args.seed, size=args.size)

        # Save test set
        save_test_set(test_df, args.output)

        # Save indices
        save_indices(indices, args.indices)

        # Save metadata
        save_metadata(test_df, indices, args.metadata)

        logger.info("Test set splitting completed successfully")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        logger.error("Prerequisite T024 (data/raw/raw_pool.csv) must be completed first.")
        return 1
    except ValueError as e:
        logger.error(f"Invalid data: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
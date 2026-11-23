import os
import sys
import logging
import pyarrow.parquet as pq
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any

from utils.logging_config import get_logger

logger = get_logger(__name__)

# Hardcoded deterministic seed for reproducibility as per T004 constraints
# and T046 determinism fix requirement.
_DETERMINISTIC_SEED = 42

def split_data(input_path: Path, output_prefix: Path, test_size: float = 0.2, seed: int = None) -> None:
    """Split data into train and test sets deterministically.
    
    Args:
        input_path: Path to the input parquet file.
        output_prefix: Base path for output files (will append _train/_test).
        test_size: Fraction of data to use for testing.
        seed: Random seed. If None, uses the hardcoded deterministic seed.
    """
    logger.info(f"Loading data from {input_path}")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} rows")
    
    # Use hardcoded seed if not provided to ensure determinism across runs
    effective_seed = seed if seed is not None else _DETERMINISTIC_SEED
    logger.info(f"Using random seed: {effective_seed}")
    
    # Explicitly set the seed before any random operations
    np.random.seed(effective_seed)
    indices = np.random.permutation(len(df))
    test_count = int(len(df) * test_size)
    test_indices = indices[:test_count]
    train_indices = indices[test_count:]
    
    train_df = df.iloc[train_indices].reset_index(drop=True)
    test_df = df.iloc[test_indices].reset_index(drop=True)
    
    train_path = output_prefix.with_name(output_prefix.name + "_train.parquet")
    test_path = output_prefix.with_name(output_prefix.name + "_test.parquet")
    
    logger.info(f"Saving train data ({len(train_df)} rows) to {train_path}")
    train_df.to_parquet(train_path, index=False)
    
    logger.info(f"Saving test data ({len(test_df)} rows) to {test_path}")
    test_df.to_parquet(test_path, index=False)
    
    logger.info(f"Split complete. Train: {len(train_df)}, Test: {len(test_df)}")

def load_splits(prefix: Path) -> Dict[str, pd.DataFrame]:
    """Load train and test splits.
    
    Args:
        prefix: Base path to the split files.
        
    Returns:
        Dictionary with 'train' and 'test' keys containing DataFrames.
    """
    train_path = prefix.with_name(prefix.name + "_train.parquet")
    test_path = prefix.with_name(prefix.name + "_test.parquet")
    
    if not train_path.exists():
        raise FileNotFoundError(f"Train file not found: {train_path}")
    if not test_path.exists():
        raise FileNotFoundError(f"Test file not found: {test_path}")
        
    return {
        "train": pd.read_parquet(train_path),
        "test": pd.read_parquet(test_path)
    }

def verify_determinism(input_path: Path, output_prefix: Path, iterations: int = 5) -> bool:
    """Verify that the split is deterministic across multiple runs.
    
    Args:
        input_path: Path to the input data.
        output_prefix: Base path for output files.
        iterations: Number of times to run the split.
        
    Returns:
        True if all splits produced identical shapes, False otherwise.
    """
    logger.info(f"Verifying determinism with {iterations} iterations...")
    
    shapes = []
    for i in range(iterations):
        # Clean up previous split files to ensure fresh run
        train_path = output_prefix.with_name(output_prefix.name + "_train.parquet")
        test_path = output_prefix.with_name(output_prefix.name + "_test.parquet")
        
        if train_path.exists():
            train_path.unlink()
        if test_path.exists():
            test_path.unlink()
        
        # Run split with explicit seed
        split_data(input_path, output_prefix, seed=_DETERMINISTIC_SEED)
        
        # Load and record shapes
        train_df, test_df = load_splits(output_prefix)
        shapes.append((train_df.shape, test_df.shape))
        logger.info(f"Iteration {i+1}: Train {train_df.shape}, Test {test_df.shape}")
    
    # Check if all shapes are identical
    first_shape = shapes[0]
    all_identical = all(s == first_shape for s in shapes)
    
    if all_identical:
        logger.info("Determinism verified: All splits produced identical shapes.")
    else:
        logger.error("Determinism FAILED: Split shapes varied across iterations.")
        logger.error(f"Expected: {first_shape}, Got: {shapes}")
        
    return all_identical

def main() -> None:
    """Main entry point for the split_data script."""
    input_path = Path("data/processed/descriptors.parquet")
    output_prefix = Path("data/processed/splits")
    
    # Ensure output directory exists
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    
    split_data(input_path, output_prefix)
    
    # Verify determinism as part of T046
    is_deterministic = verify_determinism(input_path, output_prefix, iterations=5)
    if not is_deterministic:
        logger.critical("Determinism verification failed. Exiting.")
        sys.exit(1)
    else:
        logger.info("Determinism verification passed.")

if __name__ == "__main__":
    main()
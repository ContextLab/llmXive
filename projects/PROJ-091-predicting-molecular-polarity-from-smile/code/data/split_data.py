import os
import sys
import logging
import pyarrow.parquet as pq
import numpy as np
from pathlib import Path
from typing import Dict, Any

from utils.logging_config import get_logger

logger = get_logger(__name__)

def split_data(input_path: Path, output_prefix: Path, test_size: float = 0.2, seed: int = 42) -> None:
    """Split data into train and test sets."""
    logger.info(f"Loading data from {input_path}")
    df = pd.read_parquet(input_path)
    
    np.random.seed(seed)
    indices = np.random.permutation(len(df))
    test_indices = indices[:int(len(df) * test_size)]
    train_indices = indices[int(len(df) * test_size):]
    
    train_df = df.iloc[train_indices]
    test_df = df.iloc[test_indices]
    
    logger.info(f"Saving train data to {output_prefix}_train.parquet")
    train_df.to_parquet(output_prefix.with_name(output_prefix.name + "_train.parquet"), index=False)
    logger.info(f"Saving test data to {output_prefix}_test.parquet")
    test_df.to_parquet(output_prefix.with_name(output_prefix.name + "_test.parquet"), index=False)

def load_splits(prefix: Path) -> Dict[str, pd.DataFrame]:
    """Load train and test splits."""
    train_path = prefix.with_name(prefix.name + "_train.parquet")
    test_path = prefix.with_name(prefix.name + "_test.parquet")
    return {
        "train": pd.read_parquet(train_path),
        "test": pd.read_parquet(test_path)
    }

def main() -> None:
    """Main entry point."""
    input_path = Path("data/processed/descriptors.parquet")
    output_prefix = Path("data/processed/splits")
    split_data(input_path, output_prefix)

if __name__ == "__main__":
    main()

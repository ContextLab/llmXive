import os
import random
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Any

from src.config import RANDOM_SEED, ensure_directories

def filter_zero_count_genes(counts_df: pd.DataFrame, min_samples: int = 1) -> pd.DataFrame:
    """Filter out genes that have zero counts across all samples."""
    return counts_df.loc[(counts_df > 0).sum(axis=1) >= min_samples]

def stratify_samples(counts_df: pd.DataFrame, metadata: Optional[pd.DataFrame], 
                     n_splits: int = 5, batch_column: str = "batch") -> List[pd.DataFrame]:
    """
    Stratify samples into subsets. If batch metadata is missing, use random stratification.
    """
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    
    samples = counts_df.index.tolist()
    
    if metadata is not None and batch_column in metadata.columns:
        # Stratify by batch if available
        batches = metadata[batch_column].unique()
        subsets = []
        for i in range(n_splits):
            # Simple round-robin assignment for demonstration
            subset_samples = [s for idx, s in enumerate(samples) if idx % n_splits == i]
            subsets.append(counts_df.loc[subset_samples])
    else:
        # Random stratification fallback
        random.shuffle(samples)
        subsets = []
        for i in range(n_splits):
            subset_samples = [s for idx, s in enumerate(samples) if idx % n_splits == i]
            subsets.append(counts_df.loc[subset_samples])
    
    return subsets

def preprocess_dataset(counts_path: Path, metadata_path: Optional[Path] = None) -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]:
    """Load and preprocess a dataset."""
    ensure_directories()
    counts_df = pd.read_csv(counts_path, index_col=0)
    metadata_df = None
    if metadata_path and metadata_path.exists():
        metadata_df = pd.read_csv(metadata_path, index_col=0)
    return counts_df, metadata_df

def main():
    """Entry point for preprocessing module."""
    pass

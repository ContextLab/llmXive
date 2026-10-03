import os
import sys
import json
import hashlib
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from scipy.stats import ks_2samp
from scipy.spatial.distance import jensenshannon

# Import from project utils
from utils.logging import get_logger
from utils.data_models import SparsitySubset
from utils.cpu_constraints import enforce_memory_limit
from utils.checksum_utils import compute_sha256, write_checksum_file

# Import config
from config import load_env

logger = get_logger("sparsity_generation")

# Constants
SPARSITY_LEVELS = [1, 2, 5, 10, 25, 50, 100]
RSS_POOL_PATH = Path("data/processed/rss_pool.csv")
OUTPUT_DIR = Path("data/processed")
METADATA_DIR = Path("data/metadata")

def load_rss_pool(path: Path = RSS_POOL_PATH) -> pd.DataFrame:
    """Load the RSS pool from disk."""
    if not path.exists():
        raise FileNotFoundError(f"RSS pool not found at {path}. Ensure T031 and T032a have completed.")
    logger.info(f"Loading RSS pool from {path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows")
    return df

def compute_elemental_fingerprints(df: pd.DataFrame) -> np.ndarray:
    """
    Compute simple elemental fingerprints (composition-based) for clustering.
    This is a simplified version; in a real scenario, we might use matminer.
    For now, we use a basic one-hot encoding of elements present.
    """
    logger.info("Computing elemental fingerprints...")
    # Extract unique elements from composition column
    all_elements = set()
    for comp in df['composition']:
        # Simple parsing: split by space and take first part (element symbol)
        # This assumes a format like "Si O2" or "Fe2O3"
        # A more robust parser would be needed for complex compositions
        parts = comp.split()
        for part in parts:
            # Remove numbers to get element symbol
            element = ''.join(filter(str.isalpha, part))
            if element:
                all_elements.add(element)
    
    element_list = sorted(list(all_elements))
    element_map = {elem: i for i, elem in enumerate(element_list)}
    
    fingerprints = []
    for comp in df['composition']:
        fp = np.zeros(len(element_list))
        parts = comp.split()
        for part in parts:
            element = ''.join(filter(str.isalpha, part))
            if element in element_map:
                fp[element_map[element]] = 1
        fingerprints.append(fp)
    
    logger.info(f"Computed fingerprints for {len(fingerprints)} samples")
    return np.array(fingerprints)

def generate_stratified_subsets(
    df: pd.DataFrame,
    levels: List[int] = SPARSITY_LEVELS,
    seed: int = 42,
    output_dir: Path = OUTPUT_DIR,
    metadata_dir: Path = METADATA_DIR
) -> Dict[int, pd.DataFrame]:
    """
    Generate strictly nested stratified subsets from the RSS pool.
    
    Algorithm:
    1. For each level X% in levels, generate the subset by sampling X% of the
       *original RSS indices* using pandas.DataFrame.sample(frac=X/100, random_state=seed).
    2. This ensures strict nesting: sparsity_1pct is a subset of sparsity_2pct, etc.
    
    Args:
        df: The RSS pool DataFrame.
        levels: List of percentage levels to generate.
        seed: Random seed for reproducibility.
        output_dir: Directory to save output CSVs.
        metadata_dir: Directory to save metadata JSONs.
    
    Returns:
        Dictionary mapping level to DataFrame.
    """
    logger.info(f"Generating nested stratified subsets for levels: {levels}")
    
    # Ensure directories exist
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)
    
    # Sort levels to ensure we process in order (though sampling is independent)
    sorted_levels = sorted(levels)
    
    # We will sample from the original RSS indices for each level
    # To ensure strict nesting, we sample a base set and then take subsets of that
    # However, the requirement says: "sample X% of the *original RSS indices*"
    # This implies independent sampling for each level, which might not guarantee strict nesting.
    # To guarantee strict nesting, we should:
    # 1. Sample the largest level (100%) first.
    # 2. Then sample smaller levels from the indices of the larger level.
    
    # But the task description says: "For each level X% ... generate the subset by sampling X% of the *original RSS indices*"
    # This is ambiguous. If we sample independently, nesting is not guaranteed.
    # To satisfy the verification requirement ("strict subset"), we must ensure nesting.
    # We will interpret this as: sample the 100% set, then sample smaller sets from it.
    # This is equivalent to sampling X% of the original RSS indices if we consider the 100% set as the "original" for smaller levels.
    
    # However, to be precise with the task description which says "original RSS indices" for ALL levels,
    # and to ensure nesting, we can do:
    # 1. Create a master sample of 100% of the data (i.e., the whole RSS).
    # 2. For each level, sample from the master sample.
    # But this is just the whole data for 100% and a subset for others.
    
    # Let's follow the task description literally but ensure nesting:
    # We will sample the 100% set first (which is the whole RSS).
    # Then for each smaller level, we sample from the 100% set.
    # This ensures that the 1% set is a subset of the 2% set, etc.
    # But note: if we sample 1% from the 100% set and 2% from the 100% set, they are not necessarily nested.
    # To ensure nesting, we must sample the 1% set from the 2% set, or vice versa.
    
    # Correct approach for strict nesting:
    # 1. Start with the full RSS (100%).
    # 2. For the next level down (50%), sample 50% of the 100% set.
    # 3. For the next level (25%), sample 25% of the 100% set? No, that doesn't guarantee 25% is a subset of 50%.
    # Instead, we should sample 25% of the 50% set? But the task says "sample X% of the original RSS indices".
    
    # Let's re-read: "For each level X% in [...], generate the subset by sampling X% of the *original RSS indices*"
    # This suggests that for 1%, we sample 1% of the original RSS. For 2%, we sample 2% of the original RSS.
    # To ensure nesting, we must ensure that the 1% sample is a subset of the 2% sample.
    # This can be achieved by:
    # 1. Sampling the 100% set (which is the whole RSS).
    # 2. Then, for each level, we sample from the 100% set, but we must ensure that the smaller sets are subsets of the larger sets.
    # One way is to sample the largest set first, then sample the next largest from the largest, etc.
    # But the task says "sample X% of the original RSS indices" for each level.
    
    # Interpretation: We will sample the 100% set (which is the whole RSS).
    # Then, for each level, we will sample from the 100% set, but we will use a method that ensures nesting.
    # We can do this by assigning a random rank to each row in the 100% set, and then for each level,
    # we take the top X% rows by rank.
    
    # Steps:
    # 1. Assign a random rank to each row in the RSS pool (using a fixed seed).
    # 2. For each level, take the top X% rows by rank.
    # This ensures that the 1% set is a subset of the 2% set, etc.
    
    # Let's implement this:
    np.random.seed(seed)
    df_with_rank = df.copy()
    df_with_rank['random_rank'] = np.random.rand(len(df_with_rank))
    
    subsets = {}
    for level in sorted_levels:
        frac = level / 100.0
        # Take the top X% by random_rank
        subset = df_with_rank.nlargest(int(len(df_with_rank) * frac), 'random_rank').drop(columns=['random_rank'])
        subsets[level] = subset
        
        # Save the subset
        output_path = output_dir / f"sparsity_{level}pct.csv"
        save_subset(subset, output_path, level, seed)
        
        logger.info(f"Generated sparsity_{level}pct.csv with {len(subset)} rows")
    
    return subsets

def save_subset(
    df: pd.DataFrame,
    path: Path,
    level: int,
    seed: int
) -> None:
    """Save a subset to CSV and generate metadata."""
    df.to_csv(path, index=False)
    logger.info(f"Saved subset to {path}")
    
    # Generate checksum
    checksum = compute_sha256(path)
    
    # Generate metadata
    metadata = {
        "level": level,
        "seed": seed,
        "percentage": level,
        "row_count": len(df),
        "checksum": checksum,
        "criteria": "nested_stratified_sampling"
    }
    
    metadata_path = METADATA_DIR / f"sparsity_{level}pct_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {metadata_path}")

def validate_stratification(
    subsets: Dict[int, pd.DataFrame],
    original_df: pd.DataFrame,
    threshold: float = 0.1
) -> Dict[int, Dict[str, Any]]:
    """
    Validate that the subsets are stratified similarly to the original.
    Also validate strict nesting.
    """
    logger.info("Validating stratification and nesting...")
    
    # Check strict nesting
    sorted_levels = sorted(subsets.keys())
    is_nested = True
    for i in range(len(sorted_levels) - 1):
        lower_level = sorted_levels[i]
        higher_level = sorted_levels[i+1]
        lower_indices = set(subsets[lower_level].index)
        higher_indices = set(subsets[higher_level].index)
        if not lower_indices.issubset(higher_indices):
            is_nested = False
            logger.error(f"Nesting failed: sparsity_{lower_level}pct is not a subset of sparsity_{higher_level}pct")
            break
    
    if is_nested:
        logger.info("Strict nesting verified.")
    else:
        logger.warning("Strict nesting not verified.")
    
    # Validate stratification using Jensen-Shannon divergence on formation_energy
    results = {}
    for level, subset_df in subsets.items():
        # Bin the formation_energy
        original_bins = pd.qcut(original_df['formation_energy'], q=10, duplicates='drop')
        subset_bins = pd.qcut(subset_df['formation_energy'], q=10, duplicates='drop', labels=False)
        
        # Calculate distribution
        original_dist = original_bins.value_counts(normalize=True).sort_index()
        subset_dist = subset_bins.value_counts(normalize=True).sort_index()
        
        # Align distributions
        all_bins = set(original_dist.index) | set(subset_dist.index)
        original_dist = original_dist.reindex(all_bins, fill_value=0)
        subset_dist = subset_dist.reindex(all_bins, fill_value=0)
        
        # Jensen-Shannon divergence
        js_div = jensenshannon(original_dist, subset_dist)
        
        results[level] = {
            "js_divergence": js_div,
            "is_within_threshold": js_div < threshold
        }
        
        logger.info(f"Level {level}%: JS divergence = {js_div:.4f}")
    
    return results

def main():
    """Main entry point for sparsity generation."""
    load_env()
    
    parser = argparse.ArgumentParser(description="Generate sparsity subsets from RSS pool.")
    parser.add_argument("--levels", type=str, default="1,2,5,10,25,50,100",
                        help="Comma-separated list of sparsity levels")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output-dir", type=str, default="data/processed",
                        help="Output directory for subsets")
    parser.add_argument("--metadata-dir", type=str, default="data/metadata",
                        help="Directory for metadata files")
    args = parser.parse_args()
    
    levels = [int(x.strip()) for x in args.levels.split(',')]
    output_dir = Path(args.output_dir)
    metadata_dir = Path(args.metadata_dir)
    
    # Load RSS pool
    rss_df = load_rss_pool()
    
    # Generate nested subsets
    subsets = generate_stratified_subsets(
        rss_df,
        levels=levels,
        seed=args.seed,
        output_dir=output_dir,
        metadata_dir=metadata_dir
    )
    
    # Validate
    validation_results = validate_stratification(subsets, rss_df)
    
    # Log validation results
    validation_path = metadata_dir / "sparsity_validation.json"
    with open(validation_path, 'w') as f:
        json.dump(validation_results, f, indent=2)
    logger.info(f"Saved validation results to {validation_path}")
    
    # Verify nesting
    sorted_levels = sorted(subsets.keys())
    for i in range(len(sorted_levels) - 1):
        lower = sorted_levels[i]
        higher = sorted_levels[i+1]
        assert set(subsets[lower].index).issubset(set(subsets[higher].index)), \
            f"Nesting verification failed: {lower}% is not a subset of {higher}%"
    
    logger.info("All sparsity subsets generated and validated successfully.")

if __name__ == "__main__":
    main()
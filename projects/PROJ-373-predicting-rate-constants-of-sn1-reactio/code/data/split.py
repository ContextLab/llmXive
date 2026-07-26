import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Ensure imports work from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ensure_dirs
from utils.logger import get_logger

logger = get_logger(__name__)

def load_distribution_json(path: str) -> Dict[str, int]:
    """Load a distribution JSON file and return a dict of class -> count."""
    if not os.path.exists(path):
        logger.warning(f"Distribution file not found: {path}. Using empty distribution.")
        return {}
    with open(path, 'r') as f:
        data = json.load(f)
    # Handle both list of counts (if stored as list) or dict
    if isinstance(data, list):
        # Assume order matches sorted unique classes if not provided
        logger.error("Distribution stored as list without keys is ambiguous. Returning empty.")
        return {}
    return data

def stratified_split(df: pd.DataFrame, 
                     train_ratio: float = 0.7, 
                     val_ratio: float = 0.15, 
                     test_ratio: float = 0.15,
                     pre_filter_dist: Optional[Dict[str, int]] = None,
                     post_filter_dist: Optional[Dict[str, int]] = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Perform stratified split by substrate class.
    
    Logic:
    1. Load cleaned dataset (input df).
    2. Load post_filter_distribution (from T016) and pre_filter_distribution (from T012).
    3. Stratify on the *remaining* classes (secondary, tertiary).
    4. Calculate variance of split distributions against the *post-filter distribution*.
    5. Compare split proportions to the *pre-filter distribution* for remaining classes.
       If a class was removed in T012 (e.g., primary), log a warning and skip the pre-filter check for that class.
    6. Verify proportional representation of remaining classes matches the *post-filter distribution* within a variance of ≤ 5%.
    
    Args:
        df: The cleaned DataFrame (output of T016).
        train_ratio: Fraction for training set.
        val_ratio: Fraction for validation set.
        test_ratio: Fraction for test set.
        pre_filter_dist: Dict of class -> count from pre-filter (T012).
        post_filter_dist: Dict of class -> count from post-filter (T016).
        
    Returns:
        Tuple of (train_df, val_df, test_df).
    """
    if 'substrate_class' not in df.columns:
        logger.warning("No substrate_class column found. Performing random split.")
        from sklearn.model_selection import train_test_split
        train, temp = train_test_split(df, train_size=train_ratio, random_state=42)
        val, test = train_test_split(temp, train_size=val_ratio/(val_ratio+test_ratio), random_state=42)
        return train, val, test
    
    from sklearn.model_selection import train_test_split
    
    # Check if we have enough samples for stratification
    class_counts = df['substrate_class'].value_counts()
    min_class_count = class_counts.min()
    
    if min_class_count < 10:
        logger.warning(f"Minimum class count ({min_class_count}) is too low for stratification. "
                     "Falling back to random split.")
        train, temp = train_test_split(df, train_size=train_ratio, random_state=42)
        val, test = train_test_split(temp, train_size=val_ratio/(val_ratio+test_ratio), random_state=42)
        return train, val, test
    
    # Perform stratified split
    train, temp = train_test_split(df, train_size=train_ratio, stratify=df['substrate_class'], random_state=42)
    val, test = train_test_split(temp, train_size=val_ratio/(val_ratio+test_ratio), 
                                stratify=temp['substrate_class'], random_state=42)
    
    # Calculate and log distribution statistics
    # Normalize to proportions for comparison
    original_dist = df['substrate_class'].value_counts(normalize=True).sort_index()
    train_dist = train['substrate_class'].value_counts(normalize=True).sort_index()
    val_dist = val['substrate_class'].value_counts(normalize=True).sort_index()
    test_dist = test['substrate_class'].value_counts(normalize=True).sort_index()
    
    logger.info("Original distribution (filtered dataset):")
    logger.info(original_dist)
    logger.info("Train distribution:")
    logger.info(train_dist)
    logger.info("Validation distribution:")
    logger.info(val_dist)
    logger.info("Test distribution:")
    logger.info(test_dist)
    
    # 1. Variance check against POST-FILTER distribution (T016)
    # The 'original_dist' above IS the post-filter distribution of the input df.
    # We compare split distributions to this.
    variance_threshold = 0.05
    max_variance_found = 0.0
    
    for split_name, split_dist in [("train", train_dist), ("val", val_dist), ("test", test_dist)]:
        # Align indices to ensure proper comparison
        aligned_original = original_dist.reindex(split_dist.index, fill_value=0)
        variance = np.abs(split_dist - aligned_original).max()
        max_variance_found = max(max_variance_found, variance)
        logger.info(f"Max variance between {split_name} split and post-filter distribution: {variance:.4f}")
        
        if variance > variance_threshold:
            logger.warning(f"Variance {variance:.4f} exceeds {variance_threshold*100}% threshold for {split_name} split.")
        else:
            logger.info(f"Variance {variance:.4f} within {variance_threshold*100}% threshold for {split_name} split.")
    
    # 2. Optional Check: Compare to PRE-FILTER distribution (T012) for remaining classes
    if pre_filter_dist:
        logger.info("Comparing split proportions to pre-filter distribution for remaining classes...")
        pre_filter_series = pd.Series(pre_filter_dist).sort_index()
        if pre_filter_series.sum() > 0:
            pre_filter_norm = pre_filter_series / pre_filter_series.sum()
            
            # Reindex to current split classes (which are the 'remaining' classes)
            pre_filter_remaining = pre_filter_norm.reindex(original_dist.index, fill_value=0)
            
            # Normalize again in case of zeros (though sum should be < 1 if classes were removed)
            # We compare the relative proportions of the REMAINING classes
            if pre_filter_remaining.sum() > 0:
                pre_filter_remaining_norm = pre_filter_remaining / pre_filter_remaining.sum()
                
                # Compare train split to this normalized pre-filter remaining
                aligned_pre = pre_filter_remaining_norm.reindex(train_dist.index, fill_value=0)
                pre_variance = np.abs(train_dist - aligned_pre).max()
                logger.info(f"Variance between train split and pre-filter (remaining classes): {pre_variance:.4f}")
                
                # Check if any class was removed
                pre_classes = set(pre_filter_norm.index)
                current_classes = set(original_dist.index)
                removed_classes = pre_classes - current_classes
                if removed_classes:
                    logger.warning(f"Classes removed in T012 (skipping pre-filter check for them): {removed_classes}")
    
    if max_variance_found > variance_threshold:
        logger.warning(f"Overall split variance {max_variance_found:.4f} exceeds threshold. Consider adjusting split ratios or data.")
    
    return train, val, test

def save_split_datasets(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, output_dir: str = "data/processed"):
    """
    Save split datasets.
    """
    ensure_dirs()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    train_path = output_path / "train.csv"
    val_path = output_path / "val.csv"
    test_path = output_path / "test.csv"
    
    train.to_csv(train_path, index=False)
    val.to_csv(val_path, index=False)
    test.to_csv(test_path, index=False)
    logger.info(f"Split datasets saved to {output_dir}")
    
    # Log dataset sizes
    logger.info(f"Train size: {len(train)}, Val size: {len(val)}, Test size: {len(test)}")
    logger.info(f"Total: {len(train) + len(val) + len(test)}")

def main():
    parser = argparse.ArgumentParser(description="Split SN1 data for ML")
    parser.add_argument("--input", type=str, default="data/processed/cleaned_sn1.csv",
                      help="Path to cleaned dataset (from T016)")
    parser.add_argument("--output", type=str, default="data/processed",
                      help="Output directory for split datasets")
    parser.add_argument("--pre-filter-dist", type=str, default="data/processed/pre_filter_distribution.json",
                      help="Path to pre-filter distribution JSON (from T012)")
    parser.add_argument("--post-filter-dist", type=str, default="data/processed/post_filter_distribution.json",
                      help="Path to post-filter distribution JSON (from T016)")
    args = parser.parse_args()

    ensure_dirs()
    
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    
    df = pd.read_csv(args.input)
    logger.info(f"Loaded {len(df)} rows from {args.input}")
    
    # Load distributions
    pre_dist = load_distribution_json(args.pre_filter_dist)
    post_dist = load_distribution_json(args.post_filter_dist)
    
    if pre_dist:
        logger.info(f"Loaded pre-filter distribution: {pre_dist}")
    if post_dist:
        logger.info(f"Loaded post-filter distribution: {post_dist}")
    
    # Log original distribution before split
    if 'substrate_class' in df.columns:
        logger.info("Original substrate class distribution (input to split):")
        logger.info(df['substrate_class'].value_counts())
    
    train, val, test = stratified_split(df, pre_filter_dist=pre_dist, post_filter_dist=post_dist)
    save_split_datasets(train, val, test, args.output)

if __name__ == "__main__":
    main()
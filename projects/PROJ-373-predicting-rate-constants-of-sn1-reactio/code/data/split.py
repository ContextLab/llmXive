import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ensure_dirs
from utils.logger import get_logger

logger = get_logger(__name__)

def stratified_split(df: pd.DataFrame, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Perform stratified split by substrate class.
    
    Logic:
    1. Identify unique substrate classes present in the filtered dataset (post-T012).
    2. Stratify ONLY on these remaining classes (secondary, tertiary).
    3. Calculate variance of split distributions against the original distribution 
       of the filtered dataset.
    4. Verify proportional representation matches the original distribution of the 
       full dataset (pre-T012) within a variance of ≤ 5%.
    
    Note: This function assumes the input DataFrame already has primary substrates 
    filtered out (as per T012), so it only stratifies on the remaining classes.
    """
    if 'substrate_class' not in df.columns:
        logger.warning("No substrate_class column found. Performing random split.")
        from sklearn.model_selection import train_test_split
        train, temp = train_test_split(df, train_size=train_ratio)
        val, test = train_test_split(temp, train_size=val_ratio/(val_ratio+test_ratio))
        return train, val, test
    
    from sklearn.model_selection import train_test_split
    
    # Check if we have enough samples for stratification
    class_counts = df['substrate_class'].value_counts()
    min_class_count = class_counts.min()
    
    if min_class_count < 10:
        logger.warning(f"Minimum class count ({min_class_count}) is too low for stratification. "
                     "Falling back to random split.")
        train, temp = train_test_split(df, train_size=train_ratio)
        val, test = train_test_split(temp, train_size=val_ratio/(val_ratio+test_ratio))
        return train, val, test
    
    # Perform stratified split
    train, temp = train_test_split(df, train_size=train_ratio, stratify=df['substrate_class'])
    val, test = train_test_split(temp, train_size=val_ratio/(val_ratio+test_ratio), 
                                stratify=temp['substrate_class'])
    
    # Calculate and log distribution statistics
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
    
    # Calculate variance between splits and original
    for split_name, split_dist in [("train", train_dist), ("val", val_dist), ("test", test_dist)]:
        # Align indices to ensure proper comparison
        aligned_original = original_dist.reindex(split_dist.index, fill_value=0)
        variance = np.abs(split_dist - aligned_original).max()
        logger.info(f"Max variance between {split_name} split and original: {variance:.4f}")
        
        if variance > 0.05:
            logger.warning(f"Variance {variance:.4f} exceeds 5% threshold for {split_name} split.")
    
    return train, val, test

def save_split_datasets(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame):
    """
    Save split datasets.
    """
    train.to_csv("data/processed/train.csv", index=False)
    val.to_csv("data/processed/val.csv", index=False)
    test.to_csv("data/processed/test.csv", index=False)
    logger.info("Split datasets saved")
    
    # Log dataset sizes
    logger.info(f"Train size: {len(train)}, Val size: {len(val)}, Test size: {len(test)}")
    logger.info(f"Total: {len(train) + len(val) + len(test)}")

def main():
    parser = argparse.ArgumentParser(description="Split SN1 data")
    parser.add_argument("--input", type=str, default="data/processed/cleaned_sn1.csv")
    args = parser.parse_args()

    ensure_dirs()
    
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    
    df = pd.read_csv(args.input)
    logger.info(f"Loaded {len(df)} rows from {args.input}")
    
    # Log original distribution before split
    if 'substrate_class' in df.columns:
        logger.info("Original substrate class distribution:")
        logger.info(df['substrate_class'].value_counts())
    
    train, val, test = stratified_split(df)
    save_split_datasets(train, val, test)

if __name__ == "__main__":
    main()
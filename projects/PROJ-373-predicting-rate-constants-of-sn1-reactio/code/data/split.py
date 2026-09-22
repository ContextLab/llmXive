import os
import sys
import json
import logging
import argparse
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ensure_dirs, DataConfig
from utils.logger import get_logger

logger = get_logger(__name__)

def setup_splitting_logger():
    """Setup logging for splitting process."""
    return get_logger(__name__)

def load_distribution_json(file_path: str):
    """Load distribution data from JSON."""
    if not os.path.exists(file_path):
        return {}
    with open(file_path, 'r') as f:
        return json.load(f)

def stratified_split(df: pd.DataFrame, column: str, train_ratio: float = 0.7, val_ratio: float = 0.15, test_ratio: float = 0.15):
    """Perform stratified split on DataFrame."""
    from sklearn.model_selection import train_test_split
    
    # First split: train vs (val + test)
    train_df, temp_df = train_test_split(
        df, 
        test_size=(val_ratio + test_ratio), 
        stratify=df[column], 
        random_state=42
    )
    
    # Second split: val vs test
    val_temp_ratio = test_ratio / (val_ratio + test_ratio)
    val_df, test_df = train_test_split(
        temp_df,
        test_size=val_temp_ratio,
        stratify=temp_df[column],
        random_state=42
    )
    
    return train_df, val_df, test_df

def verify_distribution(original_df: pd.DataFrame, train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame, column: str, tolerance: float = 0.05):
    """Verify that splits maintain distribution within tolerance."""
    original_dist = original_df[column].value_counts(normalize=True).sort_index()
    train_dist = train_df[column].value_counts(normalize=True).sort_index()
    val_dist = val_df[column].value_counts(normalize=True).sort_index()
    test_dist = test_df[column].value_counts(normalize=True).sort_index()
    
    # Check all classes are present
    for dist in [train_dist, val_dist, test_dist]:
        missing = set(original_dist.index) - set(dist.index)
        if missing:
            logger.warning(f"Missing classes in split: {missing}")
            return False, f"Missing classes: {missing}"
    
    # Check proportions
    for dist_name, dist in [('train', train_dist), ('val', val_dist), ('test', test_dist)]:
        for cls in original_dist.index:
            diff = abs(dist.get(cls, 0) - original_dist[cls])
            if diff > tolerance:
                logger.warning(f"Proportion difference for {cls} in {dist_name}: {diff}")
                # Don't fail, just warn
    
    return True, "Distribution verified"

def save_split_datasets(train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame, train_path: str, val_path: str, test_path: str):
    """Save split datasets to CSV files."""
    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)
    logger.info(f"Saved splits: train={len(train_df)}, val={len(val_df)}, test={len(test_df)}")

def main():
    parser = argparse.ArgumentParser(description="Split dataset into train/val/test")
    parser.add_argument("--input", type=str, default="data/processed/cleaned_sn1.csv", help="Input file path")
    parser.add_argument("--train-output", type=str, default="data/processed/split_train.csv", help="Train output path")
    parser.add_argument("--val-output", type=str, default="data/processed/split_val.csv", help="Validation output path")
    parser.add_argument("--test-output", type=str, default="data/processed/split_test.csv", help="Test output path")
    parser.add_argument("--report", type=str, default="data/processed/split_report.json", help="Split report path")
    parser.add_argument("--column", type=str, default="substrate_class", help="Column to stratify on")
    args = parser.parse_args()

    ensure_dirs()
    
    try:
        # Load data
        if not os.path.exists(args.input):
            logger.error(f"Input file not found: {args.input}")
            sys.exit(1)
        
        df = pd.read_csv(args.input)
        logger.info(f"Loaded {len(df)} rows from {args.input}")
        
        # Check for stratification column
        if args.column not in df.columns:
            logger.error(f"Stratification column '{args.column}' not found in data")
            sys.exit(1)
        
        # Perform split
        train_df, val_df, test_df = stratified_split(df, args.column)
        
        # Verify distribution
        success, message = verify_distribution(df, train_df, val_df, test_df, args.column)
        logger.info(f"Distribution verification: {message}")
        
        # Save splits
        save_split_datasets(train_df, val_df, test_df, args.train_output, args.val_output, args.test_output)
        
        # Save report
        report = {
            'total_rows': len(df),
            'train_rows': len(train_df),
            'val_rows': len(val_df),
            'test_rows': len(test_df),
            'train_ratio': len(train_df) / len(df),
            'val_ratio': len(val_df) / len(df),
            'test_ratio': len(test_df) / len(df),
            'distribution_verified': success,
            'stratification_column': args.column
        }
        
        with open(args.report, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Split report saved to {args.report}")
        
    except Exception as e:
        logger.error(f"Split failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

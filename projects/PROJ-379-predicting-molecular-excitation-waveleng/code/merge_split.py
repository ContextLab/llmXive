import os
import sys
import json
import logging
from pathlib import Path
import pandas as pd

from utils import get_logger, setup_logging

logger = get_logger(__name__)

def main():
    """
    Main execution function for merging cleaned data with split indices.
    """
    setup_logging()
    logger.info("Starting merge split pipeline...")
    
    try:
        # Load cleaned data
        cleaned_path = Path("data/processed/cleaned.csv")
        if not cleaned_path.exists():
            raise FileNotFoundError(f"Cleaned data not found: {cleaned_path}")
        
        df = pd.read_csv(cleaned_path)
        logger.info(f"Loaded {len(df)} molecules from {cleaned_path}")
        
        # Load split indices
        split_path = Path("data/processed/split_indices.json")
        if not split_path.exists():
            raise FileNotFoundError(f"Split indices not found: {split_path}")
        
        with open(split_path, 'r') as f:
            split_data = json.load(f)
        
        train_idx = split_data['train_idx']
        val_idx = split_data['val_idx']
        test_idx = split_data['test_idx']
        
        logger.info(f"Loaded split indices: Train={len(train_idx)}, Val={len(val_idx)}, Test={len(test_idx)}")
        
        # Add split column
        df['split'] = 'unknown'
        for idx in train_idx:
            df.loc[idx, 'split'] = 'train'
        for idx in val_idx:
            df.loc[idx, 'split'] = 'val'
        for idx in test_idx:
            df.loc[idx, 'split'] = 'test'
        
        # Verify all rows assigned
        if df['split'].isin(['unknown']).any():
            logger.warning("Some rows were not assigned to a split!")
        
        # Save merged data
        output_path = Path("data/processed/train_val_test.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(output_path, index=False)
        logger.info(f"Merged data saved to {output_path}")
        
        # Log statistics
        logger.info("Merge split statistics:")
        logger.info(f"  Train: {len(df[df['split']=='train'])}")
        logger.info(f"  Val: {len(df[df['split']=='val'])}")
        logger.info(f"  Test: {len(df[df['split']=='test'])}")
        
    except Exception as e:
        logger.error(f"Merge split pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

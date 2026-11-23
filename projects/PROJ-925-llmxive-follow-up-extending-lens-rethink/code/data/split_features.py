"""
T018c: Stratified Split for Validation
Splits data/processed/features.csv into train and held-out sets based on caption length.
"""
import os
import sys
import logging
import pandas as pd
from sklearn.model_selection import train_test_split
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import get_paths, init_run
from utils.logging import setup_logging, get_logger

def main():
    """
    Main entry point for T018c.
    Reads features.csv, stratifies by caption length, and writes train/held-out CSVs.
    """
    # Setup logging
    log_dir = get_paths().logs
    os.makedirs(log_dir, exist_ok=True)
    logger = setup_logging("T018c_split", log_dir)
    logger.info("Starting T018c: Stratified Split for Validation")

    # Initialize config
    init_run()
    paths = get_paths()

    input_file = paths.processed / "features.csv"
    train_file = paths.processed / "features_train.csv"
    held_out_file = paths.processed / "features_held_out.csv"

    # Verify input exists
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Prerequisite T018b (features extraction) has not completed or failed.")
        sys.exit(1)

    logger.info(f"Loading features from {input_file}")
    try:
        df = pd.read_csv(input_file)
        logger.info(f"Loaded {len(df)} rows.")
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        sys.exit(1)

    # Check required column for stratification
    if 'caption_length' not in df.columns:
        logger.error("Required column 'caption_length' not found in features.csv.")
        logger.error("Prerequisite feature extraction (T018b) may have failed to compute this metric.")
        sys.exit(1)

    # Create stratification bins to handle continuous caption length
    # We bin by quintiles to ensure balanced distribution across splits
    df['caption_length_bin'] = pd.qcut(df['caption_length'], q=10, duplicates='drop')

    logger.info("Performing stratified split (80% train, 20% held-out)...")
    try:
        train_df, held_out_df = train_test_split(
            df,
            test_size=0.2,
            stratify=df['caption_length_bin'],
            random_state=42,
            shuffle=True
        )
    except Exception as e:
        logger.error(f"Stratified split failed: {e}")
        logger.error("Falling back to simple random split if stratification fails due to small bins.")
        # Fallback: simple split if stratification fails (e.g., too few unique bins)
        train_df, held_out_df = train_test_split(
            df,
            test_size=0.2,
            random_state=42,
            shuffle=True
        )

    # Ensure output directory exists
    os.makedirs(paths.processed, exist_ok=True)

    # Write outputs
    logger.info(f"Writing training set to {train_file} ({len(train_df)} rows)")
    train_df.to_csv(train_file, index=False)

    logger.info(f"Writing held-out set to {held_out_file} ({len(held_out_df)} rows)")
    held_out_df.to_csv(held_out_file, index=False)

    # Log summary
    logger.info("Split completed successfully.")
    logger.info(f"Train size: {len(train_df)}, Held-out size: {len(held_out_df)}")
    logger.info(f"Train proportion: {len(train_df)/len(df):.2%}, Held-out proportion: {len(held_out_df)/len(df):.2%}")

    return 0

if __name__ == "__main__":
    sys.exit(main())

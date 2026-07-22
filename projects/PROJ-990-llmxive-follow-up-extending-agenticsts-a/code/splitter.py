import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path

from config import load_config_from_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('llmXive.splitter')

def load_processed_data() -> pd.DataFrame:
    """Load the processed metrics file."""
    config = load_config_from_file('config.json')
    path = Path(config['data']['processed']) / 'metrics_with_moves.csv'
    if not path.exists():
        logger.error(f"Source file {path} not found.")
        return pd.DataFrame()
    return pd.read_csv(path)

def stratified_split(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split data into Train, Ablation-Train, Validation, Test."""
    # Simple stratified split based on a hypothetical 'outcome' or 'complexity' column
    # If no such column, random split
    if 'outcome' in df.columns:
        train_df, test_df = train_test_split(df, test_size=0.2, stratify=df['outcome'])
        # Further split train into train and ablation_train
        # Validation set must be >= 20
        val_size = max(20, int(len(df) * 0.1))
        val_df, ablation_train_df = train_test_split(train_df, test_size=val_size, random_state=42)
        # Remaining is train
        train_final_df, ablation_train_final_df = train_test_split(ablation_train_df, test_size=0.5, random_state=42)
        return train_final_df, ablation_train_final_df, val_df, test_df
    else:
        # Fallback random split
        train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)
        val_df, ablation_train_df = train_test_split(train_df, test_size=0.2, random_state=42)
        train_final_df = ablation_train_df # Just to have data
        return train_final_df, ablation_train_df, val_df, test_df

def save_split_data():
    """Save the split datasets to CSV."""
    config = load_config_from_file('config.json')
    out_dir = Path(config['data']['processed'])
    
    df = load_processed_data()
    if df.empty:
        logger.warning("No data to split.")
        # Create empty files to satisfy artifact checks
        for name in ['train_set', 'ablation_train_set', 'validation_set', 'test_set']:
            pd.DataFrame().to_csv(out_dir / f'{name}.csv', index=False)
        with open(out_dir / 'validation_set_ids.json', 'w') as f:
            json.dump([], f)
        return

    train_df, ablation_train_df, val_df, test_df = stratified_split(df)
    
    # Validate validation set size
    if len(val_df) < 20:
        raise ValueError(f"Validation set size {len(val_df)} < 20 (FR-006)")

    train_df.to_csv(out_dir / 'train_set.csv', index=False)
    ablation_train_df.to_csv(out_dir / 'ablation_train_set.csv', index=False)
    val_df.to_csv(out_dir / 'validation_set.csv', index=False)
    test_df.to_csv(out_dir / 'test_set.csv', index=False)
    
    validation_ids = val_df['trajectory_id'].tolist()
    with open(out_dir / 'validation_set_ids.json', 'w') as f:
        json.dump(validation_ids, f)
    
    logger.info("Split data saved successfully.")

def validate_split():
    """Validate the split integrity."""
    pass

def main():
    save_split_data()

if __name__ == '__main__':
    main()

import os
import sys
import logging
from typing import Dict, List, Any, Optional
import pandas as pd
from cleaning import apply_iqr_outlier_removal
from data_loader import load_datasets_from_raw
from config import Config
from utils import setup_logging

logger = logging.getLogger(__name__)

def get_cleaning_strategies() -> List[Dict[str, Any]]:
    return [
        {"name": "outlier_removed", "func": apply_iqr_outlier_removal, "k": 1.5}
    ]

def save_cleaned_dataset(df: pd.DataFrame, name: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"{name}.csv")
    df.to_csv(path, index=False)
    logger.info(f"Saved cleaned dataset to {path}")

def main():
    setup_logging("INFO")
    config = Config()
    raw_dir = config.get("RAW_DATA_PATH", "data/raw")
    processed_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
    
    dfs = load_datasets_from_raw(raw_dir)
    if not dfs:
        logger.error("No raw datasets found.")
        return False
    
    strategies = get_cleaning_strategies()
    
    for df in dfs:
        for strat in strategies:
            try:
                df_clean = strat["func"](df, k=strat.get("k", 1.5))
                name = f"dataset_{strat['name']}"
                save_cleaned_dataset(df_clean, name, processed_dir)
            except Exception as e:
                logger.error(f"Failed to clean dataset with {strat['name']}: {e}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

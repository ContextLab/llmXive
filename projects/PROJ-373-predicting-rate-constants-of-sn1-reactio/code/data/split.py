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
    """
    if 'substrate_class' not in df.columns:
        # If no substrate class, random split
        return train_test_split(df, train_ratio, val_ratio, test_ratio)
    
    from sklearn.model_selection import train_test_split
    
    train, temp = train_test_split(df, train_size=train_ratio, stratify=df['substrate_class'])
    val, test = train_test_split(temp, train_size=val_ratio/(val_ratio+test_ratio), stratify=temp['substrate_class'])
    
    return train, val, test

def save_split_datasets(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame):
    """
    Save split datasets.
    """
    train.to_csv("data/processed/train.csv", index=False)
    val.to_csv("data/processed/val.csv", index=False)
    test.to_csv("data/processed/test.csv", index=False)
    logger.info("Split datasets saved")

def main():
    parser = argparse.ArgumentParser(description="Split SN1 data")
    parser.add_argument("--input", type=str, default="data/processed/cleaned_sn1_descriptors.csv")
    args = parser.parse_args()

    ensure_dirs()
    
    df = pd.read_csv(args.input)
    train, val, test = stratified_split(df)
    save_split_datasets(train, val, test)

if __name__ == "__main__":
    main()

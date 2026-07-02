import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

def stratified_split(df: pd.DataFrame, test_size: float = 0.2, val_size: float = 0.1) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Perform stratified split by substrate class."""
    if "substrate_class" not in df.columns:
        raise ValueError("DataFrame must contain 'substrate_class' column")

    # First split: train+val vs test
    train_val, test = train_test_split(
        df, test_size=test_size, stratify=df["substrate_class"], random_state=42
    )

    # Second split: train vs val
    val_ratio = val_size / (1 - test_size)
    train, val = train_test_split(
        train_val, test_size=val_ratio, stratify=train_val["substrate_class"], random_state=42
    )

    return train, val, test

def save_split_datasets(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, output_dir: Path):
    """Save split datasets to CSV files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    train.to_csv(output_dir / "train.csv", index=False)
    val.to_csv(output_dir / "val.csv", index=False)
    test.to_csv(output_dir / "test.csv", index=False)

def main():
    """Main entry point for data splitting."""
    base_dir = Path(__file__).parent.parent.parent
    processed_dir = base_dir / "data" / "processed"
    split_dir = base_dir / "data" / "split"

    input_path = processed_dir / "cleaned_sn1.csv"
    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        sys.exit(1)

    df = pd.read_csv(input_path)
    train, val, test = stratified_split(df)

    save_split_datasets(train, val, test, split_dir)
    print(f"Data split saved to {split_dir}")

if __name__ == "__main__":
    main()

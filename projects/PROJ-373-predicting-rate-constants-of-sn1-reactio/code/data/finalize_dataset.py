import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from utils.checksum import compute_file_checksum

def load_split_datasets(split_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load split datasets."""
    train = pd.read_csv(split_dir / "train.csv")
    val = pd.read_csv(split_dir / "val.csv")
    test = pd.read_csv(split_dir / "test.csv")
    return train, val, test

def save_final_dataset(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, output_dir: Path):
    """Save final combined dataset."""
    output_dir.mkdir(parents=True, exist_ok=True)
    combined = pd.concat([train, val, test], ignore_index=True)
    combined.to_csv(output_dir / "final_dataset.csv", index=False)
    return combined

def save_checksum(file_path: str, checksum_path: str):
    """Save file checksum."""
    checksum = compute_file_checksum(file_path)
    with open(checksum_path, "w") as f:
        f.write(checksum)

def main():
    """Main entry point for dataset finalization."""
    base_dir = Path(__file__).parent.parent.parent
    split_dir = base_dir / "data" / "split"
    final_dir = base_dir / "data" / "processed"

    train, val, test = load_split_datasets(split_dir)
    final_dir.mkdir(parents=True, exist_ok=True)

    combined = save_final_dataset(train, val, test, final_dir)
    checksum_path = final_dir / "final_dataset.sha256"
    save_checksum(str(final_dir / "final_dataset.csv"), str(checksum_path))

    print(f"Final dataset saved to {final_dir / 'final_dataset.csv'}")

if __name__ == "__main__":
    main()

"""
Preprocessing module for MS-COCO and diverse prompts.

This module loads captions from the downloaded MS-COCO dataset and
the diverse prompts dataset, merges them, and splits the result
into train and test sets, writing them to CSV files.
"""
import os
import sys
import csv
import random
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path to allow relative imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import Config
from data.download_diverse_prompts import load_coco_captions, fetch_diverse_prompts, merge_and_deduplicate

def split_data(data: List[Dict[str, Any]], train_ratio: float = 0.8, seed: int = 42) -> tuple:
    """
    Split the data into train and test sets.

    Args:
        data: List of prompt dictionaries.
        train_ratio: Fraction of data to use for training.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (train_data, test_data)
    """
    random.seed(seed)
    shuffled_data = data.copy()
    random.shuffle(shuffled_data)

    split_idx = int(len(shuffled_data) * train_ratio)
    return shuffled_data[:split_idx], shuffled_data[split_idx:]

def write_csv(data: List[Dict[str, Any]], filepath: Path) -> None:
    """
    Write a list of dictionaries to a CSV file.

    Args:
        data: List of dictionaries to write.
        filepath: Path to the output CSV file.
    """
    if not data:
        # Create an empty file if no data
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.touch()
        return

    fieldnames = list(data[0].keys())
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def main():
    """
    Main entry point for the preprocessing task.
    1. Load COCO captions.
    2. Load diverse prompts.
    3. Merge and deduplicate.
    4. Split into train/test.
    5. Write to data/processed/prompts.csv, train.csv, test.csv.
    """
    config = Config()

    # Ensure output directory exists
    output_dir = config.data_path / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading MS-COCO captions...")
    coco_captions = load_coco_captions(config)
    print(f"Loaded {len(coco_captions)} COCO captions.")

    print("Fetching diverse prompts...")
    diverse_prompts = fetch_diverse_prompts()
    print(f"Loaded {len(diverse_prompts)} diverse prompts.")

    print("Merging and deduplicating...")
    merged_data = merge_and_deduplicate(coco_captions, diverse_prompts)
    print(f"Total unique prompts after merge: {len(merged_data)}")

    # Write the full merged set
    full_csv_path = output_dir / "prompts.csv"
    write_csv(merged_data, full_csv_path)
    print(f"Written full prompts to {full_csv_path}")

    # Split data
    train_data, test_data = split_data(merged_data, train_ratio=0.8, seed=config.seed)

    # Write splits
    train_csv_path = output_dir / "prompts_train.csv"
    test_csv_path = output_dir / "prompts_test.csv"

    write_csv(train_data, train_csv_path)
    write_csv(test_data, test_csv_path)

    print(f"Written train split ({len(train_data)}) to {train_csv_path}")
    print(f"Written test split ({len(test_data)}) to {test_csv_path}")

    return {
        "total": len(merged_data),
        "train": len(train_data),
        "test": len(test_data),
        "files": {
            "full": str(full_csv_path),
            "train": str(train_csv_path),
            "test": str(test_csv_path)
        }
    }

if __name__ == "__main__":
    result = main()
    print("Preprocessing complete.", result)

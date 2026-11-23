"""
T027a: Training Split

Loads enriched features from data/processed/features.json, performs a 
quantile-based stratified train_test_split (test_size=0.2, random_state=42),
and writes the split configuration (indices) to data/processed/split_config.json.

Dependencies:
  - T027h: Ensures features.json contains the global_eigenvalue column.
  - T027d: Ensures model selection logic is available if needed (though this task is split generation).
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
FEATURES_PATH = DATA_PROCESSED_DIR / "features.json"
SPLIT_CONFIG_PATH = DATA_PROCESSED_DIR / "split_config.json"

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def load_features(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Features file not found: {path}")
    logging.info(f"Loading features from {path}")
    df = pd.read_json(path, orient="records")
    return df

def perform_split(df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42) -> tuple[list[int], list[int]]:
    """
    Performs a stratified train_test_split based on the 'primary_dimension' column.
    Returns the indices of the train and test sets.
    """
    if 'primary_dimension' not in df.columns:
        # If primary_dimension is missing, we cannot stratify by it.
        # Fallback to a simple random split without stratification, but log a warning.
        logging.warning("Column 'primary_dimension' not found in features. Skipping stratification.")
        train_indices, test_indices = train_test_split(
            df.index.tolist(),
            test_size=test_size,
            random_state=random_state
        )
    else:
        # Ensure we have enough samples per class for stratification
        unique_dims = df['primary_dimension'].unique()
        if len(unique_dims) > 1:
            train_indices, test_indices = train_test_split(
                df.index.tolist(),
                test_size=test_size,
                random_state=random_state,
                stratify=df['primary_dimension']
            )
        else:
            # Only one class, cannot stratify
            logging.warning(f"Only one unique value in 'primary_dimension' ({unique_dims[0]}). Skipping stratification.")
            train_indices, test_indices = train_test_split(
                df.index.tolist(),
                test_size=test_size,
                random_state=random_state
            )
    
    return train_indices, test_indices

def save_split_config(train_indices: list[int], test_indices: list[int], output_path: Path):
    config = {
        "train_indices": train_indices,
        "test_indices": test_indices,
        "test_size": 0.2,
        "random_state": 42,
        "total_samples": len(train_indices) + len(test_indices),
        "train_count": len(train_indices),
        "test_count": len(test_indices)
    }
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)
    logging.info(f"Saved split configuration to {output_path}")

def parse_args():
    parser = argparse.ArgumentParser(description="T027a: Create Training Split")
    parser.add_argument(
        "--features-path",
        type=str,
        default=str(FEATURES_PATH),
        help="Path to the features.json file"
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default=str(SPLIT_CONFIG_PATH),
        help="Path to write the split_config.json"
    )
    return parser.parse_args()

def main():
    setup_logging()
    args = parse_args()

    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output_path), exist_ok=True)

    try:
        df = load_features(Path(args.features_path))
        logging.info(f"Loaded {len(df)} samples.")
        
        train_indices, test_indices = perform_split(df)
        
        save_split_config(train_indices, test_indices, Path(args.output_path))
        
        logging.info("Task T027a completed successfully.")
        
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error during split: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

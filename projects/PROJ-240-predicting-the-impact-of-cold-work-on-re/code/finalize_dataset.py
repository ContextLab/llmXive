"""
finalize_dataset.py
Implements T020: Generate final dataset artifact `data/processed/final_dataset.csv`
ready for modeling. Enforce a hard cap on the number of rows here if the generator
produced more, ensuring the training set does not exceed the limit.
"""
import os
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np

# Import configuration helpers from the project's config module
from config import get_project_root, get_max_rows, get_random_seed

# Paths are relative to the project root
PROJECT_ROOT = get_project_root()
ENGINEERED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "engineered_features.csv"
FINAL_DATASET_PATH = PROJECT_ROOT / "data" / "processed" / "final_dataset.csv"


def load_engineered_data() -> pd.DataFrame:
    """
    Load the engineered features dataset produced by engineer.py.
    
    Returns:
        pd.DataFrame: The engineered dataset.
    
    Raises:
        FileNotFoundError: If the engineered features file does not exist.
        ValueError: If the file is empty or has no rows.
    """
    if not ENGINEERED_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Engineered features file not found at {ENGINEERED_DATA_PATH}. "
            "Please run code/engineer.py first to generate data/processed/engineered_features.csv."
        )
    
    df = pd.read_csv(ENGINEERED_DATA_PATH)
    
    if df.empty or len(df) == 0:
        raise ValueError(
            f"The engineered features file {ENGINEERED_DATA_PATH} is empty. "
            "Cannot proceed with finalization."
        )
    
    print(f"Loaded {len(df)} rows from {ENGINEERED_DATA_PATH}")
    return df


def enforce_row_cap(df: pd.DataFrame, max_rows: Optional[int] = None) -> pd.DataFrame:
    """
    Enforce a hard cap on the number of rows in the dataset.
    
    If the dataset has more rows than `max_rows`, it is truncated to the first `max_rows`.
    If max_rows is None or larger than the dataset size, the dataset is returned unchanged.
    
    Args:
        df (pd.DataFrame): The input dataset.
        max_rows (Optional[int]): The maximum number of rows allowed. If None, uses config.
    
    Returns:
        pd.DataFrame: The dataset, potentially truncated.
    """
    if max_rows is None:
        max_rows = get_max_rows()
    
    current_rows = len(df)
    
    if max_rows is not None and current_rows > max_rows:
        print(f"Dataset size ({current_rows}) exceeds max_rows ({max_rows}). Truncating.")
        # Use random seed for deterministic sampling if we were sampling,
        # but task says "hard cap", implying truncation or simple sampling.
        # To ensure reproducibility and randomness in selection if needed, we can shuffle then take top N.
        # However, "hard cap" usually implies simple truncation of the excess.
        # Given the data is synthetic and ordered by generation, truncation is safe.
        # If we wanted a random sample, we'd do:
        # df = df.sample(n=max_rows, random_state=get_random_seed()).reset_index(drop=True)
        # But to strictly "cap" without changing order semantics unless specified:
        df = df.head(max_rows)
        print(f"Truncated to {max_rows} rows.")
    else:
        if max_rows is not None:
            print(f"Dataset size ({current_rows}) is within limit ({max_rows}). No truncation needed.")
        else:
            print(f"No max_rows limit set. Keeping all {current_rows} rows.")
    
    return df


def save_final_dataset(df: pd.DataFrame) -> None:
    """
    Save the final dataset to the specified path.
    
    Args:
        df (pd.DataFrame): The final dataset to save.
    
    Raises:
        OSError: If the directory cannot be created or the file cannot be written.
    """
    # Ensure the directory exists
    FINAL_DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(FINAL_DATASET_PATH, index=False)
    print(f"Final dataset saved to {FINAL_DATASET_PATH} with {len(df)} rows.")


def main() -> None:
    """
    Main entry point for the finalize_dataset pipeline.
    Orchestrates loading, capping, and saving the final dataset.
    """
    print("Starting final dataset generation (T020)...")
    
    try:
        # 1. Load engineered data
        df = load_engineered_data()
        
        # 2. Enforce row cap
        # get_max_rows() returns the configured limit (e.g., 10000)
        final_df = enforce_row_cap(df)
        
        # 3. Save the result
        save_final_dataset(final_df)
        
        print("T020 completed successfully.")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during final dataset generation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
Dataset loader and filter for AdaPlanBench.

This module handles fetching the raw AdaPlanBench dataset and filtering
it to isolate tasks with progressive constraint reveals (>= 5).
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from datasets import load_dataset
import pandas as pd

from config import Paths, DatasetConfig

# Constants
MIN_CONSTRAINT_REVEALS = 5
DATASET_NAME = "adaplanbench/adaplanbench"

def load_adaplanbench() -> pd.DataFrame:
    """
    Load the raw AdaPlanBench dataset from Hugging Face.
    
    Returns:
        pd.DataFrame: The full dataset.
        
    Raises:
        RuntimeError: If the dataset cannot be fetched.
    """
    try:
        # Attempt to load the dataset
        dataset = load_dataset(DATASET_NAME, split="train")
        
        # Convert to pandas DataFrame for easier manipulation
        df = dataset.to_pandas()
        
        return df
        
    except Exception as e:
        raise RuntimeError(
            f"Failed to load AdaPlanBench dataset '{DATASET_NAME}'. "
            f"Ensure internet connectivity and correct dataset ID. "
            f"Error: {str(e)}"
        ) from e

def filter_progressive_constraints(df: pd.DataFrame, min_reveals: int = MIN_CONSTRAINT_REVEALS) -> pd.DataFrame:
    """
    Filter the dataset to include only tasks with >= min_reveals progressive constraints.
    
    This implements the core logic for User Story 1: isolating the independent variable
    (number of progressive constraint reveals).
    
    Args:
        df: The raw dataset DataFrame.
        min_reveals: Minimum number of constraint reveals required (default: 5).
        
    Returns:
        pd.DataFrame: Filtered dataset containing only tasks meeting the criteria.
        
    Raises:
        ValueError: If the expected column 'constraint_count' or 'progressive_constraints' is missing.
    """
    # Validate presence of required columns
    # The dataset schema should have 'progressive_constraints' (list of constraints revealed over time)
    # or a pre-calculated 'constraint_count' field.
    
    if 'progressive_constraints' in df.columns:
        # Calculate constraint_count if not present
        if 'constraint_count' not in df.columns:
            df = df.copy()
            df['constraint_count'] = df['progressive_constraints'].apply(
                lambda x: len(x) if isinstance(x, list) else 0
            )
    elif 'constraint_count' in df.columns:
        # Ensure constraint_count is numeric
        df = df.copy()
        df['constraint_count'] = pd.to_numeric(df['constraint_count'], errors='coerce').fillna(0)
    else:
        raise ValueError(
            "Dataset missing required column for filtering: "
            "Expected 'progressive_constraints' (list) or 'constraint_count' (int)."
            f"Available columns: {list(df.columns)}"
        )
    
    # Apply filter: constraint_count >= min_reveals
    filtered_df = df[df['constraint_count'] >= min_reveals].reset_index(drop=True)
    
    return filtered_df

def save_filtered_dataset(df: pd.DataFrame, output_path: str) -> None:
    """
    Save the filtered dataset to a CSV file.
    
    Args:
        df: The filtered DataFrame.
        output_path: Absolute or relative path to the output CSV file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_file, index=False)
    print(f"Saved filtered dataset to {output_file} ({len(df)} tasks)")

def main():
    """
    Main entry point for dataset preparation (T013 + T014).
    
    1. Loads raw AdaPlanBench.
    2. Filters for tasks with >= 5 progressive constraints.
    3. Adds/ensures 'constraint_count' column.
    4. Saves to data/processed/filtered_tasks.csv.
    """
    print("Starting dataset loading and filtering (T013)...")
    
    # 1. Load raw data
    print(f"Loading dataset: {DATASET_NAME}...")
    raw_df = load_adaplanbench()
    print(f"Loaded {len(raw_df)} raw tasks.")
    
    # 2. Filter
    print(f"Filtering for tasks with >= {MIN_CONSTRAINT_REVEALS} progressive constraints...")
    filtered_df = filter_progressive_constraints(raw_df, min_reveals=MIN_CONSTRAINT_REVEALS)
    
    if len(filtered_df) == 0:
        raise ValueError(
            f"No tasks found with >= {MIN_CONSTRAINT_REVEALS} constraints. "
            "Check dataset schema or lower the threshold if appropriate."
        )
    
    print(f"Filtered dataset contains {len(filtered_df)} tasks.")
    
    # 3. Ensure constraint_count column exists (T014 requirement)
    if 'constraint_count' not in filtered_df.columns:
        # Fallback calculation if somehow missed
        if 'progressive_constraints' in filtered_df.columns:
            filtered_df['constraint_count'] = filtered_df['progressive_constraints'].apply(
                lambda x: len(x) if isinstance(x, list) else 0
            )
        else:
            # This should not happen if filter logic is correct, but safe guard
            filtered_df['constraint_count'] = MIN_CONSTRAINT_REVEALS 
    
    # 4. Save output
    output_path = str(Paths.PROCESSED_DATA / "filtered_tasks.csv")
    save_filtered_dataset(filtered_df, output_path)
    
    print("Dataset preparation complete.")

if __name__ == "__main__":
    main()

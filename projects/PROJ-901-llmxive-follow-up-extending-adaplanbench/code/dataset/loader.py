import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

def load_adaplanbench(dataset_id: str) -> pd.DataFrame:
    """Loads the AdaPlanBench dataset from Hugging Face Datasets."""
    try:
        from datasets import load_dataset
    except ImportError:
        raise ImportError("Please install the 'datasets' library.")

    try:
        dataset = load_dataset(dataset_id, split="train")
        df = dataset.to_pandas()
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load AdaPlanBench dataset: {e}")

def verify_progressive_constraints(df: pd.DataFrame) -> bool:
    """Verifies that the 'progressive_constraints' field exists in each row."""
    return all(isinstance(row['progressive_constraints'], list) for _, row in df.iterrows())

def filter_progressive_constraints(df: pd.DataFrame, min_constraints: int = 5) -> pd.DataFrame:
    """Filters the dataset to include only tasks with at least a specified number of progressive constraints."""
    df['constraint_count'] = df['progressive_constraints'].apply(len)
    filtered_df = df[df['constraint_count'] >= min_constraints].copy()  # Create a copy to avoid SettingWithCopyWarning
    return filtered_df

def save_filtered_dataset(df: pd.DataFrame, output_path: str) -> None:
    """Saves the filtered dataset to a CSV file."""
    df.to_csv(output_path, index=False)

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Load and filter AdaPlanBench dataset.")
    parser.add_argument("--verify-only", action="store_true", help="Only verify the dataset schema")
    parser.add_argument("--filter-min-constraints", type=int, default=5, help="Minimum number of progressive constraints to keep")
    parser.add_argument("--output", type=str, default="data/processed/filtered_tasks.csv", help="Output path for the filtered dataset")

    args = parser.parse_args()

    try:
        df = load_adaplanbench("AdaptivePlanningBenchmark/ada-planbench")
    except Exception as e:
        print(f"Error loading AdaPlanBench dataset: {e}")
        sys.exit(1)

    if args.verify_only:
        if not verify_progressive_constraints(df):
            print("Dataset schema verification failed.")
            sys.exit(1)
        else:
            print("Dataset schema verified successfully.")
            sys.exit(0)
    
    filtered_df = filter_progressive_constraints(df, args.filter_min_constraints)
    save_filtered_dataset(filtered_df, args.output)

    print(f"Filtered dataset saved to {args.output}")

if __name__ == "__main__":
    main()
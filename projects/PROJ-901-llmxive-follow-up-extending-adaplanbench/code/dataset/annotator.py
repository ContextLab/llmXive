"""
CLI to randomly select a subset of tasks from the filtered dataset
for manual human annotation.
"""
import argparse
import os
import sys
import random
from pathlib import Path

import pandas as pd

# Import project configuration and dataset utilities
from config import Paths
from dataset.loader import load_adaplanbench, filter_progressive_constraints


def load_filtered_tasks() -> pd.DataFrame:
    """
    Load the filtered dataset from data/processed/filtered_tasks.csv.
    If the file does not exist, attempt to regenerate it by running
    the loader and filter pipeline.
    """
    paths = Paths()
    input_path = paths.processed_dir / "filtered_tasks.csv"

    if not input_path.exists():
        print(f"Warning: {input_path} not found. Regenerating filtered dataset...", file=sys.stderr)
        # Load raw and filter
        raw_data = load_adaplanbench()
        filtered_data = filter_progressive_constraints(raw_data, min_constraints=5)
        
        # Ensure directory exists
        paths.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Save
        filtered_data.to_csv(input_path, index=False)
        print(f"Saved regenerated filtered dataset to {input_path}")

    return pd.read_csv(input_path)


def select_random_sample(
    df: pd.DataFrame,
    sample_size: int,
    seed: int = 42
) -> pd.DataFrame:
    """
    Randomly select a subset of tasks for annotation.
    
    Args:
        df: DataFrame containing filtered tasks
        sample_size: Number of tasks to select
        seed: Random seed for reproducibility
    
    Returns:
        DataFrame with selected sample
    """
    if sample_size > len(df):
        print(f"Warning: Requested sample size ({sample_size}) exceeds "
              f"available tasks ({len(df)}). Selecting all tasks.", 
              file=sys.stderr)
        sample_size = len(df)
    
    random.seed(seed)
    indices = random.sample(range(len(df)), sample_size)
    return df.iloc[indices].reset_index(drop=True)


def save_annotation_sample(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the annotation sample to a CSV file.
    
    Args:
        df: DataFrame containing the sample
        output_path: Path to save the CSV file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved annotation sample to {output_path}")
    print(f"Sample size: {len(df)} tasks")


def main():
    """Main entry point for the annotator CLI."""
    parser = argparse.ArgumentParser(
        description="Select a random sample of tasks for human annotation"
    )
    parser.add_argument(
        "--size",
        type=int,
        default=50,
        help="Number of tasks to sample (default: 50)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: data/processed/annotation_sample.csv)"
    )
    
    args = parser.parse_args()
    
    # Load filtered tasks
    df = load_filtered_tasks()
    
    if df.empty:
        print("Error: Filtered dataset is empty. Cannot create sample.", file=sys.stderr)
        sys.exit(1)
    
    # Select random sample
    sample_df = select_random_sample(df, args.size, args.seed)
    
    # Determine output path
    paths = Paths()
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = paths.processed_dir / "annotation_sample.csv"
    
    # Save sample
    save_annotation_sample(sample_df, output_path)


if __name__ == "__main__":
    main()

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from config import DatasetBlockedException, get_dataset_config

from config import DatasetBlockedException, get_dataset_config

def load_adaplanbench(dataset_id: Optional[str] = None) -> pd.DataFrame:
    """Loads the AdaPlanBench dataset from Hugging Face Datasets.
    
    Raises:
        DatasetBlockedException: If the dataset cannot be fetched or the 
        'progressive_constraints' field is missing.
    """
    if dataset_id is None:
        config = get_dataset_config()
        dataset_id = config.id

    try:
        from datasets import load_dataset
    except ImportError:
        raise ImportError("Please install the 'datasets' library.")

    try:
        # Attempt to load the dataset
        # Using trust_remote_code=False for safety, and streaming=False for full load
        # to ensure we can verify the schema immediately.
        dataset = load_dataset(dataset_id, split="train", trust_remote_code=False)
        df = dataset.to_pandas()
        
        # CRITICAL: Verify the existence of 'progressive_constraints' field immediately
        # If missing, raise DatasetBlockedException to abort the pipeline
        if 'progressive_constraints' not in df.columns:
            raise DatasetBlockedException(
                f"Dataset '{dataset_id}' is missing required field 'progressive_constraints'. "
                "The pipeline cannot proceed without this field."
            )
        
        # Verify that the field actually contains list data (not just a column name)
        # Check first non-null row if possible
        sample_row = None
        for i in range(len(df)):
            if pd.notna(df.iloc[i]['progressive_constraints']):
                sample_row = df.iloc[i]
                break
        
        if sample_row is None:
            raise DatasetBlockedException(
                f"Field 'progressive_constraints' in dataset '{dataset_id}' "
                "contains only null values or is empty."
            )

        if not isinstance(sample_row['progressive_constraints'], list):
            raise DatasetBlockedException(
                f"Field 'progressive_constraints' in dataset '{dataset_id}' "
                f"does not contain list data as expected. Type found: {type(sample_row['progressive_constraints'])}"
            )

        return df
    except DatasetBlockedException:
        # Re-raise our custom exception immediately
        raise
    except Exception as e:
        # Wrap any other loading error in our block exception to ensure abort
        raise DatasetBlockedException(
            f"Failed to load or verify AdaPlanBench dataset '{dataset_id}': {e}. "
            "Pipeline aborted."
        ) from e

def verify_progressive_constraints(df: pd.DataFrame) -> bool:
    """Verifies that the 'progressive_constraints' field exists and is valid in each row."""
    if 'progressive_constraints' not in df.columns:
        return False
    # Check a sample to ensure it's a list (full check might be expensive on huge datasets)
    # but for verification purposes we check the first few rows
    sample_size = min(10, len(df))
    for i in range(sample_size):
        if pd.isna(df.iloc[i]['progressive_constraints']):
            continue # Skip nulls
        if not isinstance(df.iloc[i]['progressive_constraints'], list):
            return False
    return True

def filter_progressive_constraints(df: pd.DataFrame, min_constraints: int = 5) -> pd.DataFrame:
    """Filters the dataset to include only tasks with at least a specified number of progressive constraints.
    
    This function implements the core logic for T013:
    1. Calculates `constraint_count` as len(progressive_constraints) for each row.
    2. Filters rows where constraint_count >= min_constraints.
    3. Ensures output includes: task_id, raw_prompt, progressive_constraints, constraint_count.
    """
    # Ensure the column exists before filtering (should be guaranteed by load_adaplanbench)
    if 'progressive_constraints' not in df.columns:
        raise RuntimeError("Cannot filter: 'progressive_constraints' column missing.")
    
    # Calculate constraint count safely, handling potential nulls
    # T013 Requirement: constraint_count = len(progressive_constraints)
    df['constraint_count'] = df['progressive_constraints'].apply(
        lambda x: len(x) if isinstance(x, list) else 0
    )
    
    # Filter for tasks with >= min_constraints
    filtered_df = df[df['constraint_count'] >= min_constraints].copy()
    
    # Ensure required columns exist in output (T013 Output Schema)
    required_cols = ['task_id', 'raw_prompt', 'progressive_constraints', 'constraint_count']
    
    # Check which required columns exist in the original dataframe
    existing_cols = [col for col in required_cols if col in filtered_df.columns]
    missing_cols = [col for col in required_cols if col not in filtered_df.columns]
    
    if missing_cols:
        # If raw_prompt is missing, we might need to map it from a different column name
        # Common variations in datasets
        prompt_candidates = ['prompt', 'instruction', 'input', 'task_prompt', 'question']
        found_prompt_col = None
        
        for candidate in prompt_candidates:
            if candidate in filtered_df.columns:
                found_prompt_col = candidate
                break
        
        if found_prompt_col:
            filtered_df['raw_prompt'] = filtered_df[found_prompt_col]
            existing_cols.append('raw_prompt')
            missing_cols.remove('raw_prompt')
        else:
            # If no prompt column found, raise error as we cannot proceed without it
            raise RuntimeError(
                f"Cannot produce required output: Missing 'raw_prompt' column. "
                f"Found columns: {list(filtered_df.columns)}. "
                f"Expected one of: {prompt_candidates}"
            )
    
    # Select only the required columns for the output
    # This ensures the CSV schema matches T013 requirements exactly
    output_df = filtered_df[existing_cols].copy()
    
    return output_df

def save_filtered_dataset(df: pd.DataFrame, output_path: str) -> None:
    """Saves the filtered dataset to a CSV file.
    
    Ensures the output file is written to disk at the exact path specified.
    """
    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Write to CSV
    df.to_csv(output_path, index=False)
    
    # Verify file was written and is not empty
    if not os.path.exists(output_path):
        raise RuntimeError(f"Failed to write output file: {output_path}")
    
    file_size = os.path.getsize(output_path)
    if file_size == 0:
        raise RuntimeError(f"Output file is empty: {output_path}")

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Load and filter AdaPlanBench dataset.")
    parser.add_argument("--verify-only", action="store_true", help="Only verify the dataset schema")
    parser.add_argument("--filter-min-constraints", type=int, default=5, help="Minimum number of progressive constraints to keep")
    parser.add_argument("--output", type=str, default="data/processed/filtered_tasks.csv", help="Output path for the filtered dataset")

    args = parser.parse_args()

    # Get the dataset ID from config
    dataset_config = get_dataset_config()
    dataset_id = dataset_config.get("adaplanbench_id", "AdaptivePlanningBenchmark/ada-planbench")

    try:
        df = load_adaplanbench()
    except DatasetBlockedException as e:
        print(f"BLOCKED: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error loading AdaPlanBench dataset: {e}", file=sys.stderr)
        sys.exit(1)

    if args.verify_only:
        if not verify_progressive_constraints(df):
            print("Dataset schema verification failed.")
            sys.exit(1)
        else:
            print("Dataset schema verified successfully.")
            sys.exit(0)
    
    # T013 Implementation: Filter and save
    filtered_df = filter_progressive_constraints(df, args.filter_min_constraints)
    
    if len(filtered_df) == 0:
        print(f"WARNING: No tasks found with >= {args.filter_min_constraints} constraints.", file=sys.stderr)
        # Still create the file with headers to satisfy schema requirements, 
        # but log the warning
    
    save_filtered_dataset(filtered_df, args.output)

    print(f"Filtered dataset saved to {args.output}")
    print(f"Total tasks loaded: {len(df)}, Tasks after filtering (>= {args.filter_min_constraints}): {len(filtered_df)}")
    print(f"Output columns: {list(filtered_df.columns)}")

if __name__ == "__main__":
    main()

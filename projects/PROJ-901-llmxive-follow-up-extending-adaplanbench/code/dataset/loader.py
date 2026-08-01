import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from config import DatasetBlockedException, get_dataset_config

def load_adaplanbench(dataset_id: str) -> pd.DataFrame:
    """Loads the AdaPlanBench dataset from Hugging Face Datasets.
    
    Raises:
        DatasetBlockedException: If the dataset cannot be fetched or is missing required fields.
    """
    try:
        from datasets import load_dataset
    except ImportError:
        raise ImportError("Please install the 'datasets' library.")

    try:
        # Attempt to fetch the real dataset. 
        # We do not use streaming=True here as we need to verify the schema of the full dataset
        # or a representative sample before proceeding, and the dataset size is manageable.
        # If the dataset is too large for the environment, the load_dataset call will fail,
        # which triggers the exception below.
        dataset = load_dataset(dataset_id, split="train")
        df = dataset.to_pandas()
        
        # CRITICAL: Verify the existence of the 'progressive_constraints' field.
        # If missing, the dataset is blocked for this study.
        if 'progressive_constraints' not in df.columns:
            raise DatasetBlockedException(
                f"Dataset '{dataset_id}' is missing the required 'progressive_constraints' field. "
                "The study cannot proceed without this field."
            )
        
        # Verify that the field contains lists (as expected) for at least the first few rows
        # to ensure data integrity before returning.
        sample_count = min(10, len(df))
        for i in range(sample_count):
            if not isinstance(df.iloc[i]['progressive_constraints'], list):
                raise DatasetBlockedException(
                    f"Dataset '{dataset_id}' has invalid data in 'progressive_constraints' "
                    f"at row {i}. Expected a list, got {type(df.iloc[i]['progressive_constraints']).__name__}."
                )

        return df
    except DatasetBlockedException:
        # Re-raise our specific exception
        raise
    except Exception as e:
        # Wrap any other loading error in DatasetBlockedException to abort immediately
        raise DatasetBlockedException(
            f"Failed to load or verify AdaPlanBench dataset '{dataset_id}': {e}. "
            "The pipeline is blocked and will not proceed with synthetic data."
        ) from e

def verify_progressive_constraints(df: pd.DataFrame) -> bool:
    """Verifies that the 'progressive_constraints' field exists and is valid in each row."""
    if 'progressive_constraints' not in df.columns:
        return False
    return all(isinstance(row['progressive_constraints'], list) for _, row in df.iterrows())

def filter_progressive_constraints(df: pd.DataFrame, min_constraints: int = 5) -> pd.DataFrame:
    """Filters the dataset to include only tasks with at least a specified number of progressive constraints.
    
    Output Schema:
        - task_id: str
        - raw_prompt: str
        - progressive_constraints: list (the original list)
        - constraint_count: int (calculated as len(progressive_constraints))
    """
    # Ensure we calculate the count based on the actual list length
    df['constraint_count'] = df['progressive_constraints'].apply(len)
    
    # Filter rows where constraint_count >= min_constraints
    filtered_df = df[df['constraint_count'] >= min_constraints].copy()
    
    # Ensure the required columns exist and are in the correct order for the output schema
    required_cols = ['task_id', 'raw_prompt', 'progressive_constraints', 'constraint_count']
    
    # Check if all required columns exist in the filtered dataframe
    missing_cols = [col for col in required_cols if col not in filtered_df.columns]
    if missing_cols:
        # If the original dataset is missing expected columns, we cannot proceed
        raise DatasetBlockedException(
            f"Dataset is missing required columns for filtering: {missing_cols}. "
            "Expected columns: task_id, raw_prompt, progressive_constraints."
        )
    
    # Select and order the columns
    result_df = filtered_df[required_cols]
    
    return result_df

def save_filtered_dataset(df: pd.DataFrame, output_path: str) -> None:
    """Saves the filtered dataset to a CSV file.
    
    The CSV will contain:
        - task_id
        - raw_prompt
        - progressive_constraints (stored as JSON string representation of the list)
        - constraint_count
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert the list column to a JSON string for CSV storage
    df_to_save = df.copy()
    df_to_save['progressive_constraints'] = df_to_save['progressive_constraints'].apply(json.dumps)
    
    df_to_save.to_csv(output_path, index=False)

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
        # This will raise DatasetBlockedException if fetch fails or field is missing
        df = load_adaplanbench(dataset_id)
    except DatasetBlockedException as e:
        print(f"BLOCKED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error loading dataset: {e}")
        sys.exit(1)

    if args.verify_only:
        if not verify_progressive_constraints(df):
            print("Dataset schema verification failed.")
            sys.exit(1)
        else:
            print("Dataset schema verified successfully.")
            sys.exit(0)
    
    filtered_df = filter_progressive_constraints(df, args.filter_min_constraints)
    
    if len(filtered_df) == 0:
        print("WARNING: No tasks found matching the filter criteria. The output file will be empty.")
    
    save_filtered_dataset(filtered_df, args.output)

    print(f"Filtered dataset saved to {args.output}")
    print(f"Total tasks filtered: {len(filtered_df)}")

if __name__ == "__main__":
    main()

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import argparse

# Import configuration
from config import get_paths, get_dataset_config

# --- Constants ---
MIN_CONSTRAINT_REVEALS = 5

def load_adaplanbench() -> List[Dict[str, Any]]:
    """
    Fetches the AdaPlanBench dataset.
    Configuration: Reads dataset ID/URL from code/config.py.
    On fetch failure, raises a clear error and aborts – no mock fallback.
    Verifies existence of `progressive_constraints` field.
    """
    paths = get_paths()
    dataset_config = get_dataset_config()

    print("Loading AdaPlanBench dataset...")

    # Try to load from local path if specified
    if dataset_config.LOCAL_PATH:
        local_path = Path(dataset_config.LOCAL_PATH)
        if local_path.exists():
            print(f"Loading from local path: {local_path}")
            # Assuming parquet or jsonl format
            if local_path.suffix == '.parquet':
                df = pd.read_parquet(local_path)
            elif local_path.suffix == '.jsonl':
                df = pd.read_json(local_path, lines=True)
            else:
                df = pd.read_csv(local_path)
            return df.to_dict('records')
        else:
            raise FileNotFoundError(f"Specified local dataset path does not exist: {local_path}")

    # Try HuggingFace datasets
    try:
        from datasets import load_dataset
        # Attempt to load the dataset. If the ID is not standard, we might need to use the URL.
        # The config provides a fallback URL, but datasets.load_dataset usually expects an ID or a local path.
        # We will try the standard ID first. If that fails, we try to fetch from the URL directly if possible,
        # or raise an error.
        # For AdaPlanBench, assuming it's hosted on HF.
        dataset_id = dataset_config.DATASET_NAME
        print(f"Attempting to load from HuggingFace: {dataset_id}")
        ds = load_dataset(dataset_id, split="train")
        return ds.to_list()
    except Exception as e:
        print(f"Failed to load from HuggingFace ({dataset_config.DATASET_NAME}): {e}")

    # Fallback to direct URL download if HF fails
    # This is a robust fallback mechanism for real data
    url = dataset_config.OFFICIAL_URL_FALLBACK
    if url:
        print(f"Falling back to direct URL fetch: {url}")
        try:
            import requests
            response = requests.get(url)
            response.raise_for_status()
            
            # Save temporarily to load with pandas
            temp_path = paths.DATA_RAW / "temp_adaplanbench.parquet"
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            
            df = pd.read_parquet(temp_path)
            # Clean up temp file
            temp_path.unlink()
            return df.to_dict('records')
        except Exception as fetch_error:
            raise RuntimeError(f"Failed to fetch dataset from fallback URL {url}: {fetch_error}") from fetch_error

    raise RuntimeError("Could not load AdaPlanBench dataset from any configured source.")

def verify_progressive_constraints(tasks: List[Dict[str, Any]]) -> None:
    """
    Verifies that the 'progressive_constraints' field exists in the loaded data.
    Raises ValueError if missing.
    """
    if not tasks:
        raise ValueError("Loaded dataset is empty.")
    
    first_task = tasks[0]
    if 'progressive_constraints' not in first_task:
        raise ValueError(
            "Dataset missing required field 'progressive_constraints'. "
            "The loader cannot proceed without this field to filter tasks."
        )

def filter_progressive_constraints(tasks: List[Dict[str, Any]], min_constraints: int = MIN_CONSTRAINT_REVEALS) -> List[Dict[str, Any]]:
    """
    Filters tasks to select only those with >= min_constraints progressive constraint reveals.
    """
    filtered = []
    for task in tasks:
        constraints = task.get('progressive_constraints', [])
        if isinstance(constraints, list) and len(constraints) >= min_constraints:
            filtered.append(task)
    return filtered

def save_filtered_dataset(tasks: List[Dict[str, Any]], output_path: str):
    """
    Saves the filtered tasks to a CSV file.
    Adds 'constraint_count' column.
    """
    if not tasks:
        print("Warning: No tasks to save.")
        # Create an empty file with headers to satisfy downstream expectations if needed,
        # or just return. The task description implies we are filtering, so empty is possible.
        # However, usually we want to ensure the file exists.
        df = pd.DataFrame(columns=['task_id', 'progressive_constraints', 'constraint_count'])
        df.to_csv(output_path, index=False)
        return

    # Prepare data for DataFrame
    data = []
    for task in tasks:
        row = {
            'task_id': task.get('task_id', ''),
            'progressive_constraints': task.get('progressive_constraints', []),
            'raw_prompt': task.get('raw_prompt', ''),
            'constraint_list': task.get('constraint_list', []) # Assuming this exists or is derived
        }
        # Calculate constraint_count
        constraints = task.get('progressive_constraints', [])
        row['constraint_count'] = len(constraints) if isinstance(constraints, list) else 0
        data.append(row)

    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    print(f"Saved {len(tasks)} filtered tasks to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Load and filter AdaPlanBench dataset.")
    parser.add_argument("--verify-only", action="store_true", help="Load and verify schema, do not filter/save.")
    parser.add_argument("--filter-min-constraints", type=int, default=MIN_CONSTRAINT_REVEALS, help="Minimum constraints to keep a task.")
    parser.add_argument("--output", type=str, default="data/processed/filtered_tasks.csv", help="Output CSV path.")
    
    args = parser.parse_args()

    try:
        tasks = load_adaplanbench()
        verify_progressive_constraints(tasks)
        
        if args.verify_only:
            print("Verification successful. Dataset contains 'progressive_constraints'.")
            print(f"Total tasks loaded: {len(tasks)}")
            # Count how many would pass the filter
            count = sum(1 for t in tasks if len(t.get('progressive_constraints', [])) >= args.filter_min_constraints)
            print(f"Tasks with >= {args.filter_min_constraints} constraints: {count}")
            return

        # Filter
        filtered_tasks = filter_progressive_constraints(tasks, args.filter_min_constraints)
        print(f"Filtered to {len(filtered_tasks)} tasks with >= {args.filter_min_constraints} constraints.")
        
        # Save
        save_filtered_dataset(filtered_tasks, args.output)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
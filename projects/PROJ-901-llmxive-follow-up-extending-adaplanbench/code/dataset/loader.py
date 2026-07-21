"""
Module for loading and filtering the AdaPlanBench dataset.
Fetches real data from HuggingFace datasets and applies constraint filtering.
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datasets import load_dataset
import pandas as pd
import argparse

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Paths, get_paths, get_dataset_config

def load_adaplanbench() -> List[Dict[str, Any]]:
    """
    Load the AdaPlanBench dataset from HuggingFace.
    This function fetches REAL data and will fail loudly if the fetch fails.
    No synthetic fallback is implemented.
    """
    config = get_dataset_config()
    print(f"Loading dataset: {config.NAME}")
    
    try:
        # Load the dataset
        dataset = load_dataset(config.NAME, split="train")
        
        # Convert to list of dicts
        data_list = dataset.to_pandas().to_dict(orient='records')
        print(f"Successfully loaded {len(data_list)} tasks.")
        return data_list
    except Exception as e:
        raise RuntimeError(f"Failed to load AdaPlanBench dataset: {str(e)}")

def filter_progressive_constraints(data: List[Dict[str, Any]], min_constraints: int = 5) -> List[Dict[str, Any]]:
    """
    Filter tasks to include only those with >= min_constraints progressive constraints.
    """
    filtered = []
    for task in data:
        # Check if 'progressive_constraints' exists and is a list
        constraints = task.get('progressive_constraints', [])
        if isinstance(constraints, list) and len(constraints) >= min_constraints:
            filtered.append(task)
    
    print(f"Filtered dataset: {len(filtered)} tasks with >= {min_constraints} constraints.")
    return filtered

def save_filtered_dataset(data: List[Dict[str, Any]], output_path: Path, min_constraints: int = 5):
    """
    Save filtered dataset to CSV, adding a constraint_count column.
    """
    if not data:
        print("Warning: No data to save.")
        # Create empty file with headers
        df = pd.DataFrame(columns=['task_id', 'task_name', 'progressive_constraints', 'constraint_count'])
        df.to_csv(output_path, index=False)
        return

    # Prepare data for CSV
    rows = []
    for task in data:
        constraints = task.get('progressive_constraints', [])
        rows.append({
            'task_id': task.get('task_id', ''),
            'task_name': task.get('task_name', ''),
            'progressive_constraints': json.dumps(constraints),
            'constraint_count': len(constraints)
        })

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    print(f"Saved {len(rows)} tasks to {output_path}")

def main():
    """Main entry point for dataset loading and filtering."""
    parser = argparse.ArgumentParser(description="Load and filter AdaPlanBench dataset")
    parser.add_argument('--verify-only', action='store_true', help="Only verify dataset availability")
    parser.add_argument('--filter-min-constraints', type=int, default=5, help="Minimum number of constraints")
    parser.add_argument('--output', type=str, help="Output path for filtered dataset")
    
    args = parser.parse_args()
    paths = get_paths()
    config = get_dataset_config()

    # Default output path
    output_path = Path(args.output) if args.output else paths.DATA_PROCESSED / "filtered_tasks.csv"

    if args.verify_only:
        print("Verifying dataset availability...")
        try:
            data = load_adaplanbench()
            print(f"Dataset verified: {len(data)} tasks available.")
        except Exception as e:
            print(f"Verification failed: {e}")
            sys.exit(1)
        return

    # Load dataset
    print("Loading dataset...")
    data = load_adaplanbench()

    # Filter dataset
    print(f"Filtering tasks with >= {args.filter_min_constraints} constraints...")
    filtered_data = filter_progressive_constraints(data, args.filter_min_constraints)

    # Save dataset
    print(f"Saving filtered dataset to {output_path}...")
    save_filtered_dataset(filtered_data, output_path, args.filter_min_constraints)
    print("Done.")

if __name__ == "__main__":
    main()

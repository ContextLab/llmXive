"""
Dataset loading and filtering for AdaPlanBench.
Fetches the official dataset and filters for tasks with progressive constraints.
"""
import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_paths, get_dataset_config
from datasets import load_dataset

def load_adaplanbench() -> List[Dict[str, Any]]:
    """
    Load the AdaPlanBench dataset.
    Uses HuggingFace datasets library with fallback to direct URL.
    """
    config = get_dataset_config()
    paths = get_paths()

    # Ensure data/raw exists
    paths.DATA_RAW.mkdir(parents=True, exist_ok=True)

    try:
        # Try loading from HuggingFace
        print(f"Attempting to load dataset: {config.DATASET_ID}")
        dataset = load_dataset(config.DATASET_ID, split="train")
        
        # Verify required field
        if config.REQUIRED_FIELD not in dataset.column_names:
            raise ValueError(f"Dataset missing required field: {config.REQUIRED_FIELD}")
        
        tasks = dataset.to_list()
        print(f"Successfully loaded {len(tasks)} tasks from HuggingFace.")
        return tasks

    except Exception as e:
        print(f"Failed to load from HuggingFace: {e}", file=sys.stderr)
        print(f"Attempting fallback to direct URL: {config.FALLBACK_URL}", file=sys.stderr)
        
        # Fallback: try to load from direct URL
        try:
            # Download and load JSON file
            import urllib.request
            import tempfile
            
            with tempfile.TemporaryDirectory() as tmpdir:
                json_path = Path(tmpdir) / "adaplanbench.json"
                urllib.request.urlretrieve(config.FALLBACK_URL, str(json_path))
                
                with open(json_path, 'r', encoding='utf-8') as f:
                    tasks = json.load(f)
                
                if config.REQUIRED_FIELD not in (tasks[0] if tasks else {}):
                    raise ValueError(f"Fallback data missing required field: {config.REQUIRED_FIELD}")
                
                print(f"Successfully loaded {len(tasks)} tasks from fallback URL.")
                return tasks
                
        except Exception as fallback_error:
            print(f"Failed to load from fallback URL: {fallback_error}", file=sys.stderr)
            raise RuntimeError(
                f"Cannot load AdaPlanBench dataset. "
                f"Primary source ({config.DATASET_ID}) and fallback ({config.FALLBACK_URL}) both failed. "
                f"Primary error: {e}. Fallback error: {fallback_error}"
            ) from fallback_error

def filter_progressive_constraints(
    tasks: List[Dict[str, Any]], 
    min_constraints: int = 5
) -> List[Dict[str, Any]]:
    """
    Filter tasks to include only those with at least min_constraints progressive constraints.
    
    Args:
        tasks: List of task dictionaries.
        min_constraints: Minimum number of progressive constraints required.
        
    Returns:
        Filtered list of tasks.
    """
    config = get_dataset_config()
    filtered = []
    
    for task in tasks:
        constraints = task.get(config.REQUIRED_FIELD, [])
        # Handle string representation of list
        if isinstance(constraints, str):
            try:
                constraints = eval(constraints, {"__builtins__": {}}, {})
            except Exception:
                constraints = [constraints] if constraints else []
        
        if len(constraints) >= min_constraints:
            filtered.append(task)
    
    print(f"Filtered {len(tasks)} tasks down to {len(filtered)} tasks with >= {min_constraints} constraints.")
    return filtered

def save_filtered_dataset(
    tasks: List[Dict[str, Any]], 
    output_path: str
) -> None:
    """
    Save filtered tasks to CSV with constraint_count column.
    
    Args:
        tasks: List of task dictionaries.
        output_path: Path to output CSV file.
    """
    paths = get_paths()
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare data for DataFrame
    records = []
    for task in tasks:
        constraints = task.get('progressive_constraints', [])
        if isinstance(constraints, str):
            try:
                constraints = eval(constraints, {"__builtins__": {}}, {})
            except Exception:
                constraints = [constraints] if constraints else []
        
        record = {
            'task_id': task.get('task_id', ''),
            'raw_prompt': task.get('raw_prompt', ''),
            'progressive_constraints': str(constraints),
            'constraint_count': len(constraints)
        }
        records.append(record)
    
    df = pd.DataFrame(records)
    df.to_csv(output_file, index=False)
    print(f"Saved {len(records)} tasks to {output_file}")

def main():
    """Main entry point for dataset loading and filtering."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load and filter AdaPlanBench dataset")
    parser.add_argument("--verify-only", action="store_true",
                        help="Only verify dataset structure, don't save")
    parser.add_argument("--filter-min-constraints", type=int, default=5,
                        help="Minimum number of progressive constraints")
    parser.add_argument("--output", type=str, default="data/processed/filtered_tasks.csv",
                        help="Output path for filtered tasks CSV")
    args = parser.parse_args()
    
    print("Loading AdaPlanBench dataset...")
    tasks = load_adaplanbench()
    
    if args.verify_only:
        print("Verification complete. Dataset loaded successfully.")
        return
    
    print(f"Filtering tasks with >= {args.filter_min_constraints} constraints...")
    filtered_tasks = filter_progressive_constraints(tasks, args.filter_min_constraints)
    
    if not filtered_tasks:
        print("Error: No tasks found matching the filter criteria.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Saving filtered dataset to {args.output}...")
    save_filtered_dataset(filtered_tasks, args.output)
    
    print("Done.")

if __name__ == "__main__":
    main()
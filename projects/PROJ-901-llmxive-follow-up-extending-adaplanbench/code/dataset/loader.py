import os
import sys
import json
import hashlib
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import argparse

from config import Paths, DatasetBlockedException, get_dataset_config
import jsonlines

def get_real_data_source() -> str:
    """Returns the configured dataset URL or ID from config."""
    config = get_dataset_config()
    return config.get('url', config.get('id', 'adaplanbench/progressive'))

def fetch_dataset_from_url(url: str) -> List[Dict[str, Any]]:
    """
    Attempts to fetch the dataset from the provided URL.
    If the URL is a HuggingFace dataset ID, uses datasets library.
    If it is a direct URL, attempts to download.
    """
    try:
        # Attempt HF loading first (most common for research datasets)
        from datasets import load_dataset
        # Try loading as a dataset if it looks like an ID
        if 'http' not in url and not url.endswith('.jsonl') and not url.endswith('.json'):
            ds = load_dataset(url, split='train')
            return list(ds)
        else:
            # Direct file download logic would go here
            # For now, assume it's a local path or handled by HF
            raise ValueError(f"Unsupported URL type for fetch: {url}")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch dataset from {url}: {e}")

def verify_progressive_constraints(data: List[Dict[str, Any]]) -> bool:
    """Checks if the dataset contains the 'progressive_constraints' field."""
    if not data:
        return False
    first_item = data[0]
    return 'progressive_constraints' in first_item

def generate_synthetic_proxy(output_path: Path) -> List[Dict[str, Any]]:
    """
    Generates a deterministic synthetic proxy dataset if real data is unavailable.
    Satisfies T012b requirements for a fallback.
    """
    import random
    random.seed(42) # Deterministic
    
    tasks = []
    for i in range(100):
        task_id = f"synthetic_task_{i:03d}"
        # Create a list of constraints, varying length between 3 and 8
        num_constraints = random.randint(3, 8)
        constraints = [f"Constraint {j+1}: Do not {['open', 'close', 'move', 'touch', 'break', 'burn', 'cut', 'spill'][j % 8]} item {j}" for j in range(num_constraints)]
        
        tasks.append({
            "task_id": task_id,
            "raw_prompt": f"Plan a sequence of actions for task {i} involving household items.",
            "progressive_constraints": constraints,
            "metadata": {"source": "synthetic"}
        })
    
    # Save to file as required by T012b
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        for task in tasks:
            f.write(json.dumps(task) + '\n')
    
    return tasks

def load_adaplanbench() -> Tuple[List[Dict[str, Any], Path]]:
    """
    Main entry point to load the dataset.
    Tries real fetch first. If it fails, generates proxy.
    Returns the data list and the path to the saved file.
    """
    config = get_dataset_config()
    raw_dir = Paths().DATA_RAW
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    url = get_real_data_source()
    proxy_path = raw_dir / "synthetic_proxy.jsonl"
    real_path = raw_dir / "adaplanbench.jsonl"
    
    data = None
    
    # Attempt Real Fetch
    try:
        data = fetch_dataset_from_url(url)
        if not verify_progressive_constraints(data):
            raise ValueError("Real dataset loaded but missing 'progressive_constraints' field.")
        
        # Save real data
        with open(real_path, 'w') as f:
            for item in data:
                f.write(json.dumps(item) + '\n')
        return data, real_path
        
    except Exception as e:
        print(f"Warning: Real data fetch failed ({e}). Generating synthetic proxy.", file=sys.stderr)
        data = generate_synthetic_proxy(proxy_path)
        return data, proxy_path

def filter_progressive_constraints(data: List[Dict[str, Any]], min_constraints: int = 5) -> List[Dict[str, Any]]:
    """
    Filters the dataset to include only tasks with >= min_constraints progressive constraints.
    Calculates 'constraint_count' for each task.
    """
    filtered = []
    for task in data:
        constraints = task.get('progressive_constraints', [])
        count = len(constraints)
        if count >= min_constraints:
            # Create a new dict to ensure schema compliance
            new_task = {
                "task_id": task.get('task_id', 'unknown'),
                "raw_prompt": task.get('raw_prompt', ''),
                "progressive_constraints": constraints,
                "constraint_count": count
            }
            filtered.append(new_task)
    return filtered

def save_filtered_dataset(data: List[Dict[str, Any]], output_path: Path):
    """
    Saves the filtered dataset to a CSV file.
    Output Schema: task_id, raw_prompt, progressive_constraints (list as string), constraint_count
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(['task_id', 'raw_prompt', 'progressive_constraints', 'constraint_count'])
        
        for task in data:
            # Convert list to JSON string for CSV storage
            constraints_str = json.dumps(task['progressive_constraints'])
            writer.writerow([
                task['task_id'],
                task['raw_prompt'],
                constraints_str,
                task['constraint_count']
            ])

def main():
    """
    CLI entry point for dataset loading and filtering.
    Supports --filter-min-constraints to set the threshold.
    """
    parser = argparse.ArgumentParser(description="Load and filter AdaPlanBench dataset.")
    parser.add_argument('--filter-min-constraints', type=int, default=5, 
                        help='Minimum number of progressive constraints required (default: 5)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output path for filtered CSV (default: data/processed/filtered_tasks.csv)')
    parser.add_argument('--verify-only', action='store_true',
                        help='Only verify the dataset structure without filtering')
    
    args = parser.parse_args()
    
    print("Loading dataset...")
    data, source_path = load_adaplanbench()
    print(f"Loaded {len(data)} tasks from {source_path}")
    
    if args.verify_only:
        print("Verification passed: Dataset contains 'progressive_constraints'.")
        return

    # Filter
    print(f"Filtering tasks with >= {args.filter_min_constraints} constraints...")
    filtered_data = filter_progressive_constraints(data, args.filter_min_constraints)
    print(f"Filtered result: {len(filtered_data)} tasks.")
    
    if not filtered_data:
        print("Warning: No tasks met the constraint threshold.", file=sys.stderr)
    
    # Determine output path
    if args.output:
        out_path = Path(args.output)
    else:
        out_path = Paths().DATA_PROCESSED / "filtered_tasks.csv"
    
    # Save
    save_filtered_dataset(filtered_data, out_path)
    print(f"Saved filtered dataset to {out_path}")

if __name__ == "__main__":
    main()

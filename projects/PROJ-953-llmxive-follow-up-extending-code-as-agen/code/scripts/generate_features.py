import os
import csv
import json
from pathlib import Path
from typing import List, Dict, Any

# Import existing functions from the API surface
from scripts.extract_features import load_ground_truth, filter_unparseable

# Ensure output directories exist
DATA_PROCESSED_DIR = Path("data/processed")
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def load_graph_metrics(task_id: str) -> Dict[str, Any]:
    """
    Load the serialized dependency graph and metrics for a given task_id.
    The graph is stored at data/graphs/{task_id}.json as per T023.
    """
    graph_path = Path("data/graphs") / f"{task_id}.json"
    if not graph_path.exists():
        return {}
    
    try:
        with open(graph_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("metrics", {})
    except (json.JSONDecodeError, KeyError) as e:
        # If the file exists but is malformed or missing metrics, return empty
        # This allows the pipeline to continue but results in missing values
        # which should be caught by T025 validation.
        return {}

def merge_ground_truth_with_metrics(ground_truth_path: str) -> List[Dict[str, Any]]:
    """
    Load ground_truth.csv, iterate through rows, load corresponding metrics
    from data/graphs/{task_id}.json, and merge them into a unified list of dicts.
    """
    rows = load_ground_truth(ground_truth_path)
    merged_rows = []

    for row in rows:
        task_id = row.get("task_id")
        if not task_id:
            continue

        # Load metrics calculated in T021/T022/T023
        metrics = load_graph_metrics(task_id)
        
        # Create a new row combining ground truth and metrics
        new_row = {**row, **metrics}
        merged_rows.append(new_row)

    return merged_rows

def write_features_csv(rows: List[Dict[str, Any]], output_path: str):
    """
    Write the merged rows to a CSV file.
    Ensures all keys across all rows are included in the header.
    """
    if not rows:
        # Write empty file with no headers if no data
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            pass
        return

    # Collect all unique keys to form the header
    fieldnames = set()
    for row in rows:
        fieldnames.update(row.keys())
    
    # Sort fieldnames for consistent output (optional but good practice)
    fieldnames = sorted(list(fieldnames))

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def main():
    """
    Main entry point for T024: Generate features.csv.
    1. Load data/processed/ground_truth.csv
    2. Merge with metrics from data/graphs/{task_id}.json
    3. Write to data/processed/features.csv
    """
    ground_truth_path = "data/processed/ground_truth.csv"
    output_path = "data/processed/features.csv"

    if not Path(ground_truth_path).exists():
        raise FileNotFoundError(
            f"Required input file not found: {ground_truth_path}. "
            "Please ensure T015 (generate_ground_truth) has completed."
        )

    print(f"Loading ground truth from {ground_truth_path}...")
    merged_data = merge_ground_truth_with_metrics(ground_truth_path)
    
    print(f"Merged {len(merged_data)} rows with graph metrics.")
    print(f"Writing features to {output_path}...")
    
    write_features_csv(merged_data, output_path)
    
    print(f"Successfully generated {output_path}")

if __name__ == "__main__":
    main()
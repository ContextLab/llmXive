"""
Feature Generation Module for llmXive.

This module merges ground truth data with extracted features to create
the final features dataset.
"""

import os
import csv
import json
from pathlib import Path
from typing import List, Dict, Any
from scripts.extract_features import load_ground_truth, filter_unparseable

def load_graph_metrics(graph_dir: str) -> List[Dict[str, Any]]:
    """Load graph metrics from JSON files."""
    metrics = []
    
    if not os.path.exists(graph_dir):
        return metrics
    
    for filename in os.listdir(graph_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(graph_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                metrics.append(data)
    
    return metrics

def merge_ground_truth_with_metrics(
    ground_truth: List[Dict[str, Any]],
    graph_metrics: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Merge ground truth with graph metrics.
    
    Args:
        ground_truth: Ground truth tasks
        graph_metrics: Extracted graph metrics
        
    Returns:
        Merged list of dictionaries
    """
    # Create a lookup for metrics by task_id
    metrics_lookup = {m.get("task_id"): m for m in graph_metrics}
    
    merged = []
    for task in ground_truth:
        task_id = task.get("task_id")
        metrics = metrics_lookup.get(task_id, {})
        
        merged_task = {**task, **metrics}
        merged.append(merged_task)
    
    return merged

def write_features_csv(tasks: List[Dict[str, Any]], output_path: str) -> None:
    """Write merged tasks to CSV."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    if not tasks:
        raise ValueError("No tasks to write")
    
    fieldnames = tasks[0].keys()
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(tasks)

def main():
    """Main entry point for feature generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate features dataset")
    parser.add_argument("--ground-truth", "-g", required=True, help="Ground truth CSV")
    parser.add_argument("--graphs-dir", "-d", default="data/graphs", help="Graphs directory")
    parser.add_argument("--output", "-o", required=True, help="Output features CSV")
    
    args = parser.parse_args()
    
    print("Loading ground truth...")
    ground_truth = load_ground_truth(args.ground_truth)
    print(f"Loaded {len(ground_truth)} tasks")
    
    print("Loading graph metrics...")
    graph_metrics = load_graph_metrics(args.graphs_dir)
    print(f"Loaded {len(graph_metrics)} graph metrics")
    
    print("Merging data...")
    merged = merge_ground_truth_with_metrics(ground_truth, graph_metrics)
    print(f"Merged {len(merged)} records")
    
    print(f"Writing to {args.output}...")
    write_features_csv(merged, args.output)
    print("Done!")

if __name__ == "__main__":
    main()

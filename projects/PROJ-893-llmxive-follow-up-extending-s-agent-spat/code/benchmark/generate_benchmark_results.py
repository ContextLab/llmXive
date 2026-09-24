import os
import sys
import csv
import json
import math
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

# Ensure parent directory is in path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config

def load_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """Load a JSONL file into a list of dictionaries."""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data

def load_csv_as_dict(file_path: str, key_col: str = 'scene_id') -> Dict[str, Dict[str, Any]]:
    """Load a CSV file into a dictionary keyed by a specific column."""
    data = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row[key_col]
            data[key] = row
    return data

def load_predictions(file_path: str) -> Dict[str, Any]:
    """Load solver predictions from JSONL."""
    rows = load_jsonl(file_path)
    return {row['scene_id']: row for row in rows}

def load_ground_truth(file_path: str) -> Dict[str, Any]:
    """Load ground truth from CSV."""
    return load_csv_as_dict(file_path)

def load_latency_log(file_path: str) -> Dict[str, Any]:
    """Load latency log from JSONL."""
    rows = load_jsonl(file_path)
    return {row['scene_id']: row for row in rows}

def load_vlm_baseline(file_path: str) -> Dict[str, Any]:
    """Load VLM baseline predictions from CSV."""
    return load_csv_as_dict(file_path)

def calculate_exact_match(pred: Any, truth: Any) -> bool:
    """Calculate exact match between prediction and ground truth."""
    if pred is None or truth is None:
        return False
    # Handle potential string/numeric mismatches
    try:
        return int(pred) == int(truth)
    except (ValueError, TypeError):
        return str(pred) == str(truth)

def calculate_f1_score(pred: Any, truth: Any) -> float:
    """
    Calculate F1 score.
    For this specific task (counting/position), we treat it as a classification problem.
    If exact match -> Precision=1, Recall=1, F1=1.
    If mismatch -> Precision=0, Recall=0, F1=0.
    """
    if calculate_exact_match(pred, truth):
        return 1.0
    return 0.0

def compute_row_metrics(scene_id: str, symbolic_pred: Optional[str], vlm_pred: Optional[str],
                        ground_truth: Optional[str], status: str) -> Dict[str, Any]:
    """Compute metrics for a single row in the benchmark results."""
    exact_match = False
    f1 = 0.0
    latency_ms = 0.0

    if symbolic_pred is not None and ground_truth is not None:
        exact_match = calculate_exact_match(symbolic_pred, ground_truth)
        f1 = calculate_f1_score(symbolic_pred, ground_truth)

    # Latency is taken from the latency log
    # Note: In a real run, this would be populated from the latency log file
    # For now, we assume the latency log has the entry or we set to 0 if missing
    # The caller should ensure latency_log is loaded and passed or accessed via global/config

    return {
        'scene_id': scene_id,
        'symbolic_pred': symbolic_pred,
        'vlm_pred': vlm_pred,
        'ground_truth': ground_truth,
        'exact_match': exact_match,
        'f1': f1,
        'latency_ms': latency_ms, # Will be updated by caller if available
        'status': status
    }

def main():
    parser = argparse.ArgumentParser(description='Generate benchmark results CSV.')
    parser.add_argument('--predictions', type=str, required=True, help='Path to predictions.jsonl')
    parser.add_argument('--vlm-baseline', type=str, required=True, help='Path to vlm_baseline.csv')
    parser.add_argument('--ground-truth', type=str, required=True, help='Path to ground_truth.csv')
    parser.add_argument('--latency-log', type=str, required=True, help='Path to latency_log.jsonl')
    parser.add_argument('--exclusion-log', type=str, required=True, help='Path to exclusion_log.json')
    parser.add_argument('--output', type=str, required=True, help='Path to output benchmark_results.csv')
    args = parser.parse_args()

    # Load data
    try:
        predictions = load_predictions(args.predictions)
        vlm_baseline = load_vlm_baseline(args.vlm_baseline)
        ground_truth = load_ground_truth(args.ground_truth)
        latency_log = load_latency_log(args.latency_log)
        
        with open(args.exclusion_log, 'r') as f:
            exclusion_data = json.load(f)
    except FileNotFoundError as e:
        print(f"ERROR: Required input file not found: {e}")
        sys.exit(1)

    # Determine valid scene IDs based on exclusion log
    # The exclusion log contains 'valid_scenes' or we calculate total - excluded
    # Based on the provided sample: "valid_scenes": 5
    # We assume the exclusion log lists the IDs that were processed successfully.
    # If the log structure is different, we adapt.
    # The task description says: "Must explicitly read data/results/exclusion_log.json ... to perform filtering"
    # and "n_valid matches the processed count".
    
    # Strategy: We iterate through the ground truth (or predictions) and check if the scene_id
    # is considered valid based on the exclusion log.
    # If the exclusion log has a list of excluded IDs, we filter those out.
    # If it has a count, we assume the intersection of all sources is the valid set.
    
    # Let's assume the exclusion_log has 'excluded_ids' if available, otherwise we rely on the intersection
    # of keys present in all input files. The task says "ensure n_valid matches the processed count".
    # The provided sample exclusion_log has: "total_scenes_processed": 5, "valid_scenes": 5, "excluded_scenes": 0.
    # It does NOT list excluded IDs explicitly in the sample, but the task description says "plus a list of excluded_ids".
    # We will check for 'excluded_ids' key. If missing, we assume all scenes in the input files (that are common) are valid.
    
    excluded_ids = set(exclusion_data.get('excluded_ids', []))
    
    # Get all scene IDs from ground truth as the master list (assuming GT covers the sample)
    all_scene_ids = set(ground_truth.keys())
    
    # Filter out excluded
    valid_scene_ids = [sid for sid in all_scene_ids if sid not in excluded_ids]
    
    # Further filter to only those present in all other sources (predictions, vlm, latency)
    # This ensures we don't have rows with missing data
    valid_scene_ids = [
        sid for sid in valid_scene_ids 
        if sid in predictions and sid in vlm_baseline and sid in latency_log
    ]

    if len(valid_scene_ids) == 0:
        print("WARNING: No valid scenes found to generate benchmark results.")
        # Write empty CSV with headers
        with open(args.output, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['scene_id', 'symbolic_pred', 'vlm_pred', 'ground_truth', 'exact_match', 'f1', 'latency_ms', 'status'])
            writer.writeheader()
        return

    # Generate rows
    rows = []
    for scene_id in valid_scene_ids:
        sym_pred = predictions[scene_id].get('prediction')
        vlm_pred = vlm_baseline[scene_id].get('prediction')
        gt = ground_truth[scene_id].get('label')
        status = predictions[scene_id].get('status', 'unknown')
        latency = latency_log[scene_id].get('latency_ms', 0.0)

        row = compute_row_metrics(scene_id, sym_pred, vlm_pred, gt, status)
        row['latency_ms'] = latency
        rows.append(row)

    # Write to CSV
    fieldnames = ['scene_id', 'symbolic_pred', 'vlm_pred', 'ground_truth', 'exact_match', 'f1', 'latency_ms', 'status']
    with open(args.output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            # Convert booleans to strings for CSV consistency if needed, but csv module handles bools as True/False
            # The schema expects exact_match (bool) and f1 (float)
            writer.writerow(row)

    print(f"Generated benchmark results: {args.output} with {len(rows)} rows.")

if __name__ == '__main__':
    main()

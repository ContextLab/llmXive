import os
import sys
import csv
import json
import math
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config

def load_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """Load a JSONL file and return a list of dictionaries."""
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def load_csv_as_dict(file_path: str, key_field: str = 'scene_id') -> Dict[str, Dict[str, Any]]:
    """Load a CSV file and return a dictionary keyed by a specific field."""
    data = {}
    with open(file_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if key_field in row:
                data[row[key_field]] = row
    return data

def load_predictions(file_path: str) -> Dict[str, Dict[str, Any]]:
    """Load solver predictions from JSONL."""
    rows = load_jsonl(file_path)
    return {row['scene_id']: row for row in rows}

def load_ground_truth(file_path: str) -> Dict[str, Dict[str, Any]]:
    """Load ground truth from CSV."""
    return load_csv_as_dict(file_path, key_field='scene_id')

def load_latency_log(file_path: str) -> Dict[str, Dict[str, Any]]:
    """Load latency log from JSONL."""
    rows = load_jsonl(file_path)
    return {row['scene_id']: row for row in rows}

def load_vlm_baseline(file_path: str) -> Dict[str, Dict[str, Any]]:
    """Load VLM baseline predictions from CSV."""
    return load_csv_as_dict(file_path, key_field='scene_id')

def calculate_exact_match(pred: Any, truth: Any) -> float:
    """Calculate exact match (0 or 1)."""
    return 1.0 if str(pred) == str(truth) else 0.0

def calculate_f1_score(pred: Any, truth: Any) -> float:
    """
    Calculate F1 score for a single prediction.
    For counting tasks (discrete classes), F1 is equivalent to Exact Match.
    If prediction is correct: Precision=1, Recall=1, F1=1.
    If prediction is wrong: Precision=0, Recall=0, F1=0.
    """
    if str(pred) == str(truth):
        return 1.0
    return 0.0

def compute_row_metrics(symbolic_pred: Any, vlm_pred: Any, ground_truth: Any, latency_ms: float, status: str) -> Dict[str, Any]:
    """Compute all metrics for a single row of the benchmark results."""
    exact_match = calculate_exact_match(symbolic_pred, ground_truth)
    f1 = calculate_f1_score(symbolic_pred, ground_truth)

    # For McNemar's test, we need boolean correctness
    symbolic_correct = 1 if exact_match == 1.0 else 0
    vlm_correct = 1 if calculate_exact_match(vlm_pred, ground_truth) == 1.0 else 0

    return {
        'symbolic_pred': symbolic_pred,
        'vlm_pred': vlm_pred,
        'ground_truth': ground_truth,
        'exact_match': exact_match,
        'f1': f1,
        'latency_ms': latency_ms,
        'status': status,
        'symbolic_correct': symbolic_correct,
        'vlm_correct': vlm_correct
    }

def main():
    """
    Generate data/results/benchmark_results.csv by joining:
    - Solver predictions (data/derived/predictions.jsonl)
    - VLM baseline (data/derived/vlm_baseline.csv)
    - Ground truth (data/derived/ground_truth.csv)
    - Latency (data/derived/latency_log.jsonl)
    
    And calculating metrics (Exact Match, F1).
    The p_value column is added later by T017 (McNemar's test), 
    but we initialize it as 0.0 or None here to match schema.
    """
    # Define paths based on Config or defaults
    # T012 outputs
    predictions_path = Config.DATA_DERIVED / 'predictions.jsonl'
    latency_path = Config.DATA_DERIVED / 'latency_log.jsonl'
    
    # T006 outputs
    vlm_baseline_path = Config.DATA_DERIVED / 'vlm_baseline.csv'
    ground_truth_path = Config.DATA_DERIVED / 'ground_truth.csv'
    
    # Output
    output_path = Config.DATA_RESULTS / 'benchmark_results.csv'

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load data
    print(f"Loading predictions from {predictions_path}...")
    predictions = load_predictions(str(predictions_path))
    
    print(f"Loading VLM baseline from {vlm_baseline_path}...")
    vlm_baseline = load_vlm_baseline(str(vlm_baseline_path))
    
    print(f"Loading ground truth from {ground_truth_path}...")
    ground_truth = load_ground_truth(str(ground_truth_path))
    
    print(f"Loading latency log from {latency_path}...")
    latency_log = load_latency_log(str(latency_path))

    # Identify common scene IDs (intersection)
    all_ids = set(predictions.keys()) & set(vlm_baseline.keys()) & set(ground_truth.keys())
    
    if not all_ids:
        print("ERROR: No common scene IDs found between datasets.")
        sys.exit(1)

    print(f"Processing {len(all_ids)} matched scenes...")

    # Prepare rows
    rows = []
    for scene_id in sorted(all_ids):
        pred_row = predictions[scene_id]
        vlm_row = vlm_baseline[scene_id]
        gt_row = ground_truth[scene_id]
        lat_row = latency_log.get(scene_id, {'latency_ms': 0.0, 'status': 'unknown'})

        symbolic_pred = pred_row.get('prediction', None)
        vlm_pred = vlm_row.get('vlm_prediction', vlm_row.get('prediction', None))
        gt = gt_row.get('label', gt_row.get('ground_truth', None))
        latency = float(lat_row.get('latency_ms', 0.0))
        status = pred_row.get('status', 'unknown')

        metrics = compute_row_metrics(symbolic_pred, vlm_pred, gt, latency, status)

        row = {
            'scene_id': scene_id,
            'symbolic_pred': symbolic_pred,
            'vlm_pred': vlm_pred,
            'ground_truth': gt,
            'exact_match': metrics['exact_match'],
            'f1': metrics['f1'],
            'latency_ms': metrics['latency_ms'],
            'status': metrics['status'],
            'p_value': None # Will be filled by T017
        }
        rows.append(row)

    # Write CSV
    fieldnames = ['scene_id', 'symbolic_pred', 'vlm_pred', 'ground_truth', 
                  'exact_match', 'f1', 'latency_ms', 'status', 'p_value']
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Benchmark results written to {output_path}")
    print(f"Total rows: {len(rows)}")

if __name__ == '__main__':
    main()
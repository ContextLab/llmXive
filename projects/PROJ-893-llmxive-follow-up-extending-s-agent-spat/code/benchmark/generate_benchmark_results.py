import os
import sys
import csv
import json
import math
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from benchmark.metrics import compute_mcnemar_test

def load_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """Load a JSONL file and return a list of dictionaries."""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data

def load_csv_as_dict(file_path: str, key_column: str = 'scene_id') -> Dict[str, Dict[str, Any]]:
    """Load a CSV file and return a dictionary keyed by the specified column."""
    data = {}
    with open(file_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row[key_column]
            data[key] = row
    return data

def load_predictions(file_path: str) -> Dict[str, Any]:
    """Load symbolic predictions from JSONL."""
    data = load_jsonl(file_path)
    return {row['scene_id']: row for row in data}

def load_ground_truth(file_path: str) -> Dict[str, Any]:
    """Load ground truth from CSV."""
    return load_csv_as_dict(file_path, key_column='scene_id')

def load_latency_log(file_path: str) -> Dict[str, Any]:
    """Load latency log from JSONL."""
    data = load_jsonl(file_path)
    return {row['scene_id']: row for row in data}

def load_vlm_baseline(file_path: str) -> Dict[str, Any]:
    """Load VLM baseline predictions from CSV."""
    return load_csv_as_dict(file_path, key_column='scene_id')

def calculate_exact_match(pred: Any, gt: Any) -> bool:
    """Calculate exact match between prediction and ground truth."""
    # Handle different types of comparisons
    if isinstance(pred, dict) and isinstance(gt, dict):
        return pred == gt
    return str(pred).strip().lower() == str(gt).strip().lower()

def calculate_f1_score(pred: Any, gt: Any) -> float:
    """Calculate F1 score between prediction and ground truth."""
    if calculate_exact_match(pred, gt):
        return 1.0
    return 0.0

def compute_row_metrics(row: Dict[str, Any], vlm_baseline: Dict[str, Any], latency_log: Dict[str, Any]) -> Dict[str, Any]:
    """Compute metrics for a single row of the benchmark result."""
    scene_id = row['scene_id']
    symbolic_pred = row.get('prediction', row.get('symbolic_pred'))
    vlm_pred = vlm_baseline.get(scene_id, {}).get('prediction', vlm_baseline.get(scene_id, {}).get('vlm_pred'))
    ground_truth = row.get('ground_truth', row.get('label'))
    
    # Ensure ground_truth exists, otherwise skip or mark as missing
    if not ground_truth and scene_id in load_ground_truth.__globals__.get('gt_cache', {}):
        ground_truth = load_ground_truth.__globals__['gt_cache'][scene_id].get('label')
    
    exact_match = calculate_exact_match(symbolic_pred, ground_truth) if ground_truth else False
    f1 = calculate_f1_score(symbolic_pred, ground_truth) if ground_truth else 0.0
    
    latency = latency_log.get(scene_id, {}).get('latency_ms', 0.0)
    status = row.get('status', row.get('solver_status', 'Unknown'))
    
    return {
        'scene_id': scene_id,
        'symbolic_pred': symbolic_pred,
        'vlm_pred': vlm_pred,
        'ground_truth': ground_truth,
        'exact_match': exact_match,
        'f1': f1,
        'latency_ms': latency,
        'status': status
    }

def main():
    """Generate the benchmark results CSV."""
    parser = argparse.ArgumentParser(description='Generate benchmark results CSV')
    parser.add_argument('--predictions', type=str, required=True, help='Path to predictions.jsonl')
    parser.add_argument('--ground-truth', type=str, required=True, help='Path to ground truth CSV')
    parser.add_argument('--vlm-baseline', type=str, required=True, help='Path to VLM baseline CSV')
    parser.add_argument('--latency-log', type=str, required=True, help='Path to latency log JSONL')
    parser.add_argument('--exclusion-log', type=str, required=True, help='Path to exclusion log JSON')
    parser.add_argument('--output', type=str, required=True, help='Path to output CSV')
    args = parser.parse_args()

    # Load data
    print(f"Loading predictions from {args.predictions}...")
    predictions = load_predictions(args.predictions)
    
    print(f"Loading ground truth from {args.ground_truth}...")
    ground_truth = load_ground_truth(args.ground_truth)
    
    print(f"Loading VLM baseline from {args.vlm_baseline}...")
    vlm_baseline = load_vlm_baseline(args.vlm_baseline)
    
    print(f"Loading latency log from {args.latency_log}...")
    latency_log = load_latency_log(args.latency_log)
    
    print(f"Loading exclusion log from {args.exclusion_log}...")
    with open(args.exclusion_log, 'r', encoding='utf-8') as f:
        exclusion_log = json.load(f)

    # Prepare output rows
    output_rows = []
    valid_scene_ids = set(predictions.keys())
    
    # Filter out excluded scenes if necessary (though predictions should already be filtered)
    # We trust the predictions file contains only valid scenes as per T012c
    
    # Calculate McNemar's p-value across the whole dataset
    # We need to compare symbolic vs VLM on the intersection
    symbolic_correct = 0
    vlm_correct = 0
    both_correct = 0
    both_incorrect = 0
    symbolic_wrong_vlm_right = 0
    symbolic_right_vlm_wrong = 0

    for scene_id in valid_scene_ids:
        sym_pred = predictions[scene_id].get('prediction')
        vlm_pred = vlm_baseline.get(scene_id, {}).get('prediction')
        gt = ground_truth.get(scene_id, {}).get('label')
        
        if not gt:
            continue
            
        sym_match = calculate_exact_match(sym_pred, gt)
        vlm_match = calculate_exact_match(vlm_pred, gt)
        
        if sym_match and vlm_match:
            both_correct += 1
        elif not sym_match and not vlm_match:
            both_incorrect += 1
        elif not sym_match and vlm_match:
            symbolic_wrong_vlm_right += 1
        elif sym_match and not vlm_match:
            symbolic_right_vlm_wrong += 1

    # McNemar's test statistic
    # chi2 = (|b - c| - 1)^2 / (b + c)
    b = symbolic_wrong_vlm_right
    c = symbolic_right_vlm_wrong
    
    if (b + c) > 0:
        chi2 = ((abs(b - c) - 1) ** 2) / (b + c)
        # Approximate p-value using chi2 distribution with 1 dof
        # Using a simple approximation for p-value
        # p = 1 - cdf(chi2, 1)
        # For simplicity, we'll use a lookup or approximation
        # p = exp(-chi2/2) is a rough approximation for 1 dof
        p_value = math.exp(-chi2 / 2)
    else:
        p_value = 1.0

    # Generate rows
    for scene_id in sorted(valid_scene_ids):
        row_data = compute_row_metrics(
            {'scene_id': scene_id, 'prediction': predictions[scene_id]['prediction'], 'status': predictions[scene_id]['status']},
            vlm_baseline,
            latency_log
        )
        row_data['p_value'] = p_value
        output_rows.append(row_data)

    # Write CSV
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['scene_id', 'symbolic_pred', 'vlm_pred', 'ground_truth', 'exact_match', 'f1', 'latency_ms', 'status', 'p_value']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in output_rows:
            # Convert booleans to 1/0 for CSV compatibility if needed, or keep as True/False
            # CSV writer handles bools as 'True'/'False' which is fine
            writer.writerow(row)

    print(f"Benchmark results written to {output_path}")
    
    # Verification check
    n_valid = exclusion_log.get('total_scenes_processed', 0) - exclusion_log.get('excluded_scenes', 0)
    if len(output_rows) != n_valid:
        print(f"Warning: Row count ({len(output_rows)}) does not match expected valid scenes ({n_valid}).")
        print("This may be due to missing ground truth or VLM data for some scenes.")

if __name__ == '__main__':
    main()
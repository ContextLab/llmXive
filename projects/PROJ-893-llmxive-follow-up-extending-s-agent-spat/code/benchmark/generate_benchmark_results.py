import os
import sys
import csv
import json
import math
from pathlib import Path
from typing import Dict, List, Any, Optional
from config import config

def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Load JSONL file."""
    data = []
    with open(path, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def load_csv_as_dict(path: Path, key: str = 'scene_id') -> Dict[str, Dict[str, Any]]:
    """Load CSV file as dictionary keyed by specified column."""
    data = {}
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data[row[key]] = row
    return data

def load_predictions(path: Path) -> Dict[str, Dict[str, Any]]:
    """Load predictions JSONL."""
    data = load_jsonl(path)
    return {item['scene_id']: item for item in data}

def load_ground_truth(path: Path) -> Dict[str, Any]:
    """Load ground truth CSV."""
    return load_csv_as_dict(path)

def load_latency_log(path: Path) -> Dict[str, float]:
    """Load latency log JSONL."""
    data = load_jsonl(path)
    return {item['scene_id']: item['latency_ms'] for item in data}

def load_vlm_baseline(path: Path) -> Dict[str, Any]:
    """Load VLM baseline predictions."""
    return load_csv_as_dict(path)

def calculate_exact_match(pred: Any, gt: Any) -> bool:
    """Calculate exact match between prediction and ground truth."""
    return str(pred) == str(gt)

def calculate_f1_score(pred: Any, gt: Any) -> float:
    """Calculate F1 score (simplified for this context)."""
    if pred == gt:
        return 1.0
    return 0.0

def compute_mcnemar_test(results: List[Dict[str, Any]]) -> float:
    """
    Compute McNemar's test p-value.
    Simplified implementation for binary classification comparison.
    """
    # Count concordant and discordant pairs
    n_01 = 0  # Symbolic wrong, VLM right
    n_10 = 0  # Symbolic right, VLM wrong
    
    for r in results:
        sym_correct = r.get('symbolic_correct', False)
        vlm_correct = r.get('vlm_correct', False)
        
        if not sym_correct and vlm_correct:
            n_01 += 1
        elif sym_correct and not vlm_correct:
            n_10 += 1
    
    if n_01 + n_10 == 0:
        return 1.0  # No discordant pairs
    
    # McNemar's test statistic (chi-squared with continuity correction)
    stat = (abs(n_01 - n_10) - 1) ** 2 / (n_01 + n_10)
    
    # Approximate p-value using chi-squared distribution with 1 df
    # Using a simple approximation for p-value
    p_value = math.exp(-stat / 2) if stat > 0 else 1.0
    return min(p_value, 1.0)

def compute_row_metrics(pred: Dict[str, Any], gt: Dict[str, Any], vlm: Dict[str, Any]) -> Dict[str, Any]:
    """Compute metrics for a single row."""
    scene_id = pred.get('scene_id')
    symbolic_pred = pred.get('prediction')
    vlm_pred = vlm.get(scene_id, {}).get('prediction')
    ground_truth = gt.get(scene_id, {}).get('label')
    
    exact_match = calculate_exact_match(symbolic_pred, ground_truth)
    f1 = calculate_f1_score(symbolic_pred, ground_truth)
    
    return {
        'scene_id': scene_id,
        'symbolic_pred': symbolic_pred,
        'vlm_pred': vlm_pred,
        'ground_truth': ground_truth,
        'exact_match': exact_match,
        'f1': f1,
        'symbolic_correct': exact_match,
        'vlm_correct': calculate_exact_match(vlm_pred, ground_truth) if vlm_pred else False
    }

def main():
    """Generate benchmark results CSV."""
    # Define paths
    predictions_path = config.DATA_DERIVED / "predictions.jsonl"
    ground_truth_path = config.DATA_RAW / "ground_truth.csv"
    vlm_baseline_path = config.DATA_RAW / "vlm_baseline.csv"
    latency_path = config.DATA_DERIVED / "latency_log.jsonl"
    output_path = config.DATA_RESULTS / "benchmark_results.csv"
    
    # Load data
    predictions = load_predictions(predictions_path)
    ground_truth = load_ground_truth(ground_truth_path)
    vlm_baseline = load_vlm_baseline(vlm_baseline_path)
    latencies = load_latency_log(latency_path)
    
    # Compute metrics
    results = []
    for scene_id, pred in predictions.items():
        row = compute_row_metrics(pred, ground_truth, vlm_baseline)
        row['latency_ms'] = latencies.get(scene_id, 0)
        results.append(row)
    
    # Compute overall p-value
    p_value = compute_mcnemar_test(results)
    
    # Write results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'scene_id', 'symbolic_pred', 'vlm_pred', 'ground_truth',
            'exact_match', 'f1', 'latency_ms', 'status', 'p_value'
        ])
        writer.writeheader()
        for row in results:
            row['status'] = 'Success' if row['exact_match'] else 'Mismatch'
            row['p_value'] = p_value
            writer.writerow(row)
    
    print(f"Benchmark results written to {output_path}")

if __name__ == "__main__":
    main()

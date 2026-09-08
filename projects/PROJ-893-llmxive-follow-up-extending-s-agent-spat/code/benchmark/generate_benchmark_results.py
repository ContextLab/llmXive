"""
T019 Implementation: Generate benchmark_results.csv
Links scene IDs, predictions, ground truth, and metrics.
"""
import os
import sys
import csv
import json
import math
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import CONFIG
from benchmark.metrics import calculate_exact_match, calculate_f1_score

def load_jsonl(path: Path) -> list:
    """Load a JSONL file into a list of dicts."""
    data = []
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data

def load_csv_as_dict(path: Path, key_col: str = 'scene_id') -> dict:
    """Load a CSV file into a dictionary keyed by a specific column."""
    data = {}
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row.get(key_col)
            if key:
                data[key] = row
    return data

def load_predictions(path: Path) -> dict:
    """Load predictions.jsonl into a dict keyed by scene_id."""
    rows = load_jsonl(path)
    return {row['scene_id']: row for row in rows}

def load_ground_truth(path: Path) -> dict:
    """Load ground truth CSV (merged.csv or similar) into a dict keyed by scene_id."""
    # Assuming the ground truth CSV has a 'scene_id' column and a 'label' or 'answer' column
    # Adjust key based on actual ground truth schema if necessary. 
    # Based on T006b, we load the baseline, but for GT we assume a standard format.
    # If merged.csv contains both, we might need to parse carefully.
    # For now, assume it has 'scene_id' and 'ground_truth' (or 'label').
    return load_csv_as_dict(path, key_col='scene_id')

def load_latency_log(path: Path) -> dict:
    """Load latency_log.jsonl into a dict keyed by scene_id."""
    rows = load_jsonl(path)
    return {row['scene_id']: row for row in rows}

def load_vlm_baseline(path: Path) -> dict:
    """Load VLM baseline predictions."""
    # Assuming it's a CSV or JSONL with scene_id and prediction
    if path.suffix == '.csv':
        return load_csv_as_dict(path, key_col='scene_id')
    else:
        rows = load_jsonl(path)
        return {row['scene_id']: row for row in rows}

def calculate_exact_match(pred: Any, gt: Any) -> bool:
    """Calculate exact match between prediction and ground truth."""
    if pred is None or gt is None:
        return False
    # Normalize for comparison
    p_str = str(pred).strip().lower()
    g_str = str(gt).strip().lower()
    return p_str == g_str

def calculate_f1_score(pred: Any, gt: Any) -> float:
    """
    Calculate F1 score.
    For exact match tasks, F1 is often 1.0 if match, 0.0 otherwise.
    If pred/gt are sets or lists, compute set-based F1.
    """
    if pred is None or gt is None:
        return 0.0
    
    p_str = str(pred).strip().lower()
    g_str = str(gt).strip().lower()
    
    if p_str == g_str:
        return 1.0
    
    # If they are lists/sets represented as strings, try to parse
    # Simple heuristic: if they look like lists
    try:
        p_list = json.loads(p_str) if isinstance(p_str, str) else p_str
        g_list = json.loads(g_str) if isinstance(g_str, str) else g_str
        
        if isinstance(p_list, list) and isinstance(g_list, list):
            p_set = set(p_list)
            g_set = set(g_list)
            intersection = p_set.intersection(g_set)
            union = p_set.union(g_set)
            
            if not union:
                return 0.0
            precision = len(intersection) / len(p_set) if p_set else 0.0
            recall = len(intersection) / len(g_set) if g_set else 0.0
            
            if precision + recall == 0:
                return 0.0
            return 2 * (precision * recall) / (precision + recall)
    except (json.JSONDecodeError, TypeError):
        pass
    
    return 0.0

def compute_row_metrics(scene_id: str, pred_row: dict, gt_row: dict, vlm_row: dict, latency_row: dict) -> dict:
    """Compute metrics for a single row."""
    symbolic_pred = pred_row.get('prediction') if pred_row else None
    ground_truth = gt_row.get('label') or gt_row.get('ground_truth') or gt_row.get('answer') if gt_row else None
    vlm_pred = vlm_row.get('prediction') or vlm_row.get('vlm_prediction') if vlm_row else None
    latency_ms = latency_row.get('latency_ms') if latency_row else None

    exact_match = calculate_exact_match(symbolic_pred, ground_truth)
    f1 = calculate_f1_score(symbolic_pred, ground_truth)

    status = "Success"
    if pred_row and pred_row.get('status') == 'No Solution':
        status = "No Solution"
    elif pred_row and pred_row.get('status') == 'Ambiguous':
        status = "Ambiguous"
    
    return {
        'scene_id': scene_id,
        'symbolic_pred': symbolic_pred,
        'vlm_pred': vlm_pred,
        'ground_truth': ground_truth,
        'exact_match': int(exact_match),
        'f1': round(f1, 4),
        'latency_ms': latency_ms,
        'status': status
    }

def main():
    """
    Main entry point for T019.
    Generates data/results/benchmark_results.csv
    """
    # Define paths based on CONFIG
    predictions_path = CONFIG.DATA_DERIVED / "predictions.jsonl"
    latency_path = CONFIG.DATA_DERIVED / "latency_log.jsonl"
    # Ground truth is often in the raw data or a specific derived file. 
    # Based on T006b, we might have a specific ground truth file. 
    # Assuming merged.csv in raw contains the ground truth labels.
    # If T006b produced a specific ground truth file, use that.
    # For now, checking common locations.
    gt_path = CONFIG.DATA_RAW / "merged.csv" 
    if not gt_path.exists():
        # Fallback if merged.csv isn't the GT source, maybe a specific GT file
        # But per spec, we link to existing data.
        raise FileNotFoundError(f"Ground truth file not found at {gt_path}")

    vlm_baseline_path = CONFIG.DATA_RAW / "vlm_baseline.csv" # Assumed location based on T006b output
    if not vlm_baseline_path.exists():
        # If not found in raw, check if it was generated elsewhere or named differently
        # T006b says "fetch or load pre-computed VLM baseline"
        # Let's assume it's available as per the task description
        raise FileNotFoundError(f"VLM baseline file not found at {vlm_baseline_path}")

    output_path = CONFIG.DATA_RESULTS / "benchmark_results.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loading predictions from {predictions_path}...")
    predictions = load_predictions(predictions_path)
    
    print(f"Loading latency logs from {latency_path}...")
    latencies = load_latency_log(latency_path)

    print(f"Loading ground truth from {gt_path}...")
    ground_truths = load_ground_truth(gt_path)

    print(f"Loading VLM baseline from {vlm_baseline_path}...")
    vlm_baselines = load_vlm_baseline(vlm_baseline_path)

    # Get all scene IDs from predictions (as the primary source)
    scene_ids = list(predictions.keys())
    
    results = []
    for sid in scene_ids:
        pred = predictions.get(sid, {})
        gt = ground_truths.get(sid, {})
        vlm = vlm_baselines.get(sid, {})
        lat = latencies.get(sid, {})
        
        row = compute_row_metrics(sid, pred, gt, vlm, lat)
        results.append(row)

    # Write to CSV
    fieldnames = ['scene_id', 'symbolic_pred', 'vlm_pred', 'ground_truth', 'exact_match', 'f1', 'latency_ms', 'status']
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"Successfully wrote benchmark results to {output_path}")
    print(f"Total rows: {len(results)}")

if __name__ == "__main__":
    main()

import os
import sys
import json
import csv
import math
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import config
from scipy import stats

def load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """Load a JSONL file into a list of dicts."""
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def load_csv(file_path: Path) -> List[Dict[str, str]]:
    """Load a CSV file into a list of dicts."""
    data = []
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def calculate_exact_match(pred: Any, truth: Any) -> bool:
    """Calculate exact match between prediction and ground truth."""
    return pred == truth

def calculate_f1_score(pred: Any, truth: Any) -> float:
    """Calculate F1 score. For binary or exact match tasks, F1 is 1 if match, 0 otherwise."""
    return 1.0 if pred == truth else 0.0

def calculate_latency_stats(latencies: List[float]) -> Dict[str, float]:
    """Calculate latency statistics."""
    if not latencies:
        return {"median": 0.0, "mean": 0.0, "std": 0.0}
    return {
        "median": float(stats.median(latencies)),
        "mean": float(stats.mean(latencies)),
        "std": float(stats.std(latencies))
    }

def compute_mcnemar_test(results: List[Dict[str, bool]]) -> Dict[str, float]:
    """
    Compute McNemar's test for paired nominal data.
    results: list of dicts with keys 'symbolic' (bool), 'vlm' (bool)
    """
    # Construct contingency table
    # a: both correct, b: symbolic correct vlm wrong, c: symbolic wrong vlm correct, d: both wrong
    a = b = c = d = 0
    for r in results:
        sym = r.get('symbolic', False)
        vlm = r.get('vlm', False)
        if sym and vlm:
            a += 1
        elif sym and not vlm:
            b += 1
        elif not sym and vlm:
            c += 1
        else:
            d += 1
    
    if b + c == 0:
        return {"statistic": 0.0, "pvalue": 1.0}
    
    # McNemar's chi-squared statistic (with continuity correction)
    statistic = (abs(b - c) - 1) ** 2 / (b + c)
    pvalue = 1 - stats.chi2.cdf(statistic, 1)
    return {"statistic": float(statistic), "pvalue": float(pvalue)}

def compute_metrics(predictions_path: Path, baseline_path: Path, ground_truth_path: Path, output_path: Path):
    """
    Compute benchmark metrics and save to CSV.
    """
    predictions = load_jsonl(predictions_path)
    baseline = load_csv(baseline_path)
    ground_truth = load_csv(ground_truth_path)

    # Index by scene_id
    gt_map = {row['scene_id']: row['label'] for row in ground_truth}
    vlm_map = {row['scene_id']: row['prediction'] for row in baseline}

    results = []
    latencies = []
    mcnemar_data = []

    for pred_row in predictions:
        scene_id = pred_row['scene_id']
        symbolic_pred = pred_row.get('prediction')
        status = pred_row.get('status')
        latency = pred_row.get('latency_ms', 0)

        if scene_id not in gt_map:
            continue

        ground_truth_val = gt_map[scene_id]
        vlm_pred = vlm_map.get(scene_id, None)

        exact_match = calculate_exact_match(symbolic_pred, ground_truth_val)
        f1 = calculate_f1_score(symbolic_pred, ground_truth_val)
        latencies.append(latency)

        mcnemar_data.append({
            'symbolic': exact_match,
            'vlm': calculate_exact_match(vlm_pred, ground_truth_val) if vlm_pred else False
        })

        results.append({
            'scene_id': scene_id,
            'symbolic_pred': symbolic_pred,
            'vlm_pred': vlm_pred,
            'ground_truth': ground_truth_val,
            'exact_match': exact_match,
            'f1': f1,
            'latency_ms': latency,
            'status': status
        })

    # Calculate aggregate stats
    latency_stats = calculate_latency_stats(latencies)
    mcnemar_stats = compute_mcnemar_test(mcnemar_data)

    # Save detailed results
    with open(output_path, 'w', newline='') as f:
        fieldnames = ['scene_id', 'symbolic_pred', 'vlm_pred', 'ground_truth', 'exact_match', 'f1', 'latency_ms', 'status']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"Metrics saved to {output_path}")
    print(f"Median Latency: {latency_stats['median']} ms")
    print(f"McNemar P-Value: {mcnemar_stats['pvalue']}")

def main():
    parser = argparse.ArgumentParser(description="Compute benchmark metrics")
    parser.add_argument("--predictions", type=str, required=True, help="Path to predictions.jsonl")
    parser.add_argument("--baseline", type=str, required=True, help="Path to VLM baseline CSV")
    parser.add_argument("--ground_truth", type=str, required=True, help="Path to ground truth CSV")
    parser.add_argument("--output", type=str, required=True, help="Path to output CSV")
    args = parser.parse_args()

    compute_metrics(
        Path(args.predictions),
        Path(args.baseline),
        Path(args.ground_truth),
        Path(args.output)
    )

if __name__ == "__main__":
    main()

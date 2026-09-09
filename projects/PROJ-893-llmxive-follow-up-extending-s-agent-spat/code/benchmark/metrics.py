import os
import sys
import json
import csv
import math
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from scipy import stats

# Attempt to import config, but handle missing/changed API gracefully
try:
    from config import Config
    # If Config exists but lacks specific attrs, we rely on __getattr__ if implemented
    # or we just use it as a namespace.
except ImportError:
    Config = None

def load_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """Load a JSONL file into a list of dictionaries."""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data

def load_csv(file_path: str) -> List[Dict[str, str]]:
    """Load a CSV file into a list of dictionaries."""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def calculate_exact_match(symbolic_pred: Any, ground_truth: Any) -> bool:
    """Calculate exact match between symbolic prediction and ground truth."""
    # Normalize types for comparison
    try:
        s = str(symbolic_pred).strip().lower()
        g = str(ground_truth).strip().lower()
        return s == g
    except Exception:
        return False

def calculate_f1_score(symbolic_pred: Any, ground_truth: Any) -> float:
    """
    Calculate F1 score.
    For exact match tasks, F1 is often 1.0 if match, 0.0 if not.
    If partial credit is needed, this would require specific logic.
    Assuming binary classification (Match/No Match) for F1 calculation here.
    """
    match = calculate_exact_match(symbolic_pred, ground_truth)
    if match:
        # Precision=1, Recall=1 -> F1=1
        return 1.0
    else:
        # Precision=0, Recall=0 -> F1=0 (or undefined, handled as 0)
        return 0.0

def calculate_latency_stats(latency_log: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate latency statistics from the log."""
    latencies = [entry['latency_ms'] for entry in latency_log if 'latency_ms' in entry]
    if not latencies:
        return {'median': 0.0, 'mean': 0.0, 'std': 0.0}

    latencies.sort()
    n = len(latencies)
    median = latencies[n // 2] if n % 2 == 1 else (latencies[n // 2 - 1] + latencies[n // 2]) / 2
    mean = sum(latencies) / n
    variance = sum((x - mean) ** 2 for x in latencies) / n
    std = math.sqrt(variance)

    return {
        'median': median,
        'mean': mean,
        'std': std
    }

def compute_mcnemar_test(results: List[Dict[str, Any]]) -> Tuple[float, float]:
    """
    Compute McNemar's test for paired nominal data.
    Input: List of dicts with keys 'symbolic_pred', 'vlm_pred', 'ground_truth'.
    Returns: (chi2_statistic, p_value)
    """
    # Contingency table:
    #           VLM Correct | VLM Incorrect
    # Sym Correct    a           b
    # Sym Incorrect  c           d
    # We care about discordant pairs (b and c).
    
    b = 0 # Sym Correct, VLM Incorrect
    c = 0 # Sym Incorrect, VLM Correct

    for row in results:
        sym_pred = row.get('symbolic_pred')
        vlm_pred = row.get('vlm_pred')
        gt = row.get('ground_truth')

        # Determine correctness
        sym_correct = calculate_exact_match(sym_pred, gt)
        vlm_correct = calculate_exact_match(vlm_pred, gt)

        if sym_correct and not vlm_correct:
            b += 1
        elif not sym_correct and vlm_correct:
            c += 1

    # McNemar's test statistic: (|b - c| - 1)^2 / (b + c) with continuity correction
    # If b + c == 0, chi2 is 0, p is 1.0
    if b + c == 0:
        return 0.0, 1.0

    chi2 = (abs(b - c) - 1) ** 2 / (b + c)
    # p-value from chi-square distribution with 1 degree of freedom
    p_value = 1.0 - stats.chi2.cdf(chi2, 1)

    return chi2, p_value

def compute_metrics(results: List[Dict[str, Any]]) -> Dict[str, float]:
    """Compute aggregate metrics (Accuracy, F1) for the dataset."""
    if not results:
        return {'accuracy': 0.0, 'f1': 0.0}

    correct = 0
    f1_sum = 0.0

    for row in results:
        sym_pred = row.get('symbolic_pred')
        gt = row.get('ground_truth')
        
        if calculate_exact_match(sym_pred, gt):
            correct += 1
        
        f1_sum += calculate_f1_score(sym_pred, gt)

    accuracy = correct / len(results)
    f1_avg = f1_sum / len(results)

    return {
        'accuracy': accuracy,
        'f1': f1_avg
    }

def main():
    parser = argparse.ArgumentParser(description="Compute benchmark metrics and statistical significance.")
    parser.add_argument('--predictions', type=str, required=True, help="Path to predictions.jsonl")
    parser.add_argument('--baseline', type=str, required=True, help="Path to VLM baseline CSV (merged.csv)")
    parser.add_argument('--output', type=str, required=True, help="Path to output benchmark_results.csv")
    parser.add_argument('--latency', type=str, default="data/derived/latency_log.jsonl", help="Path to latency_log.jsonl")
    parser.add_argument('--ground_truth', type=str, default="data/raw/ground_truth.csv", help="Path to ground truth CSV")
    
    args = parser.parse_args()

    # Load data
    print(f"Loading predictions from {args.predictions}...")
    predictions = load_jsonl(args.predictions)
    
    print(f"Loading VLM baseline from {args.baseline}...")
    # Assume baseline CSV has columns: scene_id, vlm_pred, ground_truth (or similar)
    # We need to join by scene_id
    baseline_data = load_csv(args.baseline)
    baseline_map = {row['scene_id']: row for row in baseline_data}

    print(f"Loading ground truth from {args.ground_truth}...")
    # Load ground truth if not already in baseline/predictions
    # Assuming ground_truth CSV has scene_id, ground_truth
    gt_data = load_csv(args.ground_truth)
    gt_map = {row['scene_id']: row['ground_truth'] for row in gt_data}

    print(f"Loading latency log from {args.latency}...")
    latency_log = load_jsonl(args.latency)
    latency_map = {entry['scene_id']: entry['latency_ms'] for entry in latency_log}

    # Merge data
    results = []
    for pred in predictions:
        scene_id = pred.get('scene_id')
        if not scene_id:
            continue

        symbolic_pred = pred.get('prediction')
        status = pred.get('status', 'Success')
        
        vlm_pred = baseline_map.get(scene_id, {}).get('vlm_prediction')
        # Fallback to ground_truth column if vlm_prediction missing in baseline
        if not vlm_pred:
            vlm_pred = baseline_map.get(scene_id, {}).get('ground_truth') 
        
        ground_truth = gt_map.get(scene_id)
        # If no explicit GT file, maybe it's in the baseline?
        if not ground_truth:
            ground_truth = baseline_map.get(scene_id, {}).get('ground_truth')

        if not ground_truth:
            # Skip if no ground truth
            continue

        latency_ms = latency_map.get(scene_id, 0.0)

        exact_match = calculate_exact_match(symbolic_pred, ground_truth)
        f1 = calculate_f1_score(symbolic_pred, ground_truth)

        results.append({
            'scene_id': scene_id,
            'symbolic_pred': symbolic_pred,
            'vlm_pred': vlm_pred,
            'ground_truth': ground_truth,
            'exact_match': exact_match,
            'f1': f1,
            'latency_ms': latency_ms,
            'status': status
        })

    # Compute McNemar's test
    print("Computing McNemar's test...")
    chi2, p_value = compute_mcnemar_test(results)
    print(f"McNemar's Test: Chi2={chi2:.4f}, p-value={p_value:.6f}")

    # Add p_value to every row? Or just one summary row?
    # The task says: "include the calculated p-value in the final ... column p_value"
    # This implies every row gets the same p_value, or the file has a specific structure.
    # Given the schema in T005d (benchmark_result.schema.yaml) expects per-scene metrics,
    # and p_value is a global statistic, we will include it in every row for traceability
    # or assume the schema allows a global column. The prompt says "column p_value",
    # implying a CSV column. We will add it to every row.
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ['scene_id', 'symbolic_pred', 'vlm_pred', 'ground_truth', 'exact_match', 'f1', 'latency_ms', 'status', 'p_value']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            row['p_value'] = p_value
            writer.writerow(row)

    print(f"Benchmark results written to {args.output}")

    # Summary report
    metrics = compute_metrics(results)
    print("\n--- Summary Report ---")
    print(f"Total Scenes: {len(results)}")
    print(f"Symbolic Accuracy: {metrics['accuracy']:.4f}")
    print(f"Symbolic F1: {metrics['f1']:.4f}")
    print(f"McNemar's p-value: {p_value:.6f}")
    print(f"Latency (Median): {calculate_latency_stats(latency_log)['median']:.2f} ms")

    # Write summary to a text file if needed, or just stdout
    # The task mentions "summary report". Let's write a simple markdown report.
    report_path = output_path.parent / "benchmark_summary.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Benchmark Summary Report\n\n")
        f.write(f"### Dataset Statistics\n")
        f.write(f"- Total Scenes: {len(results)}\n")
        f.write(f"- Symbolic Accuracy: {metrics['accuracy']:.4f}\n")
        f.write(f"- Symbolic F1 Score: {metrics['f1']:.4f}\n\n")
        f.write(f"### Statistical Significance (McNemar's Test)\n")
        f.write(f"- Chi-Square Statistic: {chi2:.4f}\n")
        f.write(f"- p-value: {p_value:.6f}\n")
        if p_value < 0.05:
            f.write(f"- **Conclusion**: The difference between Symbolic and VLM performance is statistically significant (p < 0.05).\n")
        else:
            f.write(f"- **Conclusion**: No statistically significant difference detected (p >= 0.05).\n")
        f.write(f"\n### Latency Analysis\n")
        lat_stats = calculate_latency_stats(latency_log)
        f.write(f"- Median Latency: {lat_stats['median']:.2f} ms\n")
        f.write(f"- Mean Latency: {lat_stats['mean']:.2f} ms\n")
        f.write(f"- Std Dev: {lat_stats['std']:.2f} ms\n")
    
    print(f"Summary report written to {report_path}")

if __name__ == '__main__':
    main()

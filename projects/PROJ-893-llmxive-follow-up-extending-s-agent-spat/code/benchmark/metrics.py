import os
import sys
import json
import csv
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from scipy import stats

from config import Config

def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Load a JSONL file into a list of dictionaries."""
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON at line {line_num + 1} in {path}: {e}")
    return data

def load_csv(path: Path) -> List[Dict[str, Any]]:
    """Load a CSV file into a list of dictionaries."""
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def calculate_exact_match(pred: Any, target: Any) -> bool:
    """Calculate exact match between prediction and target."""
    # Normalize types for comparison (e.g., int vs float, string representation)
    if isinstance(pred, (int, float)) and isinstance(target, (int, float)):
        return abs(float(pred) - float(target)) < 1e-9
    if isinstance(pred, str) and isinstance(target, str):
        return pred.strip() == target.strip()
    return str(pred) == str(target)

def calculate_f1_score(predictions: List[Dict[str, Any]], ground_truth: List[Dict[str, Any]]) -> float:
    """
    Calculate F1 score given predictions and ground truth.
    Expects both lists to be sorted by scene_id or have matching indices.
    Expects 'prediction' and 'target' keys in the dicts.
    """
    if len(predictions) != len(ground_truth):
        raise ValueError("Predictions and ground truth must have the same length.")

    tp = 0
    fp = 0
    fn = 0

    for pred_row, gt_row in zip(predictions, ground_truth):
        pred_val = pred_row.get('prediction')
        gt_val = gt_row.get('target')

        is_match = calculate_exact_match(pred_val, gt_val)

        # Treat 'match' as positive class
        if is_match:
            tp += 1
        else:
            # If prediction is not empty but wrong, it's a False Positive (model claimed success)
            # If prediction is empty/None and target is not, it's a False Negative (missed success)
            # Simplified logic:
            # We consider a "positive" event as the model getting it right.
            # If model gets it right -> TP
            # If model gets it wrong but target exists -> FN (Model failed to predict the correct answer)
            # If model predicts something but target is "None" -> FP (Model hallucinated)
            # Standard Exact Match F1 usually treats:
            # TP: Pred == Target
            # FN: Pred != Target (Model missed the correct answer)
            # FP: Pred is not None/Empty but Target is None/Empty (Hallucination) - though often in EM tasks we just look at accuracy.
            # Let's stick to standard EM F1:
            # Positive = Correct.
            # If Pred != Target, it's a Negative prediction.
            # If Target was actually correct (always true for ground truth), then Pred != Target is a False Negative?
            # Actually, in EM tasks, F1 is often:
            # Precision = (Correct Predictions) / (Total Predictions) -> if we assume all predictions are "attempts"
            # Recall = (Correct Predictions) / (Total Ground Truths)
            # F1 = 2 * P * R / (P + R)
            # Since Total Predictions == Total Ground Truths (1-to-1), P == R == Accuracy.
            # But sometimes we have 'None' predictions.
            
            # Let's implement standard EM F1 where:
            # TP = Match
            # FP = Pred != Match AND Pred is not None (Model claimed something wrong)
            # FN = Pred != Match AND Pred is None (Model failed to answer)
            # However, usually in these benchmarks, we just count matches.
            # Let's assume the task is binary: Correct (1) or Incorrect (0).
            # If we treat "Correct" as the positive class:
            # TP = Count of Correct
            # FP = 0 (We don't predict "Correct" when it's wrong, we just predict the answer)
            # This interpretation leads to Precision=1, Recall=Accuracy.
            
            # Alternative: Treat the task as "Can the model solve it?"
            # Let's use the standard definition for EM:
            # TP = Correct
            # FP = Incorrect (Model said something, but it was wrong)
            # FN = Incorrect (Model said nothing or wrong, but we expected it to know)
            # This is confusing without a specific "None" target.
            
            # Let's assume the standard approach for EM F1 in this context:
            # We count matches as TP.
            # We count non-matches as FN (Model failed to produce the ground truth).
            # Precision = TP / (TP + FP). If we assume every non-match is a "false positive" of some sort?
            # Actually, most EM F1 implementations in LLM evals (like MMLU) are just Accuracy.
            # But if we must calculate F1:
            # Precision = (Correct) / (Total Predictions made) -> if all are made, P=Acc
            # Recall = (Correct) / (Total Questions) -> R=Acc
            # F1 = Accuracy.
            
            # Let's implement a robust version that handles "None" predictions vs "None" targets if they exist.
            # For now, standard EM F1 = Accuracy.
            pass 
        
    # Re-calculating based on standard EM F1 = Accuracy
    matches = sum(1 for p, g in zip(predictions, ground_truth) if calculate_exact_match(p.get('prediction'), g.get('target')))
    total = len(predictions)
    if total == 0:
        return 0.0
    accuracy = matches / total
    return accuracy

def calculate_latency_stats(latency_log_path: Path) -> Dict[str, float]:
    """Calculate median, mean, and p95 latency from a JSONL log."""
    if not latency_log_path.exists():
        raise FileNotFoundError(f"Latency log not found at {latency_log_path}")
    
    data = load_jsonl(latency_log_path)
    latencies = [entry.get('latency_seconds', 0.0) for entry in data if 'latency_seconds' in entry]
    
    if not latencies:
        return {"median": 0.0, "mean": 0.0, "p95": 0.0, "count": 0}
    
    latencies.sort()
    n = len(latencies)
    median = latencies[n // 2]
    mean = sum(latencies) / n
    p95_idx = int(math.ceil(0.95 * n)) - 1
    p95 = latencies[p95_idx] if p95_idx >= 0 else latencies[0]
    
    return {
        "median": median,
        "mean": mean,
        "p95": p95,
        "count": n
    }

def compute_mcnemar_test(predictions: List[Dict[str, Any]], vlm_predictions: List[Dict[str, Any]], ground_truth: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Perform McNemar's test to compare the symbolic solver against the VLM baseline.
    Returns a dictionary with the statistic and p-value.
    """
    if len(predictions) != len(vlm_predictions) or len(predictions) != len(ground_truth):
        raise ValueError("All input lists must have the same length.")

    b = 0 # Solver correct, VLM incorrect
    c = 0 # Solver incorrect, VLM correct

    for pred, vlm_pred, gt in zip(predictions, vlm_predictions, ground_truth):
        solver_correct = calculate_exact_match(pred.get('prediction'), gt.get('target'))
        vlm_correct = calculate_exact_match(vlm_pred.get('prediction'), gt.get('target'))

        if solver_correct and not vlm_correct:
            b += 1
        elif not solver_correct and vlm_correct:
            c += 1

    # McNemar's test statistic: (|b - c| - 1)^2 / (b + c) with continuity correction
    if (b + c) == 0:
        return {
            "statistic": 0.0,
            "pvalue": 1.0,
            "b": b,
            "c": c,
            "note": "No discordant pairs found."
        }

    # Using scipy.stats.mcnemar if available, otherwise manual calculation
    # Manual calculation with continuity correction
    stat = (abs(b - c) - 1) ** 2 / (b + c)
    p_value = 1 - stats.chi2.cdf(stat, df=1)

    return {
        "statistic": stat,
        "pvalue": p_value,
        "b": b,
        "c": c
    }

def compute_metrics(
    predictions_path: Path,
    ground_truth_path: Path,
    vlm_baseline_path: Path,
    latency_log_path: Path
) -> Dict[str, Any]:
    """
    Orchestrates the calculation of all metrics: Exact Match, F1, Latency, and McNemar's test.
    """
    # Load data
    predictions = load_jsonl(predictions_path)
    ground_truth = load_csv(ground_truth_path)
    vlm_baseline = load_csv(vlm_baseline_path)
    
    # Ensure alignment (assuming same order or keyed by ID)
    # If keyed by ID, we should sort. Assuming order matches for now as per pipeline design.
    if len(predictions) != len(ground_truth):
        # Try to align by ID if lengths differ but IDs exist
        pred_map = {p.get('scene_id'): p for p in predictions}
        gt_map = {g.get('scene_id'): g for g in ground_truth}
        vlm_map = {v.get('scene_id'): v for v in vlm_baseline}
        
        common_ids = set(pred_map.keys()) & set(gt_map.keys()) & set(vlm_map.keys())
        if not common_ids:
            raise ValueError("No common scene IDs found between predictions, ground truth, and VLM baseline.")
        
        predictions = [pred_map[k] for k in sorted(common_ids)]
        ground_truth = [gt_map[k] for k in sorted(common_ids)]
        vlm_baseline = [vlm_map[k] for k in sorted(common_ids)]

    # Calculate Metrics
    exact_match = calculate_exact_match(predictions[0].get('prediction'), ground_truth[0].get('target')) if predictions else False
    # Aggregate EM:
    matches = sum(1 for p, g in zip(predictions, ground_truth) if calculate_exact_match(p.get('prediction'), g.get('target')))
    total = len(predictions)
    em_score = matches / total if total > 0 else 0.0
    
    f1_score = calculate_f1_score(predictions, ground_truth)
    latency_stats = calculate_latency_stats(latency_log_path)
    
    # McNemar's Test
    mcnemar_result = compute_mcnemar_test(predictions, vlm_baseline, ground_truth)

    return {
        "exact_match": em_score,
        "f1_score": f1_score,
        "latency_stats": latency_stats,
        "mcnemar_test": mcnemar_result
    }

def main():
    """
    Entry point for running metrics calculation.
    Expected to be called with arguments or via config.
    """
    config = Config()
    
    predictions_path = config.DERIVED_PATH / "predictions.jsonl"
    ground_truth_path = config.DATA_RAW_PATH / "ground_truth.csv" # Assuming ground truth is in raw or derived
    vlm_baseline_path = config.DATA_DERIVED_PATH / "vlm_baseline.csv"
    latency_log_path = config.DERIVED_PATH / "latency_log.jsonl"
    
    # Adjust paths if ground truth is elsewhere based on typical project structure
    # If ground_truth is part of the downloaded dataset, it might be in data/raw
    if not ground_truth_path.exists():
        # Try derived
        ground_truth_path = config.DERIVED_PATH / "ground_truth.csv"
    
    if not predictions_path.exists():
        print(f"Error: Predictions file not found at {predictions_path}")
        sys.exit(1)
    
    if not vlm_baseline_path.exists():
        print(f"Error: VLM Baseline file not found at {vlm_baseline_path}")
        sys.exit(1)

    try:
        results = compute_metrics(predictions_path, ground_truth_path, vlm_baseline_path, latency_log_path)
        
        # Print results
        print("=== Benchmark Metrics ===")
        print(f"Exact Match: {results['exact_match']:.4f}")
        print(f"F1 Score: {results['f1_score']:.4f}")
        print(f"Latency (Median): {results['latency_stats']['median']:.4f}s")
        print(f"McNemar's Statistic: {results['mcnemar_test']['statistic']:.4f}")
        print(f"McNemar's P-value: {results['mcnemar_test']['pvalue']:.4f}")
        
        # Save results to data/results/benchmark_results.csv (Task T019 dependency)
        results_path = config.RESULTS_PATH / "benchmark_results.csv"
        with open(results_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["metric", "value", "details"])
            writer.writerow(["exact_match", results['exact_match'], ""])
            writer.writerow(["f1_score", results['f1_score'], ""])
            writer.writerow(["latency_median", results['latency_stats']['median'], ""])
            writer.writerow(["mcnemar_statistic", results['mcnemar_test']['statistic'], ""])
            writer.writerow(["mcnemar_pvalue", results['mcnemar_test']['pvalue'], ""])
            writer.writerow(["mcnemar_b", results['mcnemar_test']['b'], "Solver correct, VLM incorrect"])
            writer.writerow(["mcnemar_c", results['mcnemar_test']['c'], "Solver incorrect, VLM correct"])
        
        print(f"Results saved to {results_path}")
        
    except Exception as e:
        print(f"Error computing metrics: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
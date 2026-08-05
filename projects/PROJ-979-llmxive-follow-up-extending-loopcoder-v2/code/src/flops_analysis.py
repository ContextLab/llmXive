"""
FLOPs Analysis and Non-Inferiority Testing Module.

This module implements the unified verification step for FLOPs savings
and non-inferiority testing as required by T021b.
"""

import csv
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import math

from src.utils import calculate_flops

logger = logging.getLogger(__name__)

def load_router_predictions(filepath: str) -> List[Dict[str, Any]]:
    """
    Load router predictions from CSV.

    Expected columns: task_id, predicted_k, actual_k, accuracy
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Router predictions not found at {filepath}")

    results = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                'task_id': row['task_id'],
                'predicted_k': int(row['predicted_k']),
                'actual_k': int(row['actual_k']),
                'accuracy': row['accuracy'].lower() == 'true'
            })
    return results

def load_convergence_results(filepath: str) -> List[Dict[str, Any]]:
    """
    Load convergence results from CSV.

    Expected columns: task_id, k, output, is_correct, converged, first_correct_step
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Convergence results not found at {filepath}")

    results = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                'task_id': row['task_id'],
                'k': int(row['k']),
                'output': row['output'],
                'is_correct': row['is_correct'].lower() == 'true',
                'converged': row['converged'].lower() == 'true',
                'first_correct_step': int(row['first_correct_step']) if row['first_correct_step'] else None
            })
    return results

def align_data_for_flops(router_preds: List[Dict], convergence_data: List[Dict]) -> List[Dict]:
    """
    Align router predictions with convergence data to compute FLOPs.
    """
    # Group convergence data by task_id
    conv_by_task = {}
    for item in convergence_data:
        tid = item['task_id']
        if tid not in conv_by_task:
            conv_by_task[tid] = []
        conv_by_task[tid].append(item)

    aligned = []
    for pred in router_preds:
        tid = pred['task_id']
        if tid in conv_by_task:
            aligned.append({
                'task_id': tid,
                'predicted_k': pred['predicted_k'],
                'actual_k': pred['actual_k'],
                'accuracy': pred['accuracy'],
                'convergence_data': conv_by_task[tid]
            })
    return aligned

def calculate_flops_for_scenario(task_data: Dict, model_params: int, seq_len: int) -> float:
    """
    Calculate FLOPs for a specific scenario (predicted_k or actual_k).
    Formula: FLOPs = parameters * sequence_length * k
    """
    k = task_data['predicted_k']  # Use predicted_k for dynamic router
    return calculate_flops(model_params, seq_len, k)

def calculate_flops_dynamic_router(aligned_data: List[Dict], model_params: int, seq_len: int) -> float:
    """
    Calculate total FLOPs for the dynamic router scenario.
    """
    total_flops = 0.0
    for item in aligned_data:
        total_flops += calculate_flops_for_scenario(item, model_params, seq_len)
    return total_flops

def calculate_flops_static_baseline(aligned_data: List[Dict], model_params: int, seq_len: int, k_baseline: int) -> float:
    """
    Calculate total FLOPs for a static baseline (e.g., k=2 for all).
    """
    total_flops = 0.0
    for item in aligned_data:
        total_flops += calculate_flops(model_params, seq_len, k_baseline)
    return total_flops

def calculate_accuracy(aligned_data: List[Dict]) -> float:
    """
    Calculate accuracy based on router predictions.
    Accuracy is defined as the proportion of samples where predicted_k == actual_k.
    """
    if not aligned_data:
        return 0.0
    correct = sum(1 for item in aligned_data if item['predicted_k'] == item['actual_k'])
    return correct / len(aligned_data)

def non_inferiority_test(accuracy_router: float, accuracy_baseline: float, delta: float, samples: int) -> Tuple[float, bool]:
    """
    Perform a one-sided t-test for non-inferiority.

    Hypothesis:
      H0: accuracy_router < accuracy_baseline - delta
      H1: accuracy_router >= accuracy_baseline - delta

    Since we are comparing proportions from the same set of samples (paired),
    we use a simplified approach for the t-statistic:
    t = (diff - (-delta)) / SE

    For simplicity in this context, we assume a large enough sample size
    and use a normal approximation for the test statistic.
    """
    if samples < 2:
        return 1.0, False  # Cannot compute, not non-inferior

    diff = accuracy_router - accuracy_baseline
    # Standard error for difference in proportions (paired)
    # Approximation: SE = sqrt( (p1*(1-p1) + p2*(1-p2) + 2*Cov) / n )
    # For paired binary outcomes, Cov can be estimated, but for simplicity:
    # We use the standard error of the difference in proportions assuming independence as a conservative estimate.
    # SE = sqrt( p1(1-p1)/n + p2(1-p2)/n )
    # However, since it's paired, a better approach is McNemar's, but for t-test approximation:
    # Let's use the standard error of the difference in means (accuracy is mean of binary outcomes)
    # SE_diff = sqrt( var_router/n + var_baseline/n )
    # var = p(1-p)

    var_router = accuracy_router * (1 - accuracy_router)
    var_baseline = accuracy_baseline * (1 - accuracy_baseline)

    # If variance is 0, we can't compute t-stat properly, assume p=1 if diff >= -delta
    if var_router == 0 and var_baseline == 0:
        p_value = 0.0 if diff >= -delta else 1.0
        return p_value, diff >= -delta

    se_diff = math.sqrt((var_router + var_baseline) / samples)
    if se_diff == 0:
        p_value = 0.0 if diff >= -delta else 1.0
        return p_value, diff >= -delta

    # One-sided t-statistic
    # We test if (diff - (-delta)) / se_diff is large enough
    t_stat = (diff + delta) / se_diff

    # Approximate p-value using normal distribution (large sample)
    # CDF of standard normal at t_stat
    # Using error function approximation for CDF
    p_value = 0.5 * (1 + math.erf(-t_stat / math.sqrt(2)))

    is_non_inferior = (p_value < 0.05) and (diff >= -delta)
    return p_value, is_non_inferior

def calculate_flops_savings(
    router_preds_path: str,
    convergence_path: str,
    config_path: str,
    model_params: int,
    seq_len: int,
    output_path: str
) -> Dict[str, Any]:
    """
    Unified function to calculate FLOPs savings and perform non-inferiority test.

    Inputs:
      router_preds_path: Path to router_results.csv
      convergence_path: Path to convergence results (not strictly needed for FLOPs calc here,
                        but used for alignment if needed in future extensions)
      config_path: Path to config.json containing 'delta'
      model_params: Number of model parameters
      seq_len: Average sequence length
      output_path: Path to write flops_savings.json

    Output:
      Dict with keys: flops_saved, accuracy_diff, p_value, is_non_inferior
    """
    # Load data
    router_preds = load_router_predictions(router_preds_path)
    config = {}
    with open(config_path, 'r') as f:
        config = json.load(f)

    delta = config.get('delta', 0.02)

    # Align data
    # For FLOPs calculation, we primarily need router predictions.
    # We assume the convergence data is used to determine 'actual_k' which is already in router_preds.
    # So we can proceed with router_preds directly.
    aligned_data = []
    for pred in router_preds:
        aligned_data.append({
            'task_id': pred['task_id'],
            'predicted_k': pred['predicted_k'],
            'actual_k': pred['actual_k'],
            'accuracy': pred['accuracy']
        })

    # Calculate FLOPs
    flops_dynamic = calculate_flops_dynamic_router(aligned_data, model_params, seq_len)
    flops_static_k2 = calculate_flops_static_baseline(aligned_data, model_params, seq_len, k_baseline=2)

    flops_saved = flops_static_k2 - flops_dynamic

    # Calculate Accuracy
    # Router accuracy: proportion of correct predictions (predicted_k == actual_k)
    accuracy_router = calculate_accuracy(aligned_data)
    # Baseline accuracy: We need to define the accuracy of the static k=2 baseline.
    # For the static k=2 baseline, accuracy is the proportion of tasks where k=2 was sufficient.
    # This requires checking the convergence data for each task to see if it converged at k=2.
    # However, the router_results.csv has 'accuracy' column which indicates if predicted_k == actual_k.
    # For the baseline, we need to know if k=2 would have been correct for each task.
    # Since we don't have a direct 'was_k2_correct' column in router_results, we infer:
    # If actual_k <= 2, then k=2 would have been sufficient (correct).
    # If actual_k > 2, then k=2 would have been insufficient (incorrect).
    # So baseline accuracy is the proportion of tasks where actual_k <= 2.

    correct_baseline = sum(1 for item in aligned_data if item['actual_k'] <= 2)
    accuracy_baseline = correct_baseline / len(aligned_data) if aligned_data else 0.0

    accuracy_diff = accuracy_router - accuracy_baseline

    # Perform non-inferiority test
    p_value, is_non_inferior = non_inferiority_test(
        accuracy_router, accuracy_baseline, delta, len(aligned_data)
    )

    result = {
        'flops_saved': flops_saved,
        'accuracy_diff': accuracy_diff,
        'p_value': p_value,
        'is_non_inferior': is_non_inferior
    }

    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"FLOPs savings: {flops_saved:.2f}")
    logger.info(f"Accuracy difference: {accuracy_diff:.4f}")
    logger.info(f"P-value: {p_value:.4f}")
    logger.info(f"Is non-inferior: {is_non_inferior}")

    return result

def run_flops_analysis(
    router_preds_path: str = "data/processed/router_results.csv",
    convergence_path: str = "data/processed/convergence_results_core.csv",
    config_path: str = "data/processed/config.json",
    output_path: str = "data/processed/flops_savings.json",
    model_params: int = 1_300_000_000,  # Default for CodeLlama-1.3b
    seq_len: int = 512  # Default sequence length
) -> Dict[str, Any]:
    """
    Main entry point for running FLOPs analysis.
    """
    return calculate_flops_savings(
        router_preds_path,
        convergence_path,
        config_path,
        model_params,
        seq_len,
        output_path
    )

def main():
    """
    CLI entry point for FLOPs analysis.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Run FLOPs savings and non-inferiority test.")
    parser.add_argument("--router-preds", default="data/processed/router_results.csv", help="Path to router results CSV")
    parser.add_argument("--convergence", default="data/processed/convergence_results_core.csv", help="Path to convergence results CSV")
    parser.add_argument("--config", default="data/processed/config.json", help="Path to config JSON")
    parser.add_argument("--output", default="data/processed/flops_savings.json", help="Path to output JSON")
    parser.add_argument("--model-params", type=int, default=1_300_000_000, help="Number of model parameters")
    parser.add_argument("--seq-len", type=int, default=512, help="Sequence length")

    args = parser.parse_args()

    result = run_flops_analysis(
        router_preds_path=args.router_preds,
        convergence_path=args.convergence,
        config_path=args.config,
        output_path=args.output,
        model_params=args.model_params,
        seq_len=args.seq_len
    )

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
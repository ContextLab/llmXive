import os
import sys
import json
import argparse
import torch
import random
import numpy as np
from typing import List, Dict, Any
from transformers import BertTokenizer, BertModel
from datasets import load_dataset

# Project root import adjustment
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from models.baseline_bert import load_wic_dataset, run_frozen_bert_inference, compute_metrics
from utils.config import set_environment, get_config
from utils.logging import detect_nan_inf
from utils.framing_utils import format_associational_statement

def run_single_seed(seed: int) -> Dict[str, float]:
    """
    Run the baseline BERT evaluation on a single random seed.
    Returns a dictionary with 'accuracy' and 'macro_f1'.
    """
    set_environment(seed)
    config = get_config()
    
    print(format_associational_statement(f"--- Running Baseline Evaluation (Seed: {seed}) ---"))
    
    # Load dataset
    dataset = load_wic_dataset()
    
    # Run inference
    predictions, labels = run_frozen_bert_inference(dataset, config)
    
    # Check for NaN/Inf in predictions
    if detect_nan_inf(torch.tensor(predictions), name="Predictions"):
        raise RuntimeError(format_associational_statement(f"Seed {seed}: NaN or Inf detected in predictions."))
    
    # Compute metrics
    metrics = compute_metrics(predictions, labels)
    
    print(format_associational_statement(f"Seed {seed}: Accuracy={metrics['accuracy']:.4f}, F1={metrics['macro_f1']:.4f}"))
    return metrics

def main():
    parser = argparse.ArgumentParser(description="Run Baseline BERT Evaluation with Stability Check")
    parser.add_argument('--seeds', type=int, nargs='+', default=[42, 123, 456, 789, 1011],
                        help='List of random seeds to run for stability check')
    parser.add_argument('--variance-threshold', type=float, default=0.02,
                        help='Maximum allowed variance for metrics across seeds')
    parser.add_argument('--output-dir', type=str, default='data/results',
                        help='Directory to save output files')
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    output_path = os.path.join(args.output_dir, 'baseline_metrics.json')

    print(format_associational_statement(f"Starting baseline evaluation with seeds: {args.seeds}"))
    print(format_associational_statement(f"Stability threshold (variance): {args.variance_threshold}"))

    all_metrics = []
    accuracies = []
    f1s = []

    try:
        for seed in args.seeds:
            metrics = run_single_seed(seed)
            all_metrics.append({
                'seed': seed,
                'accuracy': metrics['accuracy'],
                'macro_f1': metrics['macro_f1']
            })
            accuracies.append(metrics['accuracy'])
            f1s.append(metrics['macro_f1'])
    except Exception as e:
        print(format_associational_statement(f"Error during evaluation: {e}"))
        sys.exit(1)

    # Calculate statistics
    mean_acc = np.mean(accuracies)
    var_acc = np.var(accuracies, ddof=0) # Population variance for stability check
    std_acc = np.std(accuracies)
    
    mean_f1 = np.mean(f1s)
    var_f1 = np.var(f1s, ddof=0)
    std_f1 = np.std(f1s)

    print(format_associational_statement(f"\n--- Stability Analysis ---"))
    print(format_associational_statement(f"Accuracy: Mean={mean_acc:.4f}, Var={var_acc:.6f}, Std={std_acc:.4f}"))
    print(format_associational_statement(f"F1 Score: Mean={mean_f1:.4f}, Var={var_f1:.6f}, Std={std_f1:.4f}"))

    # Stability Check Assertion
    if var_acc > args.variance_threshold:
        raise AssertionError(
            format_associational_statement(
                f"Stability Check FAILED: Accuracy variance ({var_acc:.6f}) exceeds threshold ({args.variance_threshold}). "
                f"The model is not stable across seeds."
            )
        )
    if var_f1 > args.variance_threshold:
        raise AssertionError(
            format_associational_statement(
                f"Stability Check FAILED: F1 variance ({var_f1:.6f}) exceeds threshold ({args.variance_threshold}). "
                f"The model is not stable across seeds."
            )
        )

    print(format_associational_statement("Stability Check PASSED."))

    # Prepare final output
    # Note: Schema requested in task: {"accuracy": float, "macro_f1": float, "seed": int, "variance_accuracy": float, "variance_macro_f1": float}
    # Since we run multiple seeds, we output per-seed metrics and summary variances.
    # We include the mean accuracy/F1 as the primary "accuracy" and "macro_f1" fields in summary, 
    # and variance fields as requested.
    final_report = {
        'seeds_used': args.seeds,
        'stability_threshold': args.variance_threshold,
        'stability_check_passed': True,
        'summary': {
            'accuracy': float(mean_acc),
            'macro_f1': float(mean_f1),
            'variance_accuracy': float(var_acc),
            'variance_macro_f1': float(var_f1)
        },
        'per_seed_metrics': all_metrics
    }

    with open(output_path, 'w') as f:
        json.dump(final_report, f, indent=2)

    print(format_associational_statement(f"Results saved to {output_path}"))

if __name__ == "__main__":
    main()
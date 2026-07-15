import os
import sys
import argparse
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional

# Constants for the sensitivity analysis
THRESHOLDS = [0.20, 0.25, 0.30, 0.35]
GROUND_TRUTH_THRESHOLD = 0.30  # Ground truth: >= 30% reduction

def calculate_reduction_metrics(baseline_df: pd.DataFrame, spiking_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the percentage reduction in perplexity and energy for each seed.
    Returns a DataFrame with seed, baseline_perplexity, spiking_perplexity,
    perplexity_reduction, baseline_energy, spiking_energy, energy_reduction.
    """
    # Merge on seed to ensure pairing
    merged = pd.merge(
        baseline_df, spiking_df, on='seed', suffixes=('_base', '_spike')
    )

    # We need the final epoch metrics for each seed (or the best epoch if early stopping)
    # Assuming the CSV contains multiple epochs, we take the last recorded epoch for simplicity
    # or the one with the lowest perplexity. For this task, we'll take the last row per seed.
    final_baseline = baseline_df.sort_values('epoch').groupby('seed').last().reset_index()
    final_spiking = spiking_df.sort_values('epoch').groupby('seed').last().reset_index()

    merged = pd.merge(
        final_baseline[['seed', 'perplexity', 'energy_per_token_kWh']],
        final_spiking[['seed', 'perplexity', 'energy_per_token_kWh']],
        on='seed',
        suffixes=('_base', '_spike')
    )

    # Calculate reductions
    # Reduction = (Baseline - Spiking) / Baseline
    # Positive value means Spiking is better (lower perplexity/energy)
    merged['perplexity_reduction'] = (merged['perplexity_base'] - merged['perplexity_spike']) / merged['perplexity_base']
    merged['energy_reduction'] = (merged['energy_per_token_kWh_base'] - merged['energy_per_token_kWh_spike']) / merged['energy_per_token_kWh_base']

    return merged

def run_sensitivity_sweep(
    baseline_path: str,
    spiking_path: str,
    output_path: str,
    thresholds: List[float] = THRESHOLDS
) -> pd.DataFrame:
    """
    Run sensitivity analysis over the specified thresholds.
    Calculates True Positive (TP), False Positive (FP), True Negative (TN), False Negative (FN)
    based on the ground truth (>= 30% reduction).

    Ground Truth: Reduction >= 0.30
    Prediction: Reduction >= threshold

    TP: GT=True, Pred=True
    FP: GT=False, Pred=True
    TN: GT=False, Pred=False
    FN: GT=True, Pred=False
    """
    if not os.path.exists(baseline_path) or not os.path.exists(spiking_path):
        raise FileNotFoundError(f"Input files not found: {baseline_path} or {spiking_path}")

    baseline_df = pd.read_csv(baseline_path)
    spiking_df = pd.read_csv(spiking_path)

    metrics_df = calculate_reduction_metrics(baseline_df, spiking_df)

    results = []

    for thresh in thresholds:
        # Ground Truth: Actual reduction >= 0.30
        gt_positive = metrics_df['energy_reduction'] >= GROUND_TRUTH_THRESHOLD
        # Prediction: Predicted reduction >= threshold
        pred_positive = metrics_df['energy_reduction'] >= thresh

        tp = (gt_positive & pred_positive).sum()
        fp = (~gt_positive & pred_positive).sum()
        tn = (~gt_positive & ~pred_positive).sum()
        fn = (gt_positive & ~pred_positive).sum()

        total = len(metrics_df)
        if total == 0:
            raise ValueError("No data points found for analysis.")

        # Calculate rates
        # Sensitivity (Recall) = TP / (TP + FN) = TP / Total_Ground_Truth_Positive
        # Specificity = TN / (TN + FP)
        # FP Rate = FP / (FP + TN)
        # FN Rate = FN / (FN + TP)

        gt_pos_count = tp + fn
        gt_neg_count = tn + fp

        sensitivity = tp / gt_pos_count if gt_pos_count > 0 else 0.0
        specificity = tn / gt_neg_count if gt_neg_count > 0 else 0.0
        fp_rate = fp / gt_neg_count if gt_neg_count > 0 else 0.0
        fn_rate = fn / gt_pos_count if gt_pos_count > 0 else 0.0

        results.append({
            'threshold': thresh,
            'tp': int(tp),
            'fp': int(fp),
            'tn': int(tn),
            'fn': int(fn),
            'sensitivity': sensitivity,
            'specificity': specificity,
            'fp_rate': fp_rate,
            'fn_rate': fn_rate,
            'total_samples': total
        })

    results_df = pd.DataFrame(results)
    results_df.to_csv(output_path, index=False)
    return results_df

def main():
    parser = argparse.ArgumentParser(description="Run sensitivity analysis for spiking transformer energy reduction.")
    parser.add_argument('--baseline', type=str, default='data/processed/baseline_metrics.csv',
                        help='Path to baseline metrics CSV')
    parser.add_argument('--spiking', type=str, default='data/processed/spiking_metrics.csv',
                        help='Path to spiking metrics CSV')
    parser.add_argument('--output', type=str, default='data/results/sensitivity_analysis.csv',
                        help='Path to save sensitivity analysis results')
    args = parser.parse_args()

    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    try:
        results = run_sensitivity_sweep(args.baseline, args.spiking, args.output)
        print(f"Sensitivity analysis complete. Results saved to {args.output}")
        print(results.to_string(index=False))
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error during analysis: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
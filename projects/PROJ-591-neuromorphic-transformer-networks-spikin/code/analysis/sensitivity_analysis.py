"""
Sensitivity Analysis for Neuromorphic Transformer Study (Task T024)

Implements a sensitivity sweep over energy reduction thresholds to calculate
False Positive (FP) and False Negative (FN) rates.

Ground Truth Definition: A model is considered a "true positive" for energy
efficiency if it achieves >= 30% reduction in energy_per_token compared to
the baseline.

Thresholds to sweep: {0.20, 0.25, 0.30, 0.35}

Output: data/results/sensitivity_analysis.csv
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from analysis.statistical_tests import load_metrics_data

def calculate_reduction_metrics(baseline_df, spiking_df):
    """
    Aggregates data by seed and calculates the mean energy reduction per seed.
    Returns a DataFrame with columns: seed, baseline_mean_energy, spiking_mean_energy, reduction_ratio.
    """
    # Group by seed to get mean energy per seed across epochs (or just use the final epoch if needed,
    # but typically we compare final performance or mean performance over stable epochs).
    # For this analysis, we will use the mean energy per token across all epochs for each seed
    # to represent the model's efficiency for that seed.

    baseline_agg = baseline_df.groupby('seed')['energy_per_token_kWh'].mean().reset_index()
    baseline_agg.columns = ['seed', 'baseline_mean_energy']

    spiking_agg = spiking_df.groupby('seed')['energy_per_token_kWh'].mean().reset_index()
    spiking_agg.columns = ['seed', 'spiking_mean_energy']

    # Merge on seed
    merged = pd.merge(baseline_agg, spiking_agg, on='seed', how='inner')

    if merged.empty:
        raise ValueError("No matching seeds found between baseline and spiking datasets.")

    # Calculate reduction ratio: (Baseline - Spiking) / Baseline
    # If Spiking is lower, this is positive.
    merged['reduction_ratio'] = (merged['baseline_mean_energy'] - merged['spiking_mean_energy']) / merged['baseline_mean_energy']

    return merged

def run_sensitivity_sweep(merged_data, thresholds):
    """
    Calculates FP and FN rates for each threshold.

    Ground Truth (GT): reduction_ratio >= 0.30 (30% reduction)
    Prediction (Pred): reduction_ratio >= threshold

    Confusion Matrix Logic:
    - True Positive (TP): GT=True AND Pred=True (Model is actually efficient, and we classified it as such)
    - False Positive (FP): GT=False AND Pred=True (Model is NOT actually efficient, but we thought it was)
    - False Negative (FN): GT=True AND Pred=False (Model IS actually efficient, but we missed it)
    - True Negative (TN): GT=False AND Pred=False

    Rates:
    - FP Rate = FP / (FP + TN)  (Proportion of inefficient models incorrectly flagged as efficient)
    - FN Rate = FN / (FN + TP)  (Proportion of efficient models incorrectly missed)
    """
    results = []

    # Define Ground Truth: >= 30% reduction
    gt_threshold = 0.30
    merged_data['is_efficient_gt'] = merged_data['reduction_ratio'] >= gt_threshold

    for thresh in thresholds:
        # Prediction based on current threshold
        merged_data['is_efficient_pred'] = merged_data['reduction_ratio'] >= thresh

        # Calculate counts
        tp = ((merged_data['is_efficient_gt']) & (merged_data['is_efficient_pred'])).sum()
        fp = ((~merged_data['is_efficient_gt']) & (merged_data['is_efficient_pred'])).sum()
        fn = ((merged_data['is_efficient_gt']) & (~merged_data['is_efficient_pred'])).sum()
        tn = ((~merged_data['is_efficient_gt']) & (~merged_data['is_efficient_pred'])).sum()

        # Calculate rates (handle division by zero)
        fp_denom = fp + tn
        fn_denom = fn + tp

        fp_rate = fp / fp_denom if fp_denom > 0 else 0.0
        fn_rate = fn / fn_denom if fn_denom > 0 else 0.0

        results.append({
            'threshold': thresh,
            'tp': int(tp),
            'fp': int(fp),
            'fn': int(fn),
            'tn': int(tn),
            'fp_rate': fp_rate,
            'fn_rate': fn_rate,
            'total_samples': len(merged_data)
        })

    return pd.DataFrame(results)

def main():
    # Define paths relative to project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    data_dir = os.path.join(project_root, "data", "processed")
    results_dir = os.path.join(project_root, "data", "results")

    baseline_path = os.path.join(data_dir, "baseline_metrics.csv")
    spiking_path = os.path.join(data_dir, "spiking_metrics.csv")
    output_path = os.path.join(results_dir, "sensitivity_analysis.csv")

    # Ensure output directory exists
    os.makedirs(results_dir, exist_ok=True)

    # Check if input files exist
    if not os.path.exists(baseline_path):
        raise FileNotFoundError(f"Baseline metrics not found at {baseline_path}. Run training tasks first.")
    if not os.path.exists(spiking_path):
        raise FileNotFoundError(f"Spiking metrics not found at {spiking_path}. Run training tasks first.")

    print(f"Loading baseline data from {baseline_path}...")
    baseline_df = load_metrics_data(baseline_path)

    print(f"Loading spiking data from {spiking_path}...")
    spiking_df = load_metrics_data(spiking_path)

    # Calculate reduction metrics
    print("Calculating energy reduction ratios per seed...")
    merged_data = calculate_reduction_metrics(baseline_df, spiking_df)

    print(f"Found {len(merged_data)} matching seeds.")
    print(f"Reduction ratios: {merged_data['reduction_ratio'].values}")

    # Define thresholds
    thresholds = [0.20, 0.25, 0.30, 0.35]

    # Run sensitivity analysis
    print(f"Running sensitivity sweep over thresholds: {thresholds}")
    sensitivity_results = run_sensitivity_sweep(merged_data, thresholds)

    # Save results
    sensitivity_results.to_csv(output_path, index=False)
    print(f"Sensitivity analysis saved to {output_path}")

    # Print summary
    print("\nSensitivity Analysis Summary:")
    print(sensitivity_results.to_string(index=False))

if __name__ == "__main__":
    main()
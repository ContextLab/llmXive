"""
Sensitivity Analysis for Meta-Critic Abstention Threshold.

This module implements a threshold sweep to evaluate the trade-off between
false positives (premature abstention) and false negatives (failure to abstain).
It generates a CSV report of metrics across a range of probability thresholds.
"""
import os
import sys
import json
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import pandas as pd

# Project imports
from config import get_path, get_config
from logging_config import setup_logging

# Setup logging
logger = setup_logging("sensitivity_analysis")

def load_simulation_results() -> pd.DataFrame:
    """
    Load the processed features and simulation results.
    Expects 'data/processed/features.parquet' as per T017.
    """
    features_path = get_path("processed_features")
    if not os.path.exists(features_path):
        raise FileNotFoundError(
            f"Required data file not found: {features_path}. "
            "Please ensure T017 (feature extraction) and T022 (evaluation) have run."
        )
    
    logger.info(f"Loading features from {features_path}")
    df = pd.read_parquet(features_path)
    
    # Validate required columns
    required_cols = ['abstention_probability', 'abstention_label']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in features: {missing}")
    
    return df

def calculate_metrics_at_threshold(
    df: pd.DataFrame, 
    threshold: float
) -> Dict[str, float]:
    """
    Calculate False Positive Rate (FPR) and False Negative Rate (FNR)
    at a specific probability threshold.

    Definitions:
    - Predicted Abstention (1) if prob >= threshold
    - True Abstention (1) if label == 1
    
    FP: Predicted 1, Actual 0 (Premature abstention)
    FN: Predicted 0, Actual 1 (Failure to abstain)
    
    FPR = FP / (FP + TN)  (Rate of abstaining when we shouldn't)
    FNR = FN / (FN + TP)  (Rate of not abstaining when we should)
    """
    # Convert to predictions
    df['predicted_abstention'] = (df['abstention_probability'] >= threshold).astype(int)
    
    # Confusion matrix components
    tp = ((df['predicted_abstention'] == 1) & (df['abstention_label'] == 1)).sum()
    tn = ((df['predicted_abstention'] == 0) & (df['abstention_label'] == 0)).sum()
    fp = ((df['predicted_abstention'] == 1) & (df['abstention_label'] == 0)).sum()
    fn = ((df['predicted_abstention'] == 0) & (df['abstention_label'] == 1)).sum()
    
    # Calculate rates (avoid division by zero)
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    
    # Additional metrics for analysis
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    accuracy = (tp + tn) / len(df) if len(df) > 0 else 0.0
    
    return {
        'threshold': threshold,
        'true_positives': int(tp),
        'true_negatives': int(tn),
        'false_positives': int(fp),
        'false_negatives': int(fn),
        'false_positive_rate': fpr,
        'false_negative_rate': fnr,
        'precision': precision,
        'recall': recall,
        'accuracy': accuracy,
        'total_samples': len(df)
    }

def run_sensitivity_sweep(
    df: pd.DataFrame,
    thresholds: List[float]
) -> List[Dict[str, Any]]:
    """
    Run the sensitivity analysis across a list of thresholds.
    """
    results = []
    for t in sorted(thresholds):
        metrics = calculate_metrics_at_threshold(df, t)
        results.append(metrics)
        logger.debug(f"Threshold {t:.2f}: FPR={metrics['false_positive_rate']:.4f}, FNR={metrics['false_negative_rate']:.4f}")
    return results

def save_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the sensitivity analysis results to a CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Sensitivity analysis results saved to {output_path}")

def plot_sensitivity_curve(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Generate a plot of FPR vs FNR (ROC-like) and Threshold vs Error Rates.
    Uses matplotlib to save figures.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("Matplotlib not installed. Skipping plot generation.")
        return

    df_res = pd.DataFrame(results)
    
    fig, axs = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1: Error Rates vs Threshold
    axs[0].plot(df_res['threshold'], df_res['false_positive_rate'], label='FPR (False Positives)', marker='o')
    axs[0].plot(df_res['threshold'], df_res['false_negative_rate'], label='FNR (False Negatives)', marker='s')
    axs[0].set_xlabel('Abstention Threshold')
    axs[0].set_ylabel('Error Rate')
    axs[0].set_title('Error Rates vs Threshold')
    axs[0].legend()
    axs[0].grid(True, alpha=0.3)
    axs[0].set_ylim(-0.05, 1.05)

    # Plot 2: Precision-Recall trade-off (or Accuracy)
    axs[1].plot(df_res['threshold'], df_res['precision'], label='Precision', marker='^')
    axs[1].plot(df_res['threshold'], df_res['recall'], label='Recall', marker='v')
    axs[1].plot(df_res['threshold'], df_res['accuracy'], label='Accuracy', marker='d')
    axs[1].set_xlabel('Abstention Threshold')
    axs[1].set_ylabel('Metric Value')
    axs[1].set_title('Precision, Recall, and Accuracy vs Threshold')
    axs[1].legend()
    axs[1].grid(True, alpha=0.3)
    axs[1].set_ylim(-0.05, 1.05)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Sensitivity plot saved to {output_path}")

def main() -> None:
    """
    Main entry point for the sensitivity analysis.
    """
    logger.info("Starting Sensitivity Analysis (T028)")
    
    # Load data
    try:
        df = load_simulation_results()
    except (FileNotFoundError, ValueError) as e:
        logger.error(str(e))
        sys.exit(1)

    logger.info(f"Loaded {len(df)} samples for analysis.")

    # Define threshold sweep range (0.0 to 1.0 with step 0.05)
    thresholds = [round(i * 0.05, 2) for i in range(21)]
    
    # Run sweep
    results = run_sensitivity_sweep(df, thresholds)
    
    # Define output paths
    config = get_config()
    results_dir = get_path("results_dir")
    csv_path = Path(results_dir) / "sensitivity_analysis.csv"
    plot_path = Path(results_dir) / "sensitivity_curve.png"

    # Save CSV
    save_results(results, csv_path)
    
    # Generate Plot
    plot_sensitivity_curve(results, plot_path)
    
    # Generate a summary JSON
    summary = {
        "num_samples": len(df),
        "thresholds_tested": len(thresholds),
        "output_csv": str(csv_path),
        "output_plot": str(plot_path),
        "optimal_threshold_candidates": []
    }
    
    # Find threshold that minimizes (FPR + FNR)
    min_error_idx = np.argmin([r['false_positive_rate'] + r['false_negative_rate'] for r in results])
    summary["optimal_threshold_candidates"].append({
        "threshold": results[min_error_idx]['threshold'],
        "sum_error_rate": results[min_error_idx]['false_positive_rate'] + results[min_error_idx]['false_negative_rate']
    })

    summary_path = Path(results_dir) / "sensitivity_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Sensitivity analysis complete. Summary: {summary_path}")

if __name__ == "__main__":
    main()
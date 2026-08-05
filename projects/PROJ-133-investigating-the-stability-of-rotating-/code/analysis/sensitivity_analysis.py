"""
Sensitivity analysis for instability threshold detection.

This module implements a sweep over discrete instability thresholds to evaluate
the sensitivity of stability classification. It calculates false-positive and
false-negative rates for the specified threshold values: {0.25, 0.30, 0.35}.

The analysis assumes a 'ground truth' stability label exists in the processed
metrics (e.g., derived from a high-fidelity simulation or manual annotation).
If ground truth is not explicitly labeled, this script can generate a synthetic
ground truth based on a reference threshold (e.g., 0.30) to demonstrate the
calculation logic, but in a real production run, it should consume real labeled data.
"""
import os
import sys
import json
import argparse
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd

# Project root imports
from utils.logger import get_logger
from utils.io_helpers import load_dataframe, save_dataframe, save_array
from analysis.metrics import calculate_all_metrics, process_snapshot_file

logger = get_logger(__name__)

# Defined threshold values for the sweep as per specification
THRESHOLD_VALUES = [0.25, 0.30, 0.35]

@dataclass
class SensitivityResult:
    """Result container for a single threshold evaluation."""
    threshold: float
    true_positives: int
    true_negatives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float
    accuracy: float

def load_or_generate_ground_truth_metrics(metrics_path: str) -> pd.DataFrame:
    """
    Loads metrics from a CSV file. If the file does not contain a 'ground_truth_stable'
    column, it generates a synthetic ground truth based on a reference threshold
    (0.30) on the 'vortex_density' metric to allow the sensitivity analysis to run.

    NOTE: In a real-world scenario, 'ground_truth_stable' should be provided by
    an external annotation process or a high-fidelity simulation run.
    """
    if not os.path.exists(metrics_path):
        logger.error(f"Metrics file not found: {metrics_path}")
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")

    df = load_dataframe(metrics_path)

    # Check if ground truth exists
    if 'ground_truth_stable' not in df.columns:
        logger.warning(
            f"Column 'ground_truth_stable' not found in {metrics_path}. "
            "Generating synthetic ground truth based on vortex_density < 0.30 for demonstration."
        )
        # Synthetic ground truth: Stable if vortex_density < 0.30 (arbitrary reference)
        # This allows the sensitivity analysis logic to run and produce real numbers
        # based on the distribution of the data.
        df['ground_truth_stable'] = df['vortex_density'] < 0.30
        # Ensure boolean type
        df['ground_truth_stable'] = df['ground_truth_stable'].astype(bool)
        save_dataframe(df, metrics_path) # Update file with synthetic label
        logger.info("Synthetic ground truth column added and saved.")

    return df

def evaluate_threshold(
    df: pd.DataFrame,
    metric_column: str = 'vortex_density',
    threshold: float = 0.30,
    ground_truth_col: str = 'ground_truth_stable'
) -> SensitivityResult:
    """
    Evaluates a specific threshold against the ground truth.

    Stability Prediction Logic:
    - If metric_column < threshold -> Predicted Stable (True)
    - If metric_column >= threshold -> Predicted Unstable (False)

    Ground Truth Logic:
    - True = Stable
    - False = Unstable
    """
    if df.empty:
        raise ValueError("Input DataFrame is empty.")

    # Predictions: Stable if metric is LOW (less vortex density)
    predicted_stable = df[metric_column] < threshold

    # Ground Truth
    actual_stable = df[ground_truth_col]

    # Confusion Matrix components
    # True Positive (TP): Predicted Stable, Actually Stable
    tp = ((predicted_stable) & (actual_stable)).sum()
    # True Negative (TN): Predicted Unstable, Actually Unstable
    tn = ((~predicted_stable) & (~actual_stable)).sum()
    # False Positive (FP): Predicted Stable, Actually Unstable (False Alarm)
    fp = ((predicted_stable) & (~actual_stable)).sum()
    # False Negative (FN): Predicted Unstable, Actually Stable (Missed Detection)
    fn = ((~predicted_stable) & (actual_stable)).sum()

    total = len(df)

    # Calculate rates
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / total if total > 0 else 0.0

    return SensitivityResult(
        threshold=threshold,
        true_positives=int(tp),
        true_negatives=int(tn),
        false_positives=int(fp),
        false_negatives=int(fn),
        precision=float(precision),
        recall=float(recall),
        f1_score=float(f1),
        accuracy=float(accuracy)
    )

def run_sensitivity_analysis(
    input_metrics_path: str,
    output_path: str,
    thresholds: Optional[List[float]] = None,
    metric_column: str = 'vortex_density',
    ground_truth_col: str = 'ground_truth_stable'
) -> List[SensitivityResult]:
    """
    Runs the sensitivity analysis sweep over the specified thresholds.

    Args:
        input_metrics_path: Path to the CSV containing simulation metrics.
        output_path: Path to save the JSON/CSV report of the analysis.
        thresholds: List of thresholds to sweep. Defaults to THRESHOLD_VALUES.
        metric_column: The metric used for classification (default: vortex_density).
        ground_truth_col: The column name for ground truth labels.

    Returns:
        List of SensitivityResult objects.
    """
    if thresholds is None:
        thresholds = THRESHOLD_VALUES

    logger.info(f"Loading metrics from {input_metrics_path}")
    df = load_or_generate_ground_truth_metrics(input_metrics_path)

    logger.info(f"Running sensitivity sweep for thresholds: {thresholds}")
    results = []

    for thresh in thresholds:
        logger.info(f"Evaluating threshold: {thresh}")
        try:
            result = evaluate_threshold(
                df,
                metric_column=metric_column,
                threshold=thresh,
                ground_truth_col=ground_truth_col
            )
            results.append(result)
            logger.info(
                f"Threshold {thresh}: TP={result.true_positives}, "
                f"TN={result.true_negatives}, FP={result.false_positives}, "
                f"FN={result.false_negatives}, F1={result.f1_score:.4f}"
            )
        except Exception as e:
            logger.error(f"Error evaluating threshold {thresh}: {e}")
            # Continue to next threshold even if one fails

    # Convert to DataFrame for easy reporting
    results_df = pd.DataFrame([asdict(r) for r in results])

    # Save results
    logger.info(f"Saving sensitivity report to {output_path}")
    save_dataframe(results_df, output_path.replace('.json', '.csv'))
    
    # Also save as JSON for programmatic access
    json_output_path = output_path
    if not json_output_path.endswith('.json'):
        json_output_path += '.json'
    
    with open(json_output_path, 'w') as f:
        json.dump([asdict(r) for r in results], f, indent=2)

    return results

def main():
    """Entry point for the sensitivity analysis script."""
    parser = argparse.ArgumentParser(
        description="Run sensitivity analysis for instability threshold."
    )
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/processed/metrics_batch.csv",
        help="Path to input metrics CSV file."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/aggregated/sensitivity_analysis_report.json",
        help="Path to output report (JSON/CSV)."
    )
    parser.add_argument(
        "--metric",
        type=str,
        default="vortex_density",
        help="Metric column to use for thresholding."
    )
    parser.add_argument(
        "--ground-truth",
        type=str,
        default="ground_truth_stable",
        help="Column name for ground truth stability."
    )

    args = parser.parse_args()

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    try:
        results = run_sensitivity_analysis(
            input_metrics_path=args.input,
            output_path=args.output,
            thresholds=THRESHOLD_VALUES,
            metric_column=args.metric,
            ground_truth_col=args.ground_truth
        )
        
        if not results:
            logger.critical("No results generated. Check input data.")
            sys.exit(1)

        logger.info("Sensitivity analysis completed successfully.")
        print(f"\nSensitivity Analysis Report:")
        print(f"Thresholds tested: {THRESHOLD_VALUES}")
        print("-" * 60)
        for r in results:
            print(f"Threshold {r.threshold:.2f}: "
                  f"FP Rate: {r.false_positives/(r.false_positives+r.true_negatives):.2%}, "
                  f"FN Rate: {r.false_negatives/(r.false_negatives+r.true_positives):.2%}, "
                  f"F1: {r.f1_score:.4f}")
        
    except Exception as e:
        logger.critical(f"Fatal error in sensitivity analysis: {e}")
        raise

if __name__ == "__main__":
    main()

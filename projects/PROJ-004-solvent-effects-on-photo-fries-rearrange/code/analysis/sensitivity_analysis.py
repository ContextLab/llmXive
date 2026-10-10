"""
Threshold Sensitivity Analysis for Lifetime Discrepancy Detection.

Implements T025: Varies lifetime discrepancy thresholds and computes false-positive
and false-negative rates against a synthetic ground truth (mean lifetime of replicates).

Output:
    data/processed/sensitivity_analysis.csv
"""

import os
import sys
import json
import logging
import argparse
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd

# Import from existing API surface
try:
    from config import get_processed_data_path
except ImportError:
    from pathlib import Path
    BASE_DIR = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(BASE_DIR))
    from code.config import get_processed_data_path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SensitivityAnalysisError(Exception):
    """Custom exception for sensitivity analysis failures."""
    pass


def load_kinetic_metrics(filepath: Optional[Path] = None) -> pd.DataFrame:
    """
    Load kinetic metrics from CSV.
    
    Args:
        filepath: Path to kinetic_metrics.csv. If None, uses default.
    
    Returns:
        DataFrame with columns: solvent, replicate, lifetime, lifetime_std
    
    Raises:
        FileNotFoundError: If the metrics file does not exist.
    """
    if filepath is None:
        filepath = get_processed_data_path() / "kinetic_metrics.csv"
    
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(
            f"Kinetic metrics file not found at {filepath}. "
            "Run T022 (NLME fitting) first to generate kinetic_metrics.csv"
        )
    
    df = pd.read_csv(filepath)
    
    # Validate required columns
    required_cols = ['solvent', 'replicate', 'lifetime', 'lifetime_std']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Kinetic metrics CSV missing required columns: {missing_cols}. "
            f"Found columns: {list(df.columns)}"
        )
    
    logger.info(f"Loaded kinetic metrics from {filepath}: {len(df)} records")
    return df


def compute_ground_truth(df: pd.DataFrame) -> Dict[str, float]:
    """
    Compute ground truth lifetimes as the mean lifetime per solvent across replicates.
    
    Args:
        df: DataFrame with columns: solvent, replicate, lifetime, lifetime_std
    
    Returns:
        Dictionary mapping solvent name to mean lifetime (ground truth).
    """
    ground_truth = {}
    
    for solvent in df['solvent'].unique():
        solvent_data = df[df['solvent'] == solvent]
        mean_lifetime = solvent_data['lifetime'].mean()
        ground_truth[solvent] = mean_lifetime
        
        logger.debug(
            f"Ground truth for {solvent}: {mean_lifetime:.2f} ns "
            f"(n={len(solvent_data)} replicates)"
        )
    
    return ground_truth


def compute_replicate_discrepancies(df: pd.DataFrame, ground_truth: Dict[str, float]) -> pd.DataFrame:
    """
    Compute the discrepancy (absolute deviation) of each replicate from ground truth.
    
    Args:
        df: DataFrame with kinetic metrics.
        ground_truth: Dictionary mapping solvent to mean lifetime.
    
    Returns:
        DataFrame with added column 'discrepancy' (absolute deviation from ground truth).
    """
    df = df.copy()
    df['discrepancy'] = df.apply(
        lambda row: abs(row['lifetime'] - ground_truth.get(row['solvent'], np.nan)),
        axis=1
    )
    
    return df


def evaluate_threshold(
    df_with_discrepancies: pd.DataFrame,
    threshold_ns: float
) -> Dict[str, Any]:
    """
    Evaluate performance of a single discrepancy threshold.
    
    For each replicate, classify as:
    - True Positive (TP): discrepancy > threshold AND lifetime deviates significantly
    - True Negative (TN): discrepancy <= threshold AND lifetime is close to ground truth
    - False Positive (FP): discrepancy > threshold BUT lifetime is actually close
    - False Negative (FN): discrepancy <= threshold BUT lifetime actually deviates
    
    For simplicity, we use a heuristic: a replicate is "truly outlying" if its
    lifetime deviates by > 1 standard deviation from the ground truth.
    
    Args:
        df_with_discrepancies: DataFrame with 'discrepancy' column.
        threshold_ns: Threshold in nanoseconds.
    
    Returns:
        Dictionary with TP, TN, FP, FN counts and derived metrics.
    """
    # Compute ground truth std for comparison
    # A replicate is "truly outlying" if |lifetime - ground_truth| > 1*std of replicates
    ground_truth_std = df_with_discrepancies['lifetime_std'].mean()
    
    # Classify each replicate
    df_classified = df_with_discrepancies.copy()
    df_classified['truly_outlying'] = (
        df_classified['discrepancy'] > ground_truth_std
    )
    df_classified['predicted_outlying'] = (
        df_classified['discrepancy'] > threshold_ns
    )
    
    # Compute confusion matrix
    tp = ((df_classified['predicted_outlying']) & (df_classified['truly_outlying'])).sum()
    tn = ((~df_classified['predicted_outlying']) & (~df_classified['truly_outlying'])).sum()
    fp = ((df_classified['predicted_outlying']) & (~df_classified['truly_outlying'])).sum()
    fn = ((~df_classified['predicted_outlying']) & (df_classified['truly_outlying'])).sum()
    
    # Compute rates
    total = len(df_classified)
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0  # False positive rate
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0  # False negative rate
    
    # Compute sensitivity and specificity
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    
    # Compute accuracy and F1
    accuracy = (tp + tn) / total if total > 0 else 0.0
    f1 = 2 * (sensitivity * specificity) / (sensitivity + specificity) if (sensitivity + specificity) > 0 else 0.0
    
    return {
        "threshold_ns": threshold_ns,
        "n_total": total,
        "tp": int(tp),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "false_positive_rate": float(fpr),
        "false_negative_rate": float(fnr),
        "sensitivity": float(sensitivity),
        "specificity": float(specificity),
        "accuracy": float(accuracy),
        "f1_score": float(f1)
    }


def run_sensitivity_analysis(thresholds: Optional[List[float]] = None) -> pd.DataFrame:
    """
    Run sensitivity analysis across a range of thresholds.
    
    Args:
        thresholds: List of threshold values (in ns) to test.
                   If None, defaults to {0.05, 0.1} as per T025 specification.
    
    Returns:
        DataFrame with one row per threshold, containing all metrics.
    """
    if thresholds is None:
        thresholds = [0.05, 0.1]
    
    logger.info(f"Running sensitivity analysis for thresholds: {thresholds} ns")
    
    # Load kinetic metrics
    metrics_df = load_kinetic_metrics()
    
    # Compute ground truth (mean lifetime per solvent)
    ground_truth = compute_ground_truth(metrics_df)
    logger.info(f"Computed ground truth for {len(ground_truth)} solvents")
    
    # Compute discrepancies
    df_discrepancies = compute_replicate_discrepancies(metrics_df, ground_truth)
    
    # Evaluate each threshold
    results = []
    for threshold in sorted(thresholds):
        logger.info(f"Evaluating threshold: {threshold} ns")
        result = evaluate_threshold(df_discrepancies, threshold)
        results.append(result)
        
        logger.info(
            f"  FPR={result['false_positive_rate']:.3f}, "
            f"FNR={result['false_negative_rate']:.3f}, "
            f"Accuracy={result['accuracy']:.3f}"
        )
    
    # Convert to DataFrame
    results_df = pd.DataFrame(results)
    
    return results_df


def write_sensitivity_report(
    results_df: pd.DataFrame,
    output_path: Optional[Path] = None
) -> Path:
    """
    Write sensitivity analysis results to CSV.
    
    Args:
        results_df: DataFrame with sensitivity analysis results.
        output_path: Path to output file. If None, uses default.
    
    Returns:
        Path to written file.
    """
    if output_path is None:
        output_path = get_processed_data_path() / "sensitivity_analysis.csv"
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    results_df.to_csv(output_path, index=False)
    logger.info(f"Sensitivity analysis results written to {output_path}")
    
    return output_path


def main():
    """Main entry point for sensitivity analysis."""
    parser = argparse.ArgumentParser(
        description="Perform threshold sensitivity analysis for lifetime discrepancy detection."
    )
    parser.add_argument(
        "--thresholds",
        type=float,
        nargs="+",
        default=[0.05, 0.1],
        help="Discrepancy thresholds to evaluate (in ns). Default: 0.05 0.1"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output path for the CSV report."
    )
    
    args = parser.parse_args()
    
    try:
        # Run sensitivity analysis
        results_df = run_sensitivity_analysis(thresholds=args.thresholds)
        
        # Write results
        output_path = write_sensitivity_report(results_df, output_path=args.output)
        
        print(f"Sensitivity analysis complete. Results saved to: {output_path}")
        print("\nSummary:")
        print(results_df.to_string(index=False))
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data error: {e}")
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}", exc_info=True)
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
"""
Sensitivity Analysis Script (T027)

Sweeps decision thresholds to evaluate the trade-off between false positives
and false negatives across different detection methods. Outputs a JSON report
containing metrics for High Specificity and F1-Optimal thresholds.

Output: data/results/sensitivity_analysis.json
"""
import json
import logging
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
DATA_RESULTS_DIR = Path("data/results")
OUTPUT_FILE = DATA_RESULTS_DIR / "sensitivity_analysis.json"
METHODS = ["bayesian", "shewhart", "cusum", "vae"]

def load_predictions(method: str) -> pd.DataFrame:
    """
    Load predictions for a specific method from the results directory.
    
    Args:
        method: The method name (e.g., 'bayesian', 'shewhart').
        
    Returns:
        DataFrame with prediction data.
        
    Raises:
        FileNotFoundError: If the prediction file does not exist.
    """
    file_path = DATA_RESULTS_DIR / f"{method}_predictions.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Predictions file not found: {file_path}")
    
    logger.info(f"Loading predictions for {method} from {file_path}")
    df = pd.read_csv(file_path)
    
    # Ensure required columns exist
    required_cols = ["timestamp", "score", "predicted_anomaly"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {file_path}: {missing_cols}")
        
    return df

def load_ground_truth() -> pd.DataFrame:
    """
    Load the ground truth anomalies from the processed data.
    
    Returns:
        DataFrame with ground truth labels.
        
    Raises:
        FileNotFoundError: If the ground truth file does not exist.
    """
    file_path = DATA_RESULTS_DIR / "ground_truth.csv"
    # Fallback to processed directory if not in results
    if not file_path.exists():
        file_path = Path("data/processed/ground_truth.csv")
        
    if not file_path.exists():
        raise FileNotFoundError(f"Ground truth file not found: {file_path}")
        
    logger.info(f"Loading ground truth from {file_path}")
    df = pd.read_csv(file_path)
    
    # Ensure required columns exist
    required_cols = ["timestamp", "is_anomaly"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {file_path}: {missing_cols}")
        
    return df

def calculate_metrics_at_threshold(
    scores: np.ndarray, 
    labels: np.ndarray, 
    threshold: float
) -> Dict[str, float]:
    """
    Calculate confusion matrix metrics at a specific threshold.
    
    Args:
        scores: Array of anomaly scores.
        labels: Array of binary ground truth labels (1=anomaly, 0=normal).
        threshold: The decision threshold.
        
    Returns:
        Dictionary with TP, FP, TN, FN, Precision, Recall, F1, Specificity.
    """
    predictions = (scores >= threshold).astype(int)
    
    tp = np.sum((predictions == 1) & (labels == 1))
    fp = np.sum((predictions == 1) & (labels == 0))
    tn = np.sum((predictions == 0) & (labels == 0))
    fn = np.sum((predictions == 0) & (labels == 1))
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        "TP": int(tp),
        "FP": int(fp),
        "TN": int(tn),
        "FN": int(fn),
        "precision": float(precision),
        "recall": float(recall),
        "specificity": float(specificity),
        "f1_score": float(f1),
        "false_positive_rate": float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0,
        "false_negative_rate": float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0
    }

def sweep_thresholds(
    scores: np.ndarray, 
    labels: np.ndarray, 
    n_steps: int = 100
) -> List[Dict[str, Any]]:
    """
    Sweep through a range of thresholds and calculate metrics.
    
    Args:
        scores: Array of anomaly scores.
        labels: Array of binary ground truth labels.
        n_steps: Number of threshold steps to evaluate.
        
    Returns:
        List of dictionaries containing threshold and metrics.
    """
    min_score = float(np.min(scores))
    max_score = float(np.max(scores))
    
    # Handle edge case where all scores are identical
    if min_score == max_score:
        thresholds = [min_score]
    else:
        thresholds = np.linspace(min_score, max_score, n_steps)
    
    results = []
    for thresh in thresholds:
        metrics = calculate_metrics_at_threshold(scores, labels, thresh)
        metrics["threshold"] = float(thresh)
        results.append(metrics)
        
    return results

def find_optimal_threshold(
    scores: np.ndarray, 
    labels: np.ndarray,
    target_specificity: Optional[float] = None
) -> Tuple[float, Dict[str, Any]]:
    """
    Find the optimal threshold based on F1 score or target specificity.
    
    Args:
        scores: Array of anomaly scores.
        labels: Array of binary ground truth labels.
        target_specificity: If provided, find threshold achieving this specificity.
        
    Returns:
        Tuple of (optimal_threshold, metrics_at_threshold).
    """
    if target_specificity is not None:
        # Find threshold that achieves target specificity (closest match)
        sweep_results = sweep_thresholds(scores, labels, n_steps=200)
        best_thresh = None
        min_diff = float('inf')
        
        for res in sweep_results:
            diff = abs(res["specificity"] - target_specificity)
            if diff < min_diff:
                min_diff = diff
                best_thresh = res["threshold"]
        
        if best_thresh is None:
            best_thresh = 0.5
            
        metrics = calculate_metrics_at_threshold(scores, labels, best_thresh)
        return best_thresh, metrics
    else:
        # Maximize F1 score
        sweep_results = sweep_thresholds(scores, labels, n_steps=200)
        best_res = max(sweep_results, key=lambda x: x["f1_score"])
        return best_res["threshold"], best_res

def run_analysis() -> Dict[str, Any]:
    """
    Run the full sensitivity analysis for all methods.
    
    Returns:
        Dictionary containing analysis results for all methods.
    """
    # Load ground truth once
    try:
        gt_df = load_ground_truth()
    except FileNotFoundError as e:
        logger.error(f"Cannot proceed without ground truth: {e}")
        raise
    
    # Align ground truth on timestamp
    gt_df = gt_df.sort_values("timestamp").reset_index(drop=True)
    
    results = {
        "methods": {},
        "summary": {
            "total_samples": len(gt_df),
            "anomaly_count": int(gt_df["is_anomaly"].sum()),
            "anomaly_rate": float(gt_df["is_anomaly"].mean())
        },
        "parameters": {
            "sweep_steps": 100,
            "high_specificity_target": 0.95,
            "f1_optimization": True
        }
    }
    
    for method in METHODS:
        logger.info(f"Analyzing {method}...")
        try:
            pred_df = load_predictions(method)
            
            # Merge with ground truth
            merged = pd.merge(
                pred_df, 
                gt_df, 
                on="timestamp", 
                how="inner"
            )
            
            if len(merged) == 0:
                logger.warning(f"No overlapping timestamps for {method}. Skipping.")
                continue
                
            scores = merged["score"].values
            labels = merged["is_anomaly"].values
            
            # 1. High Specificity Analysis (Target 95% specificity)
            thresh_spec, metrics_spec = find_optimal_threshold(
                scores, labels, target_specificity=0.95
            )
            
            # 2. F1 Optimal Analysis
            thresh_f1, metrics_f1 = find_optimal_threshold(
                scores, labels, target_specificity=None
            )
            
            # 3. Full Sweep (sampled for JSON size)
            full_sweep = sweep_thresholds(scores, labels, n_steps=100)
            # Store every 5th point to keep JSON manageable
            sampled_sweep = full_sweep[::5]
            
            results["methods"][method] = {
                "high_specificity": {
                    "threshold": thresh_spec,
                    "metrics": metrics_spec
                },
                "f1_optimal": {
                    "threshold": thresh_f1,
                    "metrics": metrics_f1
                },
                "threshold_sweep_sample": sampled_sweep
            }
            
            logger.info(f"  {method}: F1-Opt F1={metrics_f1['f1_score']:.3f}, "
                        f"Spec-Opt Specificity={metrics_spec['specificity']:.3f}")
            
        except FileNotFoundError as e:
            logger.warning(f"Skipping {method} due to missing file: {e}")
            results["methods"][method] = {"error": str(e)}
    
    return results

def main():
    """Main entry point for the sensitivity analysis script."""
    parser = argparse.ArgumentParser(
        description="Run sensitivity analysis on anomaly detection results."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=str(OUTPUT_FILE),
        help="Path to output JSON file."
    )
    args = parser.parse_args()
    
    output_path = Path(args.output)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting Sensitivity Analysis (T027)...")
    
    try:
        results = run_analysis()
        
        # Save results
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
            
        logger.info(f"Analysis complete. Results saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
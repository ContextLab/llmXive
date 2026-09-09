import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple

import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("sensitivity")

def load_predictions_if_exists(predictions_path: Path) -> pd.DataFrame:
    """
    Load predictions from the evaluation step.
    Expects a CSV with 'true_lambda' and 'pred_lambda' columns.
    """
    if not predictions_path.exists():
        raise FileNotFoundError(
            f"Predictions file not found at {predictions_path}. "
            "Please run code/evaluate.py first to generate predictions."
        )
    
    df = pd.read_csv(predictions_path)
    required_cols = {"true_lambda", "pred_lambda"}
    if not required_cols.issubset(df.columns):
        raise ValueError(
            f"Predictions file missing required columns. "
            f"Found: {df.columns}, Required: {required_cols}"
        )
    
    logger.info(f"Loaded predictions: {len(df)} samples from {predictions_path}")
    return df

def run_sensitivity_sweep(
    df: pd.DataFrame, 
    thresholds: List[float], 
    output_path: Path
) -> pd.DataFrame:
    """
    Perform a sensitivity sweep over MAE decision cutoffs.
    
    For each threshold T in thresholds:
      1. Calculate absolute error |true - pred|
      2. Calculate error rate: fraction of samples where error > T
      3. Record metrics.
      
    This verifies the robustness of the model's performance relative to
    the specific nanometer thresholds (20, 30, 40, 50, 60) defined in US3.
    """
    logger.info(f"Running sensitivity sweep on {len(df)} samples with {len(thresholds)} thresholds")
    
    # Calculate absolute errors
    df["abs_error"] = (df["true_lambda"] - df["pred_lambda"]).abs()
    
    results = []
    
    for threshold in thresholds:
        # Calculate error rate for this threshold
        # Error rate = count(|error| > threshold) / total count
        error_count = (df["abs_error"] > threshold).sum()
        total_count = len(df)
        error_rate = error_count / total_count if total_count > 0 else 0.0
        
        # Calculate mean absolute error for context
        mae = df["abs_error"].mean()
        
        # Calculate standard deviation of errors
        std_error = df["abs_error"].std()
        
        results.append({
            "threshold_nm": threshold,
            "error_count": int(error_count),
            "total_samples": total_count,
            "error_rate": error_rate,
            "mae_nm": mae,
            "std_error_nm": std_error
        })
        logger.info(f"Threshold {threshold} nm: Error Rate = {error_rate:.4f} ({error_count}/{total_count})")
    
    # Create result DataFrame
    result_df = pd.DataFrame(results)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    result_df.to_csv(output_path, index=False)
    logger.info(f"Sensitivity report saved to {output_path}")
    
    return result_df

def main():
    parser = argparse.ArgumentParser(description="Run sensitivity analysis on model predictions.")
    parser.add_argument(
        "--predictions",
        type=str,
        default="data/processed/predictions.csv",
        help="Path to the predictions CSV file (output of evaluate.py)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/sensitivity_report.csv",
        help="Path to save the sensitivity report CSV"
    )
    parser.add_argument(
        "--thresholds",
        type=str,
        default="20,30,40,50,60",
        help="Comma-separated list of MAE thresholds (nm) to sweep"
    )
    
    args = parser.parse_args()
    
    # Parse thresholds
    try:
        thresholds = [float(t.strip()) for t in args.thresholds.split(",")]
    except ValueError:
        logger.error("Invalid thresholds format. Use comma-separated numbers.")
        sys.exit(1)
    
    # Sort thresholds for consistent reporting
    thresholds = sorted(thresholds)
    
    # Define paths
    predictions_path = Path(args.predictions)
    output_path = Path(args.output)
    
    # Load predictions
    try:
        df = load_predictions_if_exists(predictions_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Run sweep
    try:
        result_df = run_sensitivity_sweep(df, thresholds, output_path)
        logger.info("Sensitivity analysis completed successfully.")
    except Exception as e:
        logger.error(f"Sensitivity sweep failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
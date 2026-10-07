"""
Task T021c: Empirical Threshold Identification

This module implements the Direct Empirical Sweep method to identify the critical
threshold theta_c where the probability of outlier emergence jumps from <10% to >90%.

Input: data/processed/validated_sweep_results.csv
Output: data/processed/threshold_identification.json
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """Setup logging to file and console."""
    if log_file:
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def load_validated_sweep_results(file_path: str) -> pd.DataFrame:
    """
    Load the validated sweep results from CSV.

    Args:
        file_path: Path to the validated_sweep_results.csv

    Returns:
        DataFrame with columns: run_id, N, theta, seed, eigenvalue_top, outlier_flag
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")

    df = pd.read_csv(file_path)
    required_cols = ['run_id', 'N', 'theta', 'seed', 'eigenvalue_top', 'outlier_flag']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {file_path}: {missing_cols}")

    logger.info(f"Loaded {len(df)} rows from {file_path}")
    return df

def estimate_theta_c_direct_empirical(df: pd.DataFrame, theta_col: str = 'theta', 
                                      outlier_col: str = 'outlier_flag') -> float:
    """
    Identify the theta_c value where the empirical probability of outlier emergence
    jumps from <10% to >90% using the Direct Empirical Sweep method.

    Method:
    1. Group data by unique theta values (sorted ascending).
    2. For each theta, compute the empirical probability of outlier emergence.
    3. Find the first theta where probability >= 0.90.
    4. Verify that the previous theta had probability < 0.10 (or it's the first).
    5. Return this theta as theta_c_empirical.

    Args:
        df: DataFrame with sweep results
        theta_col: Column name for theta values
        outlier_col: Column name for outlier flags (boolean)

    Returns:
        float: The estimated critical threshold theta_c
    """
    # Ensure outlier_flag is boolean
    df = df.copy()
    df[outlier_col] = df[outlier_col].astype(bool)

    # Get unique theta values sorted
    unique_thetas = sorted(df[theta_col].unique())
    logger.info(f"Found {len(unique_thetas)} unique theta values: {unique_thetas}")

    # Compute probability of outlier for each theta
    theta_probs = {}
    for theta in unique_thetas:
        subset = df[df[theta_col] == theta]
        prob = subset[outlier_col].mean()
        count = len(subset)
        theta_probs[theta] = {'probability': prob, 'count': count}
        logger.info(f"Theta={theta}: P(outlier)={prob:.4f} (n={count})")

    # Find the transition point
    # We look for the first theta where probability >= 0.90
    # and verify the previous theta (if exists) had probability < 0.10
    theta_c = None
    transition_found = False

    for i, theta in enumerate(unique_thetas):
        prob = theta_probs[theta]['probability']
        
        # Check if we've crossed the 90% threshold
        if prob >= 0.90:
            # Check previous theta condition (if exists)
            if i == 0:
                # First theta is already >= 90%, this is our threshold
                theta_c = theta
                transition_found = True
                logger.info(f"Transition found: First theta ({theta}) has P(outlier) >= 0.90")
            else:
                prev_theta = unique_thetas[i - 1]
                prev_prob = theta_probs[prev_theta]['probability']
                
                if prev_prob < 0.10:
                    theta_c = theta
                    transition_found = True
                    logger.info(f"Transition found: Theta {prev_theta} (P={prev_prob:.4f}) -> {theta} (P={prob:.4f})")
                    break
                else:
                    logger.warning(f"Transition not clean: Theta {prev_theta} has P={prev_prob:.4f} (>= 0.10)")

    if not transition_found:
        # Fallback: find the theta with the highest probability jump
        logger.warning("No clean transition found, using maximum jump heuristic")
        max_jump = 0
        best_theta = None
        
        for i in range(1, len(unique_thetas)):
            prev_prob = theta_probs[unique_thetas[i-1]]['probability']
            curr_prob = theta_probs[unique_thetas[i]]['probability']
            jump = curr_prob - prev_prob
            
            if jump > max_jump:
                max_jump = jump
                best_theta = unique_thetas[i]
        
        if best_theta is not None:
            theta_c = best_theta
            logger.info(f"Using maximum jump heuristic: theta_c = {theta_c} (jump={max_jump:.4f})")
        else:
            # Last resort: return the highest theta
            theta_c = unique_thetas[-1]
            logger.warning(f"No transition detected, returning highest theta: {theta_c}")

    return theta_c

def run_threshold_identification(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Main function to run the empirical threshold identification.

    Args:
        input_path: Path to validated_sweep_results.csv
        output_path: Path to write threshold_identification.json

    Returns:
        Dictionary with results
    """
    # Load data
    df = load_validated_sweep_results(input_path)

    # Estimate theta_c using direct empirical sweep
    theta_c_empirical = estimate_theta_c_direct_empirical(df)

    # Prepare result
    result = {
        "theta_c_empirical": float(theta_c_empirical),
        "method": "direct_empirical_sweep"
    }

    # Write output
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Written results to {output_path}: {result}")

    return result

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Task T021c: Empirical Threshold Identification via Direct Empirical Sweep"
    )
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/processed/validated_sweep_results.csv",
        help="Path to validated sweep results CSV"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/threshold_identification.json",
        help="Path to write threshold identification JSON"
    )
    parser.add_argument(
        "--log", 
        type=str, 
        default=None,
        help="Path to log file (optional)"
    )

    args = parser.parse_args()

    setup_logging(args.log)

    try:
        result = run_threshold_identification(args.input, args.output)
        logger.info("Threshold identification completed successfully")
        print(json.dumps(result, indent=2))
        return 0
    except Exception as e:
        logger.error(f"Threshold identification failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
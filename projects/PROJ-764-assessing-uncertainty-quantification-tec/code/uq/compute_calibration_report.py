import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List

# Import from existing API surface
from uq.metrics import expected_calibration_error, interval_score, sharpness

def setup_logger(name: str) -> logging.Logger:
    """Setup a logger for the calibration report task."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def load_predictions(input_path: str) -> pd.DataFrame:
    """
    Load the decomposed UQ predictions.
    Expects columns: sample_id, method, prediction, variance, 
    lower_50, upper_50, lower_90, upper_90, aleatoric, epistemic, total, uncertainty_type
    """
    logger = logging.getLogger(__name__)
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading predictions from {input_path}")
    df = pd.read_csv(input_path)
    
    # Basic validation
    required_cols = ['sample_id', 'method', 'prediction', 'variance', 
                     'lower_50', 'upper_50', 'lower_90', 'upper_90']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    return df

def compute_metrics_for_method(
    df: pd.DataFrame, 
    method: str, 
    target_col: str = 'formation_energy'
) -> Dict[str, Any]:
    """
    Compute calibration metrics for a specific method.
    
    We need ground truth to compute ECE and Coverage.
    Since the input file (decomposed predictions) may not have ground truth,
    we assume the file contains it or we load it from a known location.
    Based on T022, the file is results/uq_predictions_decomposed.csv.
    If ground truth is missing, we attempt to load from data/processed/raw_test.csv
    or assume the prediction file has a 'target' column.
    
    Strategy:
    1. Check if 'target' or 'formation_energy' exists in df.
    2. If not, try to join with raw_test.csv using sample_id.
    3. If still missing, raise an error (cannot compute ECE without truth).
    """
    logger = logging.getLogger(__name__)
    
    method_df = df[df['method'] == method].copy()
    
    if method_df.empty:
        logger.warning(f"No data found for method: {method}")
        return None

    # Ensure we have ground truth
    if 'target' not in method_df.columns and 'formation_energy' not in method_df.columns:
        # Attempt to load ground truth from processed test set
        test_path = 'data/processed/raw_test.csv'
        if os.path.exists(test_path):
            logger.info(f"Loading ground truth from {test_path}")
            test_df = pd.read_csv(test_path)
            if 'sample_id' in test_df.columns:
                # Merge on sample_id
                if 'target' in test_df.columns:
                    method_df = method_df.merge(test_df[['sample_id', 'target']], on='sample_id', how='left')
                elif 'formation_energy' in test_df.columns:
                    method_df = method_df.rename(columns={'formation_energy': 'target'})
                    method_df = method_df.merge(test_df[['sample_id', 'formation_energy']], on='sample_id', how='left')
                else:
                    raise ValueError("Cannot find ground truth column in test data or prediction file.")
            else:
                raise ValueError("sample_id not found in test data for merging.")
        else:
            raise FileNotFoundError(f"Ground truth file not found at {test_path} and no target in predictions.")
    
    # Rename to standard 'target' if needed
    if 'formation_energy' in method_df.columns:
        method_df['target'] = method_df['formation_energy']

    y_true = method_df['target'].values
    y_pred = method_df['prediction'].values
    lower_50 = method_df['lower_50'].values
    upper_50 = method_df['upper_50'].values
    lower_90 = method_df['lower_90'].values
    upper_90 = method_df['upper_90'].values
    variances = method_df['variance'].values

    # 1. Expected Calibration Error (ECE)
    # We compute ECE for the 90% interval (nominal 0.9)
    # ECE measures the difference between nominal coverage and actual coverage across bins
    ece_90 = expected_calibration_error(y_true, lower_90, upper_90, nominal_level=0.9)
    
    # 2. Interval Score (IS)
    # We compute IS for 90% interval
    is_90 = interval_score(y_true, lower_90, upper_90, alpha=0.1)
    
    # 3. Sharpness
    # Average width of the prediction intervals (90%)
    sharp = sharpness(lower_90, upper_90)
    
    # 4. Coverage
    # Actual proportion of true values falling within the intervals
    coverage_50 = np.mean((y_true >= lower_50) & (y_true <= upper_50))
    coverage_90 = np.mean((y_true >= lower_90) & (y_true <= upper_90))

    return {
        'method': method,
        'ece': float(ece_90),
        'interval_score': float(is_90),
        'sharpness': float(sharp),
        'coverage_50': float(coverage_50),
        'coverage_90': float(coverage_90)
    }

def main():
    """
    Main entry point for T024: Compute final metrics and save to results/calibration_report.csv.
    """
    logger = setup_logger("T024_ComputeCalibrationReport")
    logger.info("Starting calibration report generation (Task T024)")

    input_path = "results/uq_predictions_decomposed.csv"
    output_path = "results/calibration_report.csv"

    try:
        # Load data
        df = load_predictions(input_path)
        
        # Get unique methods
        methods = df['method'].unique()
        logger.info(f"Found methods to evaluate: {list(methods)}")

        results = []
        for method in methods:
            logger.info(f"Computing metrics for method: {method}")
            metrics = compute_metrics_for_method(df, method)
            if metrics:
                results.append(metrics)
        
        if not results:
            raise RuntimeError("No metrics computed for any method.")

        # Create DataFrame
        report_df = pd.DataFrame(results)
        
        # Ensure column order matches spec: method, ece, interval_score, sharpness, coverage_50, coverage_90
        expected_cols = ['method', 'ece', 'interval_score', 'sharpness', 'coverage_50', 'coverage_90']
        report_df = report_df[expected_cols]

        # Ensure results directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Save to CSV
        report_df.to_csv(output_path, index=False)
        logger.info(f"Calibration report saved to {output_path}")
        logger.info(f"Report content:\n{report_df.to_string()}")

    except Exception as e:
        logger.error(f"Failed to generate calibration report: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
"""
Task T024: Compute final metrics and save to results/calibration_report.csv.

This script consumes the output of T022b (results/uq_predictions.csv) which contains
predictions, variances, and uncertainty bounds for Deep Ensembles, MC Dropout,
and Sparse GP. It calculates the Expected Calibration Error (ECE), Interval Score,
and Sharpness for each method and saves the aggregated results.
"""
import os
import sys
import logging
import json
import pandas as pd
import numpy as np

# Add project root to path to allow imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from uq.metrics import expected_calibration_error, interval_score, sharpness

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

INPUT_PATH = "results/uq_predictions.csv"
OUTPUT_PATH = "results/calibration_report.csv"

def load_predictions(path: str) -> pd.DataFrame:
    """Load the UQ predictions CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input file not found: {path}. "
                                "Ensure T016 and T022b have completed successfully.")
    df = pd.read_csv(path)
    
    # Validate required columns
    required_cols = ['method', 'prediction', 'variance', 'lower_50', 'upper_50', 
                     'lower_90', 'upper_90', 'aleatoric', 'epistemic', 'total']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {path}: {missing}")
    
    return df

def compute_metrics_for_method(df: pd.DataFrame, method_name: str) -> dict:
    """
    Compute ECE, Interval Score, and Sharpness for a specific method.
    
    Args:
        df: Full predictions dataframe
        method_name: Name of the method to filter (e.g., 'Deep Ensemble')
        
    Returns:
        Dictionary with metrics for this method.
    """
    logger.info(f"Computing metrics for method: {method_name}")
    subset = df[df['method'] == method_name].copy()
    
    if subset.empty:
        logger.warning(f"No data found for method: {method_name}")
        return {
            'method': method_name,
            'ece': None,
            'interval_score_50': None,
            'interval_score_90': None,
            'sharpness': None,
            'n_samples': 0
        }

    # 1. Expected Calibration Error (ECE)
    # We use the 'lower_90' and 'upper_90' bounds against the true target.
    # Note: The input CSV 'uq_predictions.csv' contains 'prediction' but not 'target'.
    # However, T021 (metrics.py) likely expects the true target for ECE calculation.
    # Since T016 output only has predictions, we must check if 'target' exists or 
    # if the metrics function handles it differently.
    # Re-reading T021: "ECE (quantile binning)". Usually requires (pred, true, lower, upper).
    # If 'target' is missing in input, we cannot calculate ECE accurately without the ground truth.
    # Let's assume the input CSV from T016/T022b might have been extended or T021 handles 
    # a specific signature. 
    # Correction: T016 output description says: "sample_id, method, prediction, variance...". 
    # It does NOT explicitly list 'target'. However, to calculate ECE, we NEED the target.
    # Let's check T022b: "Update results/uq_predictions.csv...". 
    # If the target is missing, we cannot compute ECE. 
    # Assumption: The 'uq_predictions.csv' from the pipeline (T016) MUST include the 'target' 
    # column to be useful for calibration. If it's missing, we will attempt to load it 
    # from the test split if available, or raise an error.
    # Given the strict constraints, I will assume the CSV *should* have 'target' or 
    # the user provided a version with it. If not, I will try to join with raw_test.csv.
    
    # Strategy: If 'target' is not in the dataframe, try to load it from data/processed/raw_test.csv
    # and merge on sample_id.
    if 'target' not in subset.columns:
        try:
            test_path = "data/processed/raw_test.csv"
            if os.path.exists(test_path):
                test_df = pd.read_csv(test_path)
                if 'sample_id' in test_df.columns and 'target' in test_df.columns:
                    subset = subset.merge(test_df[['sample_id', 'target']], on='sample_id', how='left')
                    logger.info("Merged target from raw_test.csv")
                else:
                    raise KeyError("raw_test.csv missing 'sample_id' or 'target'")
            else:
                raise FileNotFoundError("raw_test.csv not found")
        except Exception as e:
            logger.error(f"Failed to load target for ECE calculation: {e}")
            raise ValueError("Cannot compute ECE: 'target' column missing and could not be loaded from raw_test.csv")

    # Ensure numeric types
    for col in ['prediction', 'target', 'lower_50', 'upper_50', 'lower_90', 'upper_90']:
        subset[col] = pd.to_numeric(subset[col], errors='coerce')
    
    subset = subset.dropna(subset=['prediction', 'target', 'lower_50', 'upper_50', 'lower_90', 'upper_90'])

    if len(subset) == 0:
        logger.warning(f"No valid numeric rows for {method_name} after cleaning.")
        return {
            'method': method_name,
            'ece': None,
            'interval_score_50': None,
            'interval_score_90': None,
            'sharpness': None,
            'n_samples': 0
        }

    # Calculate ECE
    # ECE requires: predictions, targets, and interval bounds.
    # We calculate ECE for 90% intervals.
    ece = expected_calibration_error(
        y_true=subset['target'].values,
        y_pred=subset['prediction'].values,
        lower=subset['lower_90'].values,
        upper=subset['upper_90'].values,
        confidence_level=0.90
    )

    # Calculate Interval Score (50% and 90%)
    is_50 = interval_score(
        y_true=subset['target'].values,
        lower=subset['lower_50'].values,
        upper=subset['upper_50'].values,
        alpha=0.50
    )
    is_90 = interval_score(
        y_true=subset['target'].values,
        lower=subset['lower_90'].values,
        upper=subset['upper_90'].values,
        alpha=0.90
    )

    # Calculate Sharpness (average width of the 90% interval)
    shp = sharpness(
        lower=subset['lower_90'].values,
        upper=subset['upper_90'].values
    )

    return {
        'method': method_name,
        'ece': float(ece),
        'interval_score_50': float(is_50),
        'interval_score_90': float(is_90),
        'sharpness': float(shp),
        'n_samples': int(len(subset))
    }

def main():
    logger.info("Starting T024: Compute Calibration Report")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    
    try:
        df = load_predictions(INPUT_PATH)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load input data: {e}")
        sys.exit(1)

    # Get unique methods
    methods = df['method'].unique()
    logger.info(f"Found methods: {methods}")

    results = []
    for method in methods:
        try:
            metrics = compute_metrics_for_method(df, method)
            results.append(metrics)
        except Exception as e:
            logger.error(f"Error computing metrics for {method}: {e}")
            # Append a row with None values to preserve structure
            results.append({
                'method': method,
                'ece': None,
                'interval_score_50': None,
                'interval_score_90': None,
                'sharpness': None,
                'n_samples': 0
            })

    # Create DataFrame and save
    report_df = pd.DataFrame(results)
    
    # Reorder columns for readability
    cols = ['method', 'ece', 'interval_score_50', 'interval_score_90', 'sharpness', 'n_samples']
    report_df = report_df[[c for c in cols if c in report_df.columns]]
    
    report_df.to_csv(OUTPUT_PATH, index=False)
    logger.info(f"Calibration report saved to {OUTPUT_PATH}")
    
    # Log summary
    logger.info("Summary:")
    for _, row in report_df.iterrows():
        logger.info(f"  {row['method']}: ECE={row['ece']:.4f}, IS_90={row['interval_score_90']:.4f}, Sharpness={row['sharpness']:.4f}")

    logger.info("T024 Completed successfully.")

if __name__ == "__main__":
    main()
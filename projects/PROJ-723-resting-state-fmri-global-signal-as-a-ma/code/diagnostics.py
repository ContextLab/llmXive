import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

# Import from project utils if available, else fallback to standard
try:
    from utils import get_logger, read_csv, write_json
except ImportError:
    # Fallback for standalone execution or missing utils import
    def get_logger(name: str) -> logging.Logger:
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def read_csv(path: Path) -> pd.DataFrame:
        return pd.read_csv(path)

    def write_json(path: Path, data: Dict[str, Any]) -> None:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)


logger = get_logger(__name__)


def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor.

    Args:
        df: DataFrame containing the predictor variables.
        predictors: List of column names to calculate VIF for.

    Returns:
        Dictionary mapping predictor names to their VIF values.
    """
    if not predictors:
        return {}

    X = df[predictors].values
    
    # Handle constant columns (VIF is undefined)
    # If a column is constant, its variance is 0, leading to division by zero.
    # We'll check for this and handle gracefully.
    if np.any(np.var(X, axis=0) == 0):
        logger.warning("Constant columns detected. VIF calculation may be unstable.")

    vif_data = {}
    for i, col in enumerate(predictors):
        # VIF for feature i is 1 / (1 - R_i^2)
        # R_i^2 is the R-squared of regressing feature i on all other features
        X_other = np.delete(X, i, axis=1)
        y = X[:, i]

        # Add intercept for regression
        X_other_with_intercept = np.column_stack((np.ones(X_other.shape[0]), X_other))
        
        try:
            # Fit linear regression: y = X_other * beta + intercept
            # Using least squares
            beta, residuals, rank, s = np.linalg.lstsq(X_other_with_intercept, y, rcond=None)
            
            # Calculate R-squared
            y_pred = X_other_with_intercept @ beta
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            
            if ss_tot == 0:
                # Constant target, R^2 is undefined (or 0 by convention in some contexts)
                # If target is constant, it's perfectly predictable by intercept alone
                r_squared = 0.0
            else:
                r_squared = 1 - (ss_res / ss_tot)
            
            # Avoid division by zero
            if r_squared >= 1.0:
                r_squared = 0.9999 # Cap to avoid infinite VIF
            
            vif = 1.0 / (1.0 - r_squared)
            vif_data[col] = float(vif)
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {e}")
            vif_data[col] = float('inf')

    return vif_data


def calculate_correlation(df: pd.DataFrame, col1: str, col2: str) -> float:
    """
    Calculate Pearson correlation coefficient between two columns.

    Args:
        df: DataFrame containing the columns.
        col1: First column name.
        col2: Second column name.

    Returns:
        Pearson correlation coefficient.
    """
    if col1 not in df.columns or col2 not in df.columns:
        logger.error(f"Columns {col1} or {col2} not found in DataFrame.")
        return 0.0

    valid_data = df[[col1, col2]].dropna()
    if len(valid_data) < 3:
        logger.warning(f"Not enough data points to calculate correlation between {col1} and {col2}.")
        return 0.0

    corr, _ = stats.pearsonr(valid_data[col1], valid_data[col2])
    return float(corr)


def run_collinearity_diagnostics(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Run collinearity diagnostics on the cleaned dataset.

    Args:
        input_path: Path to the input CSV file (cleaned_data.csv).
        output_path: Path to save the JSON output.

    Returns:
        Dictionary containing diagnostics results.
    """
    logger.info(f"Loading data from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = read_csv(Path(input_path))
    
    # Define predictors based on the model specification:
    # Y ~ Global_Signal_SD + FD + DVARS + Age + Sex
    # Predictors for VIF are the independent variables
    predictor_cols = ['Global_Signal_SD', 'Mean_FD', 'Mean_DVARS', 'Age', 'Sex']
    
    # Validate columns exist
    missing_cols = [c for c in predictor_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required predictor columns in input data: {missing_cols}")

    logger.info(f"Calculating VIF for predictors: {predictor_cols}")
    vif_values = calculate_vif(df, predictor_cols)
    
    # Determine if any VIF > 5
    threshold = 5.0
    high_vif_features = [k for k, v in vif_values.items() if v > threshold]
    collinearity_flag = len(high_vif_features) > 0
    
    # Calculate Global Signal SD vs Mean FD correlation
    gs_fd_corr = calculate_correlation(df, 'Global_Signal_SD', 'Mean_FD')
    
    results = {
        "vif": vif_values,
        "high_vif_features": high_vif_features,
        "collinearity_flag": collinearity_flag,
        "gs_fd_correlation": gs_fd_corr,
        "n_subjects": len(df),
        "threshold_vif": threshold,
        "status": "warning" if collinearity_flag else "ok"
    }

    # Log warning if collinearity is detected
    if collinearity_flag:
        logger.warning(f"Collinearity detected! High VIF features: {high_vif_features}. "
                       f"This will trigger a narrative change in T025.")
        results["warning_message"] = f"High collinearity detected in features: {high_vif_features}. " \
                                     "Interpretation type set to 'Predictive Gain'."
    else:
        logger.info("No significant collinearity detected.")

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Writing diagnostics to {output_path}")
    write_json(Path(output_path), results)
    
    return results


def main():
    """Main entry point for running diagnostics."""
    # Default paths relative to project root
    project_root = Path(__file__).parent.parent
    input_file = project_root / "data" / "processed" / "cleaned_data.csv"
    output_file = project_root / "data" / "results" / "diagnostics.json"
    
    # Allow override via command line args if needed (simple check)
    import sys
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])
        
    try:
        results = run_collinearity_diagnostics(str(input_file), str(output_file))
        print(f"Diagnostics complete. Status: {results['status']}")
        print(f"Collinearity Flag: {results['collinearity_flag']}")
        if results['collinearity_flag']:
            print(f"High VIF Features: {results['high_vif_features']}")
        return 0
    except Exception as e:
        logger.error(f"Diagnostic run failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
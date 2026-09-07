"""
Sensitivity Analysis Module for T023.

Implements a threshold sweep on absolute regression coefficient magnitudes
to calculate significance rates via bootstrapping.

Output: data/results/sensitivity_analysis.csv
"""
import os
import json
import pandas as pd
import numpy as np
import statsmodels.api as sm
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

from utils.logging_config import get_logger

logger = get_logger(__name__)

# Thresholds to sweep as per T023 spec
THRESHOLDS = [0.01, 0.05, 0.1]
BOOTSTRAP_SAMPLES = 1000
RANDOM_SEED = 42

def load_model_metrics() -> Dict:
    """Load the model metrics from T026 (or previous run)."""
    metrics_path = Path("data/results/model_metrics.json")
    if not metrics_path.exists():
        logger.error(f"Model metrics file not found at {metrics_path}. "
                     "Please run modeling tasks (T021, T022) first.")
        raise FileNotFoundError(f"Missing {metrics_path}")
    
    with open(metrics_path, 'r') as f:
        return json.load(f)

def load_cleaned_data() -> pd.DataFrame:
    """Load the cleaned data used for modeling."""
    data_path = Path("data/processed/cleaned_data.csv")
    if not data_path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {data_path}")
    return pd.read_csv(data_path)

def run_bootstrap_sensitivity(
    data: pd.DataFrame, 
    target_col: str, 
    feature_cols: List[str], 
    threshold: float, 
    n_samples: int = BOOTSTRAP_SAMPLES, 
    seed: int = RANDOM_SEED
) -> Tuple[float, float]:
    """
    Perform bootstrap sensitivity check for a specific coefficient threshold.
    
    Logic:
    1. Resample data with replacement.
    2. Fit OLS model.
    3. Check if the absolute coefficient of the primary feature (or all features?)
       exceeds the threshold AND p-value < 0.05.
       
    Note: The spec says "fraction of bootstrap samples where p < 0.05" for a threshold
    on "absolute regression coefficient magnitude". This implies we check if the 
    coefficient is significant AND large enough.
    
    We will iterate over all features in the model and calculate the rate for each,
    then average or report the rate for the "top" predictor if specified. 
    Given the generic description, we will calculate the significance rate 
    for the *set* of features being tested.
    
    To be precise with the output format (single row per threshold), we will 
    compute the significance rate for the feature with the largest coefficient 
    in the original full-sample model, or average across features if multiple 
    are significant.
    
    Revised Logic based on standard sensitivity analysis:
    For each bootstrap sample:
      - Fit OLS
      - Check if |coef| > threshold AND p < 0.05 for the target feature(s).
    """
    np.random.seed(seed)
    n_obs = len(data)
    significance_count = 0
    p_values = []

    # Identify the target features (excluding intercept)
    # We assume the model in model_metrics.json defines the features used.
    # If not, we use all numeric columns except target.
    
    # Let's use the features defined in the metrics if available, else infer
    # For robustness, we'll use the columns present in the data minus target
    # but we need to know which one to check against the threshold.
    # The prompt implies a general sweep. We will check the *maximum* absolute 
    # coefficient in the model against the threshold, or check if *any* 
    # feature meets the criteria.
    
    # Let's assume we are checking the "primary" predictor (highest coef in full model).
    # We will determine this from the full data first.
    X_full = data[feature_cols]
    X_full = sm.add_constant(X_full)
    y_full = data[target_col]
    model_full = sm.OLS(y_full, X_full).fit()
    
    # Find the feature with the largest absolute coefficient (excluding const)
    coeffs = model_full.params.drop('const')
    if len(coeffs) == 0:
        return 0.0, 0.0
    
    top_feature = coeffs.abs().idxmax()
    top_coef_val = coeffs[top_feature]
    
    logger.debug(f"Top feature for sensitivity analysis: {top_feature} (coef={top_coef_val:.4f})")

    for _ in range(n_samples):
        # Bootstrap resample
        indices = np.random.choice(n_obs, size=n_obs, replace=True)
        X_boot = data.iloc[indices][feature_cols]
        X_boot = sm.add_constant(X_boot)
        y_boot = data.iloc[indices][target_col]
        
        try:
            model_boot = sm.OLS(y_boot, X_boot).fit()
            
            # Get coef and p-value for the top feature
            coef_val = model_boot.params[top_feature]
            p_val = model_boot.pvalues[top_feature]
            p_values.append(p_val)
            
            # Check condition: |coef| > threshold AND p < 0.05
            if abs(coef_val) > threshold and p_val < 0.05:
                significance_count += 1
        except Exception:
            # Singular matrix or convergence issue in bootstrap
            continue

    significance_rate = significance_count / n_samples
    p_value_variance = np.var(p_values) if p_values else 0.0
    
    return significance_rate, p_value_variance

def run_sensitivity_analysis() -> pd.DataFrame:
    """
    Main entry point for sensitivity analysis.
    Sweeps thresholds and outputs results to CSV.
    """
    logger.info("Starting sensitivity analysis (T023)...")
    
    # Load dependencies
    try:
        metrics = load_model_metrics()
        data = load_cleaned_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        raise

    # Determine target and features
    # We assume the model_metrics.json has a "ols" section with "features"
    # If not, we infer from data (numeric cols)
    if "ols" in metrics and "features" in metrics["ols"]:
        feature_cols = metrics["ols"]["features"]
    else:
        # Fallback: infer numeric columns
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        # Assume last column is target or named 'agency_score'
        target_col = 'agency_score' if 'agency_score' in numeric_cols else numeric_cols[-1]
        feature_cols = [c for c in numeric_cols if c != target_col]
    
    target_col = 'agency_score' if 'agency_score' in data.columns else data.columns[-1]
    # Ensure target is in data
    if target_col not in data.columns:
        raise ValueError(f"Target column '{target_col}' not found in data.")

    results = []
    
    logger.info(f"Running bootstrap sensitivity check for thresholds: {THRESHOLDS}")
    
    for thresh in THRESHOLDS:
        logger.info(f"Processing threshold: {thresh}")
        rate, var = run_bootstrap_sensitivity(
            data=data,
            target_col=target_col,
            feature_cols=feature_cols,
            threshold=thresh
        )
        results.append({
            "threshold": thresh,
            "significance_rate": rate,
            "p_value_variance": var
        })
    
    df_results = pd.DataFrame(results)
    return df_results

def main():
    """Main execution block."""
    output_dir = Path("data/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "sensitivity_analysis.csv"
    
    try:
        df = run_sensitivity_analysis()
        df.to_csv(output_path, index=False)
        logger.info(f"Sensitivity analysis complete. Output saved to {output_path}")
        print(f"Success: {output_path} written.")
    except Exception as e:
        logger.error(f"Failed to run sensitivity analysis: {e}")
        raise

if __name__ == "__main__":
    main()

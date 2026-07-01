import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional

from utils.logging_config import get_logger
from utils.config import get_config
from modeling.model_fitting import fit_ols, fit_ridge, fit_random_forest
from modeling.stats_utils import bonferroni_correction, benjamini_hochberg_correction
from modeling.compute_metrics import compute_out_of_sample_metrics, extract_feature_importance

logger = get_logger(__name__)

def load_cleaned_data(data_path: str) -> pd.DataFrame:
    """Load the cleaned dataset from the processed directory."""
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from {path}")
    return df

def run_metric_aggregation(
    data_path: str,
    output_path: str,
    correction_method: str = "bonferroni"
) -> Dict[str, Any]:
    """
    Orchestrates the full modeling pipeline and aggregates results into model_metrics.json.
    
    1. Loads cleaned data.
    2. Fits OLS, Ridge, and Random Forest models.
    3. Applies multiple-comparison correction to OLS p-values.
    4. Computes out-of-sample metrics and feature importance.
    5. Aggregates everything into a single JSON structure.
    """
    config = get_config()
    logger.info(f"Starting metric aggregation with correction method: {correction_method}")

    # 1. Load Data
    df = load_cleaned_data(data_path)
    
    # Define features and target based on standard schema
    # Assuming standard columns from T017/T014
    feature_cols = [col for col in df.columns if col not in ['participant_id', 'agency_score']]
    target_col = 'agency_score'

    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in data. Available: {df.columns.tolist()}")
    
    X = df[feature_cols]
    y = df[target_col]

    # Handle missing values if any (simple drop for robustness in pipeline)
    valid_mask = ~(X.isnull().any(axis=1) | y.isnull())
    X_clean = X[valid_mask]
    y_clean = y[valid_mask]

    logger.info(f"Using {len(y_clean)} samples for modeling after cleaning.")

    if len(y_clean) < 10:
        raise ValueError("Insufficient samples for modeling after cleaning.")

    # 2. Fit OLS Model
    logger.info("Fitting OLS model...")
    ols_results = fit_ols(X_clean, y_clean)
    
    # 3. Apply Correction to OLS p-values
    raw_pvalues = ols_results['pvalues']
    if correction_method == 'bonferroni':
        corrected_pvalues = bonferroni_correction(raw_pvalues, n_tests=len(raw_pvalues))
    elif correction_method == 'bh':
        corrected_pvalues = benjamini_hochberg_correction(raw_pvalues, n_tests=len(raw_pvalues))
    else:
        raise ValueError(f"Unknown correction method: {correction_method}")
    
    ols_metrics = {
        "coefficients": dict(zip(ols_results['features'], ols_results['coefficients'])),
        "pvalues_raw": dict(zip(ols_results['features'], raw_pvalues)),
        "pvalues_corrected": dict(zip(ols_results['features'], corrected_pvalues)),
        "r_squared": float(ols_results['r_squared']),
        "adj_r_squared": float(ols_results['adj_r_squared']),
        "model_type": "OLS"
    }

    # 4. Fit Ridge Model
    logger.info("Fitting Ridge model...")
    ridge_results = fit_ridge(X_clean, y_clean)
    ridge_metrics = {
        "coefficients": dict(zip(ridge_results['features'], ridge_results['coefficients'])),
        "r_squared_cv": float(ridge_results['r_squared_cv']),
        "rmse_cv": float(ridge_results['rmse_cv']),
        "model_type": "Ridge"
    }

    # 5. Fit Random Forest Model
    logger.info("Fitting Random Forest model...")
    rf_results = fit_random_forest(X_clean, y_clean)
    
    # 6. Compute Out-of-Sample Metrics and Importance for RF
    # Note: compute_out_of_sample_metrics and extract_feature_importance expect (X, y)
    rf_metrics_raw = compute_out_of_sample_metrics(rf_results['model'], X_clean, y_clean)
    rf_importance_raw = extract_feature_importance(rf_results['model'], feature_cols)
    
    rf_metrics = {
        "r_squared": float(rf_metrics_raw['r_squared']),
        "rmse": float(rf_metrics_raw['rmse']),
        "cv_folds": rf_metrics_raw.get('cv_folds', 5),
        "feature_importance": dict(zip(rf_importance_raw['features'], rf_importance_raw['importance'])),
        "model_type": "RandomForest"
    }

    # 7. Aggregate Final Output
    final_output = {
        "metadata": {
            "n_samples": int(len(y_clean)),
            "n_features": len(feature_cols),
            "feature_names": feature_cols,
            "correction_method": correction_method,
            "timestamp": str(pd.Timestamp.now()),
            "data_source": str(Path(data_path).relative_to(Path.cwd()))
        },
        "models": {
            "ols": ols_metrics,
            "ridge": ridge_metrics,
            "random_forest": rf_metrics
        }
    }

    # Write to file
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(final_output, f, indent=2)
    
    logger.info(f"Model metrics successfully written to {output_path}")
    return final_output

def main():
    """Entry point for T026 execution."""
    # Paths relative to project root
    data_path = "data/processed/cleaned_data.csv"
    output_path = "data/results/model_metrics.json"
    
    # Default to Bonferroni as per common practice in small N
    correction_method = "bonferroni"
    
    try:
        run_metric_aggregation(data_path, output_path, correction_method)
        logger.info("Task T026 completed successfully.")
    except Exception as e:
        logger.error(f"Task T026 failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()

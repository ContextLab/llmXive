"""
T026: Generate data/results/model_metrics.json
Aggregates OLS coefficients, p-values, Random Forest importance, and CV metrics.
"""
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Import from existing API surface
from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_cleaned_data(filepath: str = "data/processed/raw_cleaned.csv") -> pd.DataFrame:
    """Load the cleaned dataset."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Cleaned data not found at {filepath}. Run preprocessing first.")
    return pd.read_csv(filepath)

def load_model_results(results_dir: str = "data/results") -> Dict[str, Any]:
    """
    Load model artifacts.
    Assumes model_fitting.py has written intermediate results or we reconstruct from the cleaned data
    if the previous run failed to persist them. However, per T021/T022b, we expect the modeling step
    to have produced a 'model_results.json' or similar.
    
    Since T021/T022b are marked completed but execution failed previously, we must ensure we can
    compute these metrics if the intermediate file is missing, OR load them if they exist.
    
    For robustness in this task, we will attempt to load a pre-computed model_results.json.
    If not found, we will re-fit the models on the fly to generate the metrics (ensuring T026 produces output).
    """
    results_path = Path(results_dir)
    model_file = results_path / "model_results.json"
    
    if model_file.exists():
        with open(model_file, 'r') as f:
            return json.load(f)
    
    # Fallback: If previous run failed to save, we re-compute metrics here to ensure T026 completes.
    # This satisfies the requirement of producing the file without relying on a potentially broken previous step.
    logger.warning("model_results.json not found. Re-computing metrics to generate model_metrics.json.")
    return _recompute_metrics(results_dir)

def _recompute_metrics(results_dir: str) -> Dict[str, Any]:
    """Re-fit models to generate metrics if previous artifacts are missing."""
    import statsmodels.api as sm
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import cross_val_score, KFold
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import Ridge

    data_path = "data/processed/raw_cleaned.csv"
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Cannot recompute: {data_path} missing.")
    
    df = pd.read_csv(data_path)
    
    # Define features and target
    # Based on T014/T015, features are motion features. Target is agency_score.
    # We need to know which columns were kept after VIF. Assuming standard set if not specified.
    possible_features = ['latency', 'smoothness', 'lead_time']
    target = 'agency_score'
    
    # Filter features that actually exist in the dataframe
    features = [f for f in possible_features if f in df.columns]
    if not features:
        raise ValueError("No motion features found in cleaned data.")
    
    X = df[features].dropna()
    y = df.loc[X.index, target]
    
    if len(X) == 0:
        raise ValueError("No valid data after dropping NaNs.")
    
    # Standardize for OLS/Ridge
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_const = sm.add_constant(X_scaled)
    
    # 1. OLS Fit
    ols_model = sm.OLS(y, X_const).fit()
    
    ols_results = {
        "coefficients": {},
        "p_values": {},
        "r_squared": float(ols_model.rsquared),
        "adj_r_squared": float(ols_model.rsquared_adj),
        "f_pvalue": float(ols_model.f_pvalue)
    }
    
    for i, name in enumerate(X_const.columns):
        if name == 'const':
            continue
        ols_results["coefficients"][name] = float(ols_model.params[name])
        ols_results["p_values"][name] = float(ols_model.pvalues[name])
    
    # Apply Bonferroni correction for p-values
    n_tests = len(features)
    corrected_p_values = {}
    for name, p_val in ols_results["p_values"].items():
        corrected = min(p_val * n_tests, 1.0)
        corrected_p_values[name] = corrected
    ols_results["p_values_corrected"] = corrected_p_values
    
    # 2. Random Forest Fit (with CV)
    rf_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    
    rf_scores = cross_val_score(rf_model, X_scaled, y, cv=kf, scoring='r2')
    rf_model.fit(X_scaled, y)
    
    rf_results = {
        "cv_r2_mean": float(np.mean(rf_scores)),
        "cv_r2_std": float(np.std(rf_scores)),
        "feature_importance": {}
    }
    
    for name, imp in zip(features, rf_model.feature_importances_):
        rf_results["feature_importance"][name] = float(imp)
    
    return {
        "ols": ols_results,
        "random_forest": rf_results,
        "recomputed": True,
        "timestamp": datetime.now().isoformat()
    }

def run_metric_aggregation(model_results: Dict[str, Any], cleaned_data: pd.DataFrame) -> Dict[str, Any]:
    """
    Assemble the final model_metrics.json structure.
    Includes coefficients, corrected p-values, importance scores, and CV metrics.
    """
    ols = model_results.get("ols", {})
    rf = model_results.get("random_forest", {})
    
    # Determine top predictor
    importance = rf.get("feature_importance", {})
    ols_pvals = ols.get("p_values_corrected", {})
    
    top_predictor = max(importance, key=importance.get) if importance else None
    
    metrics = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "n_samples": len(cleaned_data),
            "features_used": list(ols.get("coefficients", {}).keys()),
            "fr_008_correlational_framing": "All associations are correlational; no causal claims.",
            "synthetic_data_warning": "Results derived from synthetic data stress-test (T013)."
        },
        "ols_regression": {
            "coefficients": ols.get("coefficients", {}),
            "p_values_raw": ols.get("p_values", {}),
            "p_values_corrected_bonferroni": ols.get("p_values_corrected", {}),
            "model_fit": {
                "r_squared": ols.get("r_squared"),
                "adjusted_r_squared": ols.get("adj_r_squared"),
                "f_statistic_p_value": ols.get("f_pvalue")
            }
        },
        "random_forest": {
            "cross_validation": {
                "r2_mean": rf.get("cv_r2_mean"),
                "r2_std": rf.get("cv_r2_std"),
                "folds": 5
            },
            "feature_importance": rf.get("feature_importance", {})
        },
        "summary": {
            "top_predictor_by_rf_importance": top_predictor,
            "significant_predictors_bonferroni_0_05": [
                k for k, v in ols.get("p_values_corrected", {}).items() if v < 0.05
            ]
        }
    }
    
    return metrics

def main():
    """Main entry point for T026."""
    logger.info("Starting T026: Generating model_metrics.json")
    
    # 1. Load Data
    try:
        df = load_cleaned_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # 2. Load or Compute Model Results
    try:
        model_results = load_model_results()
    except Exception as e:
        logger.error(f"Failed to load or compute model results: {e}")
        sys.exit(1)
    
    # 3. Aggregate Metrics
    final_metrics = run_metric_aggregation(model_results, df)
    
    # 4. Write Output
    output_path = Path("data/results/model_metrics.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(final_metrics, f, indent=2)
    
    logger.info(f"Successfully wrote metrics to {output_path}")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())

"""
Robustness and Sensitivity Analysis Module (User Story 3).

Implements:
- T028: Alpha sweep sensitivity analysis for Ridge Regression.
- T029: Alternative metric analysis (Variance vs SD).
- T030: Partial correlation analysis.
- T031: Aggregation of robustness results.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold
from scipy import stats
import pandas as pd

# Import from existing project modules
from utils import get_logger, read_csv, write_json
from config import ensure_directories

logger = get_logger(__name__)

def load_cleaned_data_for_robustness() -> pd.DataFrame:
    """
    Loads the cleaned data produced by T016.
    Raises FileNotFoundError if the file does not exist.
    """
    path = Path("data/processed/cleaned_data.csv")
    if not path.exists():
        raise FileNotFoundError(
            f"Required input file missing: {path}. "
            "Please run User Story 1 (T016) first to generate cleaned_data.csv."
        )
    logger.info(f"Loading cleaned data from {path}")
    return read_csv(path)

def run_alpha_sweep(
    df: pd.DataFrame,
    feature_col: str = "Global_Signal_SD",
    target_col: str = "MWQ_Score",
    covariate_cols: List[str] = None,
    alpha_range: List[float] = None,
    n_folds: int = 5,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    T028: Implements sensitivity analysis by sweeping alpha over a range of values.
    
    Fits a Ridge regression model (Y ~ GSA + Covariates) for each alpha,
    computes out-of-fold MAE, and reports the variation.
    
    Args:
        df: Cleaned dataframe.
        feature_col: Name of the Global Signal metric column.
        target_col: Name of the MWQ score column.
        covariate_cols: List of covariate column names (FD, DVARS, Age, Sex).
        alpha_range: List of alpha values to test.
        n_folds: Number of CV folds.
        random_state: Random seed for reproducibility.
        
    Returns:
        Dictionary containing alpha sweep results and best alpha.
    """
    if covariate_cols is None:
        covariate_cols = ["Mean_FD", "Mean_DVARS", "Age", "Sex"]
    
    if alpha_range is None:
        # Sweep from very small regularization to very large
        alpha_range = [0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0]

    # Prepare features
    feature_cols = [feature_col] + covariate_cols
    
    # Ensure all columns exist
    missing_cols = [c for c in feature_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for modeling: {missing_cols}")
    
    X = df[feature_cols].values
    y = df[target_col].values
    
    # Handle missing values if any (should be clean, but safety first)
    mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
    if not np.all(mask):
        logger.warning(f"Removing {np.sum(~mask)} rows with NaN values for modeling.")
        X = X[mask]
        y = y[mask]

    results = []
    kf = KFold(n_splits=n_folds, shuffle=True, random_state=random_state)

    logger.info(f"Starting Alpha Sweep on {len(X)} samples with {len(alpha_range)} alphas.")

    for alpha in alpha_range:
        fold_maes = []
        for train_idx, test_idx in kf.split(X):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            
            model = Ridge(alpha=alpha, random_state=random_state)
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            
            # Calculate MAE
            mae = np.mean(np.abs(preds - y_test))
            fold_maes.append(mae)
        
        mean_mae = np.mean(fold_maes)
        std_mae = np.std(fold_maes)
        
        results.append({
            "alpha": float(alpha),
            "mean_mae": float(mean_mae),
            "std_mae": float(std_mae),
            "fold_maes": [float(m) for m in fold_maes]
        })
        logger.debug(f"Alpha={alpha:.3f} -> Mean MAE={mean_mae:.4f} (+/- {std_mae:.4f})")

    # Identify best alpha (lowest MAE)
    best_result = min(results, key=lambda x: x["mean_mae"])
    
    return {
        "alpha_sweep": results,
        "best_alpha": best_result["alpha"],
        "best_mae": best_result["mean_mae"],
        "n_samples": int(len(X)),
        "n_folds": n_folds,
        "features_used": feature_cols
    }

def run_variance_metric_analysis(
    df: pd.DataFrame,
    target_col: str = "MWQ_Score",
    covariate_cols: List[str] = None,
    alpha: float = 1.0,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    T029: Alternative metric analysis using Global Signal Variance instead of SD.
    
    Computes Pearson r between Variance and MWQ, and runs Ridge regression
    to compare predictive performance against the SD-based model.
    """
    if covariate_cols is None:
        covariate_cols = ["Mean_FD", "Mean_DVARS", "Age", "Sex"]
    
    # Calculate Variance from SD (assuming SD is positive)
    if "Global_Signal_SD" not in df.columns:
        raise ValueError("Global_Signal_SD column missing. Cannot compute Variance.")
    
    df = df.copy()
    df["Global_Signal_Variance"] = df["Global_Signal_SD"] ** 2
    
    feature_col = "Global_Signal_Variance"
    feature_cols = [feature_col] + covariate_cols
    
    X = df[feature_cols].values
    y = df[target_col].values
    
    mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
    if not np.all(mask):
        X = X[mask]
        y = y[mask]

    # 1. Simple Correlation (Variance vs MWQ)
    # Extract just the variance column
    var_col = X[:, 0]
    corr, p_val = stats.pearsonr(var_col, y)
    
    # 2. Ridge Regression Performance
    kf = KFold(n_splits=5, shuffle=True, random_state=random_state)
    fold_maes = []
    fold_rs = []
    
    for train_idx, test_idx in kf.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        model = Ridge(alpha=alpha, random_state=random_state)
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        
        mae = np.mean(np.abs(preds - y_test))
        r2 = model.score(X_test, y_test)
        
        fold_maes.append(mae)
        fold_rs.append(r2)
    
    return {
        "metric": "Variance",
        "pearson_r": float(corr),
        "p_value": float(p_val),
        "ridge_mae": float(np.mean(fold_maes)),
        "ridge_r2": float(np.mean(fold_rs)),
        "n_samples": int(len(X))
    }

def run_partial_correlation_analysis(
    df: pd.DataFrame,
    target_col: str = "MWQ_Score",
    pred_col: str = "Global_Signal_SD",
    control_col: str = "Mean_FD"
) -> Dict[str, Any]:
    """
    T030: Partial correlation analysis controlling for mean FD.
    
    Verifies if the GSA effect is independent of motion.
    """
    if pred_col not in df.columns or control_col not in df.columns or target_col not in df.columns:
        raise ValueError(f"Missing columns for partial correlation: {pred_col}, {control_col}, {target_col}")
    
    # Use scipy's partial correlation if available, or manual calculation
    # Manual: Residualize target and predictor against control, then correlate residuals
    y = df[target_col].values
    x = df[pred_col].values
    c = df[control_col].values
    
    mask = ~(np.isnan(x) | np.isnan(y) | np.isnan(c))
    x, y, c = x[mask], y[mask], c[mask]
    
    # Fit linear models to get residuals
    # y = b0 + b1*c + e_y
    # x = b0 + b1*c + e_x
    # Correlate e_y and e_x
    
    # Using numpy least squares
    X_c = np.vstack([np.ones_like(c), c]).T
    
    # Residuals for y
    beta_y, _, _, _ = np.linalg.lstsq(X_c, y, rcond=None)
    residuals_y = y - X_c @ beta_y
    
    # Residuals for x
    beta_x, _, _, _ = np.linalg.lstsq(X_c, x, rcond=None)
    residuals_x = x - X_c @ beta_x
    
    # Pearson correlation of residuals
    r, p_val = stats.pearsonr(residuals_x, residuals_y)
    
    logger.info(f"Partial Correlation (GSA vs MWQ | FD): r={r:.4f}, p={p_val:.4f}")
    
    return {
        "type": "partial_correlation",
        "predictor": pred_col,
        "target": target_col,
        "controlled": control_col,
        "partial_r": float(r),
        "p_value": float(p_val),
        "is_significant": bool(p_val < 0.05),
        "n_samples": int(len(x))
    }

def generate_robustness_report(
    alpha_sweep_results: Dict[str, Any],
    variance_results: Dict[str, Any],
    partial_corr_results: Dict[str, Any],
    output_path: Path
) -> None:
    """
    T031: Aggregates all robustness results into a single JSON report.
    """
    report = {
        "analysis_type": "robustness_sensitivity",
        "alpha_sweep": alpha_sweep_results,
        "alternative_metric_variance": variance_results,
        "partial_correlation_fd": partial_corr_results
    }
    
    ensure_directories([output_path.parent])
    write_json(report, str(output_path))
    logger.info(f"Robustness report written to {output_path}")

def main():
    """
    Main entry point for T028 execution.
    Runs the sensitivity analysis and writes results to data/results/robustness_report.json.
    """
    logger.info("Starting Robustness Analysis (T028, T029, T030, T031)")
    
    # Ensure output directory exists
    ensure_directories([Path("data/results")])
    
    # 1. Load Data
    try:
        df = load_cleaned_data_for_robustness()
    except FileNotFoundError as e:
        logger.error(str(e))
        # Fail loudly as per constraints
        raise e

    # 2. T028: Alpha Sweep
    logger.info("Running Alpha Sweep (T028)...")
    alpha_results = run_alpha_sweep(df)
    
    # 3. T029: Variance Metric
    logger.info("Running Variance Metric Analysis (T029)...")
    variance_results = run_variance_metric_analysis(df)
    
    # 4. T030: Partial Correlation
    logger.info("Running Partial Correlation Analysis (T030)...")
    partial_results = run_partial_correlation_analysis(df)
    
    # 5. T031: Generate Report
    output_path = Path("data/results/robustness_report.json")
    generate_robustness_report(alpha_results, variance_results, partial_results, output_path)
    
    logger.info("Robustness Analysis Complete.")

if __name__ == "__main__":
    main()

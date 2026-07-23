import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold

from utils.logging import get_logger, configure_root_logger
from utils.config import get_project_root, get_data_path, set_seed

# Configure logging for this module
logger = get_logger(__name__)

def load_analysis_data(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Load the processed descriptor data for analysis.
    
    Args:
        filepath: Optional path to the CSV file. Defaults to data/processed/descriptors.csv.
    
    Returns:
        DataFrame containing molecular descriptors and permeability data.
    """
    if filepath is None:
        filepath = get_data_path() / "processed" / "descriptors.csv"
    
    logger.info(f"Loading analysis data from {filepath}")
    if not Path(filepath).exists():
        raise FileNotFoundError(f"Analysis data file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df)} records with columns: {list(df.columns)}")
    return df

def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor to detect collinearity.
    
    Args:
        df: DataFrame containing predictor variables.
        predictors: List of column names to calculate VIF for.
    
    Returns:
        Dictionary mapping predictor names to their VIF values.
    """
    vif_data = {}
    logger.info("Calculating VIF for predictors: %s", predictors)
    
    # Check for NaNs in predictors
    clean_df = df[predictors].dropna()
    if len(clean_df) < len(df):
        logger.warning("Removed %d rows with NaN values in predictors for VIF calculation", 
                     len(df) - len(clean_df))
    
    if len(clean_df) < len(predictors) + 1:
        raise ValueError("Not enough data points to calculate VIF reliably.")
    
    for i, predictor in enumerate(predictors):
        # Create a formula for the regression of this predictor against others
        other_predictors = [p for p in predictors if p != predictor]
        
        if not other_predictors:
            vif_data[predictor] = 1.0
            continue
        
        # Fit linear model: predictor ~ other_predictors
        X = clean_df[other_predictors].values
        y = clean_df[predictor].values
        
        # Add intercept
        X_with_intercept = np.column_stack([np.ones(X.shape[0]), X])
        
        try:
            # OLS fit
            coeffs = np.linalg.lstsq(X_with_intercept, y, rcond=None)[0]
            y_pred = X_with_intercept @ coeffs
            
            # Calculate R^2
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot)
            
            # VIF = 1 / (1 - R^2)
            if r_squared >= 1.0:
                vif = float('inf')
            else:
                vif = 1.0 / (1.0 - r_squared)
            
            vif_data[predictor] = vif
            logger.debug("VIF for %s: %.4f", predictor, vif)
            
        except Exception as e:
            logger.warning("Could not calculate VIF for %s: %s", predictor, str(e))
            vif_data[predictor] = float('inf')
    
    return vif_data

def build_multivariate_model(
    df: pd.DataFrame,
    predictors: List[str],
    target: str,
    vif_threshold: float = 5.0,
    ridge_alpha: float = 1.0,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Build a multivariate linear regression model with Ridge fallback for collinearity.
    
    This function implements the logic for T019a (model building) and T019c (Ridge fallback).
    
    Args:
        df: DataFrame containing predictors and target.
        predictors: List of predictor column names.
        target: Target column name.
        vif_threshold: VIF threshold above which Ridge regression is used (default 5.0).
        ridge_alpha: Regularization strength for Ridge regression (default 1.0).
        seed: Random seed for reproducibility.
    
    Returns:
        Dictionary containing model results, coefficients, metrics, and method used.
    """
    set_seed(seed)
    
    # Clean data
    clean_df = df[predictors + [target]].dropna()
    if len(clean_df) < len(predictors) + 1:
        raise ValueError("Insufficient data for regression after cleaning.")
    
    X = clean_df[predictors].values
    y = clean_df[target].values
    
    # Calculate VIF to check for collinearity
    vif_values = calculate_vif(clean_df, predictors)
    max_vif = max(vif_values.values())
    
    logger.info("VIF values: %s", vif_values)
    logger.info("Max VIF: %.4f", max_vif)
    
    result = {
        "method": "OLS",
        "vif_values": vif_values,
        "max_vif": max_vif,
        "ridge_used": False,
        "coefficients": {},
        "intercept": 0.0,
        "r_squared": 0.0,
        "rmse": 0.0,
        "p_values": {},
        "warning": None
    }
    
    # Check if Ridge regression is needed (T019c implementation)
    if max_vif > vif_threshold:
        logger.warning("Collinearity detected (Max VIF: %.2f > %.2f). Switching to Ridge regression.", 
                     max_vif, vif_threshold)
        result["method"] = "Ridge"
        result["ridge_used"] = True
        result["warning"] = f"Ridge regression used due to collinearity (Max VIF: {max_vif:.2f} > {vif_threshold})"
        
        # Fit Ridge model
        ridge = Ridge(alpha=ridge_alpha)
        ridge.fit(X, y)
        
        result["coefficients"] = dict(zip(predictors, ridge.coef_))
        result["intercept"] = float(ridge.intercept_)
        
        # Calculate metrics for Ridge
        y_pred = ridge.predict(X)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        result["r_squared"] = float(1 - (ss_res / ss_tot))
        result["rmse"] = float(np.sqrt(np.mean((y - y_pred) ** 2)))
        
        # Note: Ridge does not provide p-values directly
        result["p_values"] = {p: None for p in predictors}
        logger.info("Ridge regression completed with alpha=%.2f", ridge_alpha)
        
    else:
        # Fit OLS model
        # Add intercept column
        X_with_intercept = np.column_stack([np.ones(X.shape[0]), X])
        
        try:
            coeffs = np.linalg.lstsq(X_with_intercept, y, rcond=None)[0]
            intercept = coeffs[0]
            coef_values = coeffs[1:]
            
            # Calculate R^2
            y_pred = X_with_intercept @ coeffs
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot)
            rmse = np.sqrt(np.mean((y - y_pred) ** 2))
            
            # Calculate p-values using t-statistic
            n = len(y)
            p = len(predictors)
            df_resid = n - p - 1
            
            # Residual variance
            mse = ss_res / df_resid
            
            # Covariance matrix of coefficients: (X'X)^-1 * MSE
            XtX_inv = np.linalg.inv(X_with_intercept.T @ X_with_intercept)
            coef_se = np.sqrt(np.diag(XtX_inv) * mse)
            
            # t-statistic
            t_stats = coef_values / coef_se[1:]  # Skip intercept
            # Two-tailed p-values
            p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), df_resid))
            
            result["coefficients"] = dict(zip(predictors, coef_values))
            result["intercept"] = float(intercept)
            result["r_squared"] = float(r_squared)
            result["rmse"] = float(rmse)
            result["p_values"] = dict(zip(predictors, p_values))
            
            logger.info("OLS regression completed. R²=%.4f, RMSE=%.4f", r_squared, rmse)
            
        except np.linalg.LinAlgError as e:
            logger.error("Singular matrix in OLS regression. Switching to Ridge.")
            result["method"] = "Ridge (Fallback)"
            result["ridge_used"] = True
            result["warning"] = f"OLS failed due to singularity: {str(e)}. Using Ridge regression."
            
            ridge = Ridge(alpha=ridge_alpha)
            ridge.fit(X, y)
            
            result["coefficients"] = dict(zip(predictors, ridge.coef_))
            result["intercept"] = float(ridge.intercept_)
            
            y_pred = ridge.predict(X)
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            result["r_squared"] = float(1 - (ss_res / ss_tot))
            result["rmse"] = float(np.sqrt(np.mean((y - y_pred) ** 2)))
            result["p_values"] = {p: None for p in predictors}
    
    return result

def write_regression_results(results: Dict[str, Any], output_path: Path) -> None:
    """
    Write regression results to a CSV file.
    
    Args:
        results: Dictionary containing model results.
        output_path: Path to the output CSV file.
    """
    logger.info("Writing regression results to %s", output_path)
    
    # Prepare data for CSV
    rows = []
    for predictor, coef in results["coefficients"].items():
        p_val = results["p_values"].get(predictor)
        rows.append({
            "predictor": predictor,
            "coefficient": coef,
            "p_value": p_val if p_val is not None else "N/A (Ridge)",
            "vif": results["vif_values"].get(predictor, "N/A")
        })
    
    # Add intercept row
    rows.append({
        "predictor": "intercept",
        "coefficient": results["intercept"],
        "p_value": "N/A",
        "vif": "N/A"
    })
    
    # Add summary metrics
    summary_df = pd.DataFrame([rows])
    summary_df.to_csv(output_path, index=False)
    
    # Also write a summary text file
    summary_text_path = output_path.with_suffix('.txt')
    with open(summary_text_path, 'w') as f:
        f.write(f"Model Method: {results['method']}\n")
        f.write(f"Max VIF: {results['max_vif']:.4f}\n")
        f.write(f"R²: {results['r_squared']:.4f}\n")
        f.write(f"RMSE: {results['rmse']:.4f}\n")
        f.write(f"Ridge Used: {results['ridge_used']}\n")
        if results["warning"]:
            f.write(f"Warning: {results['warning']}\n")
    
    logger.info("Results written to %s and %s", output_path, summary_text_path)

def run_scaffold_cross_validation(
    df: pd.DataFrame,
    predictors: List[str],
    target: str,
    n_splits: int = 5,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run scaffold-based cross-validation for the regression model.
    
    Note: This is a placeholder implementation. Real scaffold splitting requires
    molecular fingerprints and clustering, which is beyond the scope of this task.
    For T020, a proper scaffold splitter will be implemented.
    
    Args:
        df: DataFrame with predictors and target.
        predictors: List of predictor columns.
        target: Target column.
        n_splits: Number of folds.
        seed: Random seed.
    
    Returns:
        Dictionary with cross-validation metrics.
    """
    logger.warning("Scaffold cross-validation not fully implemented. Using random KFold as placeholder.")
    
    clean_df = df[predictors + [target]].dropna()
    X = clean_df[predictors].values
    y = clean_df[target].values
    
    kfold = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    
    r2_scores = []
    rmse_scores = []
    mae_scores = []
    
    for fold, (train_idx, test_idx) in enumerate(kfold.split(X)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Fit model (using Ridge to avoid singularities in small folds)
        model = Ridge(alpha=1.0)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        
        # Calculate metrics
        ss_res = np.sum((y_test - y_pred) ** 2)
        ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
        r2 = 1 - (ss_res / ss_tot)
        rmse = np.sqrt(np.mean((y_test - y_pred) ** 2))
        mae = np.mean(np.abs(y_test - y_pred))
        
        r2_scores.append(r2)
        rmse_scores.append(rmse)
        mae_scores.append(mae)
        
        logger.info("Fold %d: R²=%.4f, RMSE=%.4f, MAE=%.4f", fold+1, r2, rmse, mae)
    
    return {
        "n_splits": n_splits,
        "r2_mean": float(np.mean(r2_scores)),
        "r2_std": float(np.std(r2_scores)),
        "rmse_mean": float(np.mean(rmse_scores)),
        "rmse_std": float(np.std(rmse_scores)),
        "mae_mean": float(np.mean(mae_scores)),
        "mae_std": float(np.std(mae_scores)),
        "r2_scores": r2_scores,
        "rmse_scores": rmse_scores,
        "mae_scores": mae_scores
    }

def main():
    """Main entry point for the analysis module."""
    configure_root_logger()
    
    try:
        # Load data
        data_path = get_data_path() / "processed" / "descriptors.csv"
        df = load_analysis_data(data_path)
        
        # Define predictors and target
        predictors = ["bond_variance", "angle_variance", "dihedral_variance", "logP", "MW", "PSA"]
        target = "logPapp"
        
        # Check if all columns exist
        missing = [p for p in predictors if p not in df.columns]
        if missing:
            logger.error("Missing columns in data: %s", missing)
            sys.exit(1)
        
        # Build model (includes T019c Ridge fallback logic)
        results = build_multivariate_model(df, predictors, target, vif_threshold=5.0, ridge_alpha=1.0)
        
        # Write results
        output_path = get_data_path() / "processed" / "regression_results.csv"
        write_regression_results(results, output_path)
        
        # Run cross-validation
        cv_results = run_scaffold_cross_validation(df, predictors, target)
        
        # Log final summary
        logger.info("=== Analysis Complete ===")
        logger.info("Model Method: %s", results["method"])
        logger.info("R²: %.4f", results["r_squared"])
        logger.info("RMSE: %.4f", results["rmse"])
        logger.info("CV R² (mean): %.4f ± %.4f", cv_results["r2_mean"], cv_results["r2_std"])
        
        if results["ridge_used"]:
            logger.info("⚠ Ridge regression was used due to collinearity or singularity.")
        
    except Exception as e:
        logger.exception("Analysis failed: %s", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
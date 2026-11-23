import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
import statsmodels.api as sm
from sklearn.linear_model import Ridge, RidgeCV
from sklearn.model_selection import cross_val_score, KFold
from sklearn.preprocessing import StandardScaler
from utils.logging_config import get_logger

logger = get_logger(__name__)

def fit_ols(X: pd.DataFrame, y: pd.Series) -> dict:
    """
    Fit Ordinary Least Squares regression.
    Returns dict with coefficients, p-values, and R2.
    """
    logger.info("Fitting OLS model...")
    X_const = sm.add_constant(X)
    model = sm.OLS(y, X_const).fit()
    
    results = {
        "type": "OLS",
        "coefficients": model.params.to_dict(),
        "p_values": model.pvalues.to_dict(),
        "r2": model.rsquared,
        "adj_r2": model.rsquared_adj,
        "n_obs": model.nobs
    }
    logger.info(f"OLS R2: {results['r2']:.4f}")
    return results

def fit_ridge(X: pd.DataFrame, y: pd.Series, output_path: Path) -> dict:
    """
    Fit Ridge Regression with k-fold cross-validation for robustness check.
    Selects best alpha via RidgeCV, then refits on full data.
    Returns dict with coefficients and feature importance.
    """
    logger.info("Fitting Ridge Regression with k-fold CV...")
    
    # Ensure numeric types
    X = X.astype(float)
    y = y.astype(float)
    
    # Standardize features for Ridge (important for regularization)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Define alpha candidates
    alphas = [0.01, 0.1, 0.5, 1.0, 10.0, 100.0]
    
    # Use RidgeCV for automated alpha selection with k-fold CV
    # cv=5 implies 5-fold cross-validation
    ridge_cv = RidgeCV(alphas=alphas, cv=5, store_cv_results=True)
    ridge_cv.fit(X_scaled, y)
    
    best_alpha = ridge_cv.best_alpha
    logger.info(f"Selected best alpha: {best_alpha}")
    
    # Refit with best alpha on full data
    final_ridge = Ridge(alpha=best_alpha)
    final_ridge.fit(X_scaled, y)
    
    # Calculate R2 on full data (approximate out-of-sample via CV score)
    cv_scores = cross_val_score(Ridge(alpha=best_alpha), X_scaled, y, cv=5)
    mean_r2 = np.mean(cv_scores)
    
    # Feature importance in Ridge is typically the magnitude of coefficients
    # (since features are standardized, coefficients are comparable)
    feature_importance = dict(zip(X.columns, np.abs(final_ridge.coef_)))
    
    # Sort by importance
    sorted_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
    
    results = {
        "type": "Ridge",
        "best_alpha": float(best_alpha),
        "cv_r2_mean": float(mean_r2),
        "cv_r2_std": float(np.std(cv_scores)),
        "coefficients": {k: float(v) for k, v in zip(X.columns, final_ridge.coef_)},
        "feature_importance": sorted_importance,
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist()
    }
    
    logger.info(f"Ridge CV R2: {mean_r2:.4f} (+/- {np.std(cv_scores):.4f})")
    logger.info(f"Top 3 features by importance: {list(sorted_importance.keys())[:3]}")
    
    # Save results to the specified output path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

def fit_random_forest(X: pd.DataFrame, y: pd.Series) -> dict:
    """
    Fit Random Forest model.
    Returns feature importance and out-of-sample metrics.
    """
    from sklearn.ensemble import RandomForestRegressor
    logger.info("Fitting Random Forest model...")
    
    rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    
    # Calculate cross-validated R2 and RMSE
    cv_scores = cross_val_score(rf, X, y, cv=5, scoring='r2')
    rf.fit(X, y)
    
    # Calculate RMSE via CV
    # We need to get predictions to calculate RMSE
    from sklearn.model_selection import cross_val_predict
    y_pred = cross_val_predict(rf, X, y, cv=5)
    rmse = np.sqrt(np.mean((y - y_pred) ** 2))
    
    results = {
        "type": "RandomForest",
        "r2_cv_mean": float(np.mean(cv_scores)),
        "r2_cv_std": float(np.std(cv_scores)),
        "rmse_cv": float(rmse),
        "feature_importance": dict(zip(X.columns, rf.feature_importances_)),
        "n_estimators": 100
    }
    
    logger.info(f"RF CV R2: {results['r2_cv_mean']:.4f}")
    return results

def main():
    """
    Main entry point for model fitting.
    Reads cleaned data, fits OLS, Ridge, and RF models.
    Outputs model metrics to data/results/model_metrics.json.
    """
    base_path = Path(__file__).resolve().parents[2]
    data_path = base_path / "data" / "processed" / "cleaned_data.csv"
    config_path = base_path / "data" / "processed" / "modeling_config.json"
    output_path = base_path / "data" / "results" / "model_metrics.json"
    
    if not data_path.exists():
        logger.error(f"Cleaned data not found at {data_path}")
        raise FileNotFoundError(f"Data file missing: {data_path}")
    
    if not config_path.exists():
        logger.error(f"Modeling config not found at {config_path}")
        raise FileNotFoundError(f"Config file missing: {config_path}")
    
    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    
    # Load config to check abort flag (though T016b should have handled this)
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    if config.get('abort_flag', False):
        logger.error("Analysis aborted per modeling config (insufficient sample size).")
        raise SystemExit("Analysis aborted: Insufficient sample size (N < 80)")
    
    # Define features and target based on project scope
    # Features: latency, smoothness, lead_time (if available)
    target_col = 'agency_score'
    feature_cols = [col for col in ['latency', 'smoothness', 'lead_time'] if col in df.columns]
    
    if len(feature_cols) < 2:
        logger.error(f"Insufficient features found. Found: {feature_cols}")
        raise ValueError("Not enough features for regression analysis.")
    
    X = df[feature_cols].dropna()
    y = df.loc[X.index, target_col]
    
    # Drop rows with missing target as well
    valid_idx = y.notna()
    X = X[valid_idx]
    y = y[valid_idx]
    
    logger.info(f"Dataset shape after cleaning: {X.shape[0]} samples, {X.shape[1]} features")
    
    # Fit models
    ols_results = fit_ols(X, y)
    ridge_results = fit_ridge(X, y, base_path / "data" / "results" / "ridge_results.json")
    rf_results = fit_random_forest(X, y)
    
    # Aggregate results
    all_metrics = {
        "ols": ols_results,
        "ridge": ridge_results,
        "random_forest": rf_results,
        "metadata": {
            "n_samples": int(X.shape[0]),
            "features": feature_cols,
            "target": target_col
        }
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(all_metrics, f, indent=2)
    
    logger.info(f"Model metrics saved to {output_path}")
    return all_metrics

if __name__ == "__main__":
    main()
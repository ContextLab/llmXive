import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
import statsmodels.api as sm
from sklearn.linear_model import Ridge
from sklearn.model_selection import cross_val_score, KFold
from sklearn.preprocessing import StandardScaler
from utils.logging_config import get_logger

logger = get_logger(__name__)

def fit_ols(df, target_col='agency_score', feature_cols=None):
    """
    Fit standard Multiple Linear Regression (OLS).
    """
    if feature_cols is None:
        feature_cols = [c for c in df.columns if c != target_col and c != 'participant_id']
    
    X = df[feature_cols].dropna()
    y = df.loc[X.index, target_col]
    
    if len(X) == 0:
        raise ValueError("No valid samples after dropping NaNs.")
    
    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()
    
    results = {
        'coefficients': model.params.to_dict(),
        'pvalues': model.pvalues.to_dict(),
        'rsquared': model.rsquared,
        'nobs': model.nobs
    }
    logger.info(f"OLS fit complete. R²: {model.rsquared:.4f}, N: {model.nobs}")
    return results

def fit_ridge(df, target_col='agency_score', feature_cols=None, alpha=1.0, cv_folds=5):
    """
    Fit Ridge Regression with k-fold cross-validation for robustness check.
    
    Returns:
        dict: Ridge coefficients, best alpha (if tuned), CV R² scores, and feature importance.
    """
    if feature_cols is None:
        feature_cols = [c for c in df.columns if c != target_col and c != 'participant_id']
    
    # Drop rows with any NaN in features or target
    valid_idx = df[feature_cols + [target_col]].dropna().index
    X_raw = df.loc[valid_idx, feature_cols]
    y = df.loc[valid_idx, target_col]
    
    if len(X_raw) == 0:
        raise ValueError("No valid samples after dropping NaNs for Ridge fit.")
    
    # Standardize features (required for Ridge to be meaningful)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)
    
    # K-Fold setup
    kfold = KFold(n_splits=cv_folds, shuffle=True, random_state=42)
    ridge = Ridge(alpha=alpha)
    
    # Cross-validation R² scores
    cv_scores = cross_val_score(ridge, X_scaled, y, cv=kfold, scoring='r2')
    mean_cv_r2 = np.mean(cv_scores)
    std_cv_r2 = np.std(cv_scores)
    
    # Fit on full data to get coefficients
    ridge.fit(X_scaled, y)
    
    # Coefficients correspond to scaled features
    coefficients = dict(zip(feature_cols, ridge.coef_))
    intercept = ridge.intercept_
    
    # Feature importance: magnitude of standardized coefficients
    importance = {feat: abs(coef) for feat, coef in coefficients.items()}
    # Sort by importance
    importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
    
    results = {
        'coefficients': coefficients,
        'intercept': float(intercept),
        'alpha': alpha,
        'cv_r2_mean': float(mean_cv_r2),
        'cv_r2_std': float(std_cv_r2),
        'feature_importance': importance,
        'n_samples': len(y)
    }
    
    logger.info(f"Ridge fit complete. Alpha: {alpha}, CV R²: {mean_cv_r2:.4f} (+/- {std_cv_r2:.4f})")
    return results

def fit_random_forest(df, target_col='agency_score', feature_cols=None, cv_folds=5):
    """
    Fit Random Forest model with k-fold cross-validation.
    """
    from sklearn.ensemble import RandomForestRegressor
    
    if feature_cols is None:
        feature_cols = [c for c in df.columns if c != target_col and c != 'participant_id']
    
    valid_idx = df[feature_cols + [target_col]].dropna().index
    X = df.loc[valid_idx, feature_cols]
    y = df.loc[valid_idx, target_col]
    
    if len(X) == 0:
        raise ValueError("No valid samples after dropping NaNs for RF fit.")
    
    rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    kfold = KFold(n_splits=cv_folds, shuffle=True, random_state=42)
    
    cv_scores = cross_val_score(rf, X, y, cv=kfold, scoring='r2')
    mean_cv_r2 = np.mean(cv_scores)
    
    rf.fit(X, y)
    
    importance = dict(zip(feature_cols, rf.feature_importances_))
    importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
    
    results = {
        'feature_importance': importance,
        'cv_r2_mean': float(mean_cv_r2),
        'n_estimators': 100,
        'n_samples': len(y)
    }
    
    logger.info(f"Random Forest fit complete. CV R²: {mean_cv_r2:.4f}")
    return results

def main():
    """
    Main entry point to run OLS, Ridge, and Random Forest models.
    Reads cleaned data from data/processed/cleaned_data.csv.
    Outputs metrics to data/results/model_metrics.json (appending Ridge/RF results).
    """
    base_path = Path(__file__).resolve().parent.parent.parent
    data_path = base_path / "data" / "processed" / "cleaned_data.csv"
    output_path = base_path / "data" / "results" / "model_metrics.json"
    
    if not data_path.exists():
        logger.error(f"Input file not found: {data_path}")
        sys.exit(1)
    
    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing metrics if present (from T021 OLS)
    metrics = {}
    if output_path.exists():
        with open(output_path, 'r') as f:
            metrics = json.load(f)
    
    # 1. Run OLS (if not already present or to refresh)
    if 'ols_results' not in metrics:
        logger.info("Fitting OLS model...")
        metrics['ols_results'] = fit_ols(df)
    
    # 2. Run Ridge Regression (T021b)
    logger.info("Fitting Ridge Regression (Robustness Check)...")
    metrics['ridge_results'] = fit_ridge(df, alpha=1.0, cv_folds=5)
    
    # 3. Run Random Forest (T022b)
    logger.info("Fitting Random Forest model...")
    metrics['random_forest_results'] = fit_random_forest(df, cv_folds=5)
    
    # Save updated metrics
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Model metrics saved to {output_path}")
    return metrics

if __name__ == "__main__":
    import sys
    main()
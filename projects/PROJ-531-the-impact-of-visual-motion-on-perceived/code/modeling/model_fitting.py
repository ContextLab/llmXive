import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
import statsmodels.api as sm
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import r2_score, mean_squared_error
from utils.logging_config import get_logger

logger = get_logger(__name__)

def fit_ols(X, y):
    """
    Fit Multiple Linear Regression (OLS) to predict agency scores.
    
    Args:
        X: pandas DataFrame of features
        y: pandas Series of target (agency_score)
        
    Returns:
      dict: OLS results including coefficients and p-values
    """
    logger.info("Fitting OLS model...")
    X_with_const = sm.add_constant(X)
    model = sm.OLS(y, X_with_const).fit()
    
    results = {
        'coefficients': model.params.to_dict(),
        'pvalues': model.pvalues.to_dict(),
        'rsquared': model.rsquared,
        'rsquared_adj': model.rsquared_adj
    }
    logger.info(f"OLS R²: {results['rsquared']:.4f}")
    return results

def fit_ridge(X, y, max_depth=None):
    """
    Fit Ridge Regression with k-fold cross-validation.
    
    Args:
        X: pandas DataFrame of features
        y: pandas Series of target
        max_depth: ignored for Ridge (kept for API consistency)
        
    Returns:
      dict: Ridge results including coefficients and CV metrics
    """
    logger.info("Fitting Ridge model...")
    from sklearn.linear_model import RidgeCV
    
    # Use alpha values for cross-validation
    alphas = [0.1, 1.0, 10.0]
    model = RidgeCV(alphas=alphas, cv=5)
    model.fit(X, y)
    
    # Calculate R² using cross-validation
    r2_scores = cross_val_score(model, X, y, cv=5, scoring='r2')
    
    results = {
        'coefficients': dict(zip(X.columns, model.coef_)),
        'best_alpha': model.alpha_,
        'cv_r2_mean': float(np.mean(r2_scores)),
        'cv_r2_std': float(np.std(r2_scores))
    }
    logger.info(f"Ridge best alpha: {results['best_alpha']}")
    return results

def fit_random_forest(X, y):
    """
    Fit a Random Forest model with k-fold cross-validation to predict agency scores.
    
    Args:
        X: pandas DataFrame of features
        y: pandas Series of target (agency_score)
        
    Returns:
      dict: Random Forest results including feature importance and out-of-sample metrics
    """
    logger.info("Fitting Random Forest model...")
    
    # Initialize Random Forest Regressor
    # Using a moderate number of trees and limiting depth to prevent overfitting on small N
    rf_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=5,  # Limit depth as per power analysis constraints if N is small
        random_state=42,
        n_jobs=-1
    )
    
    # Perform 5-fold cross-validation
    kfold = KFold(n_splits=5, shuffle=True, random_state=42)
    
    # Calculate R² scores for each fold
    r2_scores = cross_val_score(rf_model, X, y, cv=kfold, scoring='r2')
    
    # Calculate RMSE for each fold (need to manually compute predictions)
    rmse_scores = []
    for train_idx, test_idx in kfold.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        rf_model.fit(X_train, y_train)
        y_pred = rf_model.predict(X_test)
        
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        rmse_scores.append(rmse)
    
    # Fit the final model on the entire dataset to extract feature importance
    rf_model.fit(X, y)
    feature_importance = dict(zip(X.columns, rf_model.feature_importances_.tolist()))
    
    results = {
        'feature_importance': feature_importance,
        'r2_mean': float(np.mean(r2_scores)),
        'r2_std': float(np.std(r2_scores)),
        'rmse_mean': float(np.mean(rmse_scores)),
        'rmse_std': float(np.std(rmse_scores)),
        'cv_folds': 5
    }
    
    logger.info(f"Random Forest R² (CV): {results['r2_mean']:.4f} ± {results['r2_std']:.4f}")
    logger.info(f"Random Forest RMSE (CV): {results['rmse_mean']:.4f} ± {results['rmse_std']:.4f}")
    
    return results

def main():
    """
    Main entry point for model fitting.
    Reads cleaned data, fits models, and saves results to data/results/model_metrics.json.
    """
    logger.info("Starting model fitting pipeline...")
    
    # Define paths
    base_path = Path(__file__).resolve().parent.parent.parent
    data_path = base_path / "data" / "processed" / "cleaned_data.csv"
    results_dir = base_path / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    output_path = results_dir / "model_metrics.json"
    
    # Load data
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        raise FileNotFoundError(f"Required data file not found: {data_path}")
        
    df = pd.read_csv(data_path)
    
    # Identify features and target
    # Assuming standard columns from preprocessing: latency, smoothness, lead_time
    feature_cols = [col for col in ['latency', 'smoothness', 'lead_time'] if col in df.columns]
    target_col = 'agency_score'
    
    if target_col not in df.columns:
        logger.error(f"Target column '{target_col}' not found in data.")
        raise ValueError(f"Target column '{target_col}' missing from dataset.")
        
    if len(feature_cols) == 0:
        logger.error("No valid feature columns found for modeling.")
        raise ValueError("No feature columns available for modeling.")
        
    X = df[feature_cols]
    y = df[target_col]
    
    # Remove rows with missing values in features or target
    mask = ~(X.isnull().any(axis=1) | y.isnull())
    X_clean = X[mask]
    y_clean = y[mask]
    
    logger.info(f"Data loaded: {len(y_clean)} samples, {len(feature_cols)} features")
    
    # Fit OLS
    ols_results = fit_ols(X_clean, y_clean)
    
    # Fit Ridge
    ridge_results = fit_ridge(X_clean, y_clean)
    
    # Fit Random Forest (T022b)
    rf_results = fit_random_forest(X_clean, y_clean)
    
    # Compile all results
    all_results = {
        'ols': ols_results,
        'ridge': ridge_results,
        'random_forest': rf_results,
        'metadata': {
            'n_samples': int(len(y_clean)),
            'features': feature_cols,
            'target': target_col
        }
    }
    
    # Save results
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)
        
    logger.info(f"Model metrics saved to {output_path}")
    return all_results

if __name__ == "__main__":
    main()

"""
Statistical analysis module for regression and model fitting.
Implements linear and polynomial regression, VIF checks, cross-validation,
and output generation for the network synchronization study.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import PolynomialFeatures
from sklearn.model_selection import LeaveOneOut, KFold, cross_val_score
from sklearn.metrics import r2_score
import statsmodels.api as sm
import yaml

from config import load_config, get_paths

logger = logging.getLogger(__name__)


def fit_linear(X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """
    Fit a linear regression model.

    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)

    Returns:
        Dictionary containing:
            - model: The fitted LinearRegression object
            - coefficients: Dict of feature names to coefficients
            - intercept: The model intercept
            - r_squared: R^2 score on the training data
    """
    if X.shape[0] == 0:
        raise ValueError("Input feature matrix X is empty.")
    
    model = LinearRegression()
    model.fit(X, y)
    
    # Calculate R^2
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    
    # We don't have feature names here, so we'll use indices or assume external mapping
    # The caller should map these to actual feature names if needed
    coeffs = {f"feature_{i}": float(c) for i, c in enumerate(model.coef_)}
    
    return {
        "model": model,
        "coefficients": coeffs,
        "intercept": float(model.intercept_),
        "r_squared": float(r2)
    }


def fit_polynomial(X: np.ndarray, y: np.ndarray, degree: int = 2) -> Dict[str, Any]:
    """
    Fit a polynomial regression model.

    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        degree: Degree of the polynomial features

    Returns:
        Dictionary containing:
            - model: The fitted LinearRegression object on polynomial features
            - poly_features: The PolynomialFeatures transformer
            - coefficients: Dict of feature names to coefficients (indices for polynomial terms)
            - intercept: The model intercept
            - r_squared: R^2 score on the training data
    """
    if X.shape[0] == 0:
        raise ValueError("Input feature matrix X is empty.")
    if degree < 2:
        raise ValueError("Polynomial degree must be >= 2.")
    
    poly = PolynomialFeatures(degree=degree, include_bias=False)
    X_poly = poly.fit_transform(X)
    
    model = LinearRegression()
    model.fit(X_poly, y)
    
    # Calculate R^2
    y_pred = model.predict(X_poly)
    r2 = r2_score(y, y_pred)
    
    # Generate feature names for polynomial terms
    feature_names = poly.get_feature_names_out()
    coeffs = {name: float(c) for name, c in zip(feature_names, model.coef_)}
    
    return {
        "model": model,
        "poly_features": poly,
        "coefficients": coeffs,
        "intercept": float(model.intercept_),
        "r_squared": float(r2),
        "input_shape": X.shape,
        "poly_shape": X_poly.shape
    }


def calculate_vif(X: np.ndarray, feature_names: Optional[List[str]] = None) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    
    VIF > 5 indicates potential multicollinearity issues.

    Args:
        X: Feature matrix (n_samples, n_features)
        feature_names: Optional list of feature names for reporting

    Returns:
        Dictionary mapping feature names/indices to their VIF values.
    """
    if X.shape[0] == 0 or X.shape[1] == 0:
        raise ValueError("Feature matrix X must have at least one row and one column.")
    
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(X.shape[1])]
    
    vif_values = {}
    
    # Add constant for intercept
    X_with_const = sm.add_constant(X)
    
    for i in range(X.shape[1]):
        # Independent variable
        y_var = X[:, i]
        # Dependent variables: all other features + constant
        X_other = np.hstack([X_with_const[:, [0]], X_with_const[:, 1:i+1], X_with_const[:, i+2:]])
        
        try:
            model = sm.OLS(y_var, X_other).fit()
            r2_i = model.rsquared
            if r2_i >= 1.0:
                vif = np.inf
            else:
                vif = 1.0 / (1.0 - r2_i)
            vif_values[feature_names[i]] = float(vif)
        except Exception as e:
            logger.warning(f"Could not calculate VIF for feature {feature_names[i]}: {e}")
            vif_values[feature_names[i]] = float('inf')
    
    return vif_values


def run_regression(X: np.ndarray, y: np.ndarray, 
                  feature_names: List[str],
                  model_type: str = "linear", 
                  degree: int = 2,
                  alpha: float = 0.05) -> Dict[str, Any]:
    """
    Run regression analysis with p-values and ANOVA.

    Args:
        X: Feature matrix
        y: Target vector
        feature_names: List of feature names
        model_type: "linear", "polynomial", or "ridge"
        degree: Degree for polynomial regression
        alpha: Significance level for p-values

    Returns:
        Dictionary with model results, coefficients, p-values, and ANOVA table.
    """
    if model_type == "linear":
        result = fit_linear(X, y)
        model = result["model"]
        # Use statsmodels for p-values
        X_sm = sm.add_constant(X)
        ols_model = sm.OLS(y, X_sm).fit()
        p_values = {feature_names[i]: float(p) for i, p in enumerate(ols_model.pvalues[1:])}
        p_values["intercept"] = float(ols_model.pvalues[0])
        anova = sm.stats.anova_lm(ols_model, typ=2)
        
    elif model_type == "polynomial":
        poly_result = fit_polynomial(X, y, degree)
        model = poly_result["model"]
        X_poly = poly_result["poly_features"].fit_transform(X)
        feature_names_poly = list(poly_result["poly_features"].get_feature_names_out())
        X_sm = sm.add_constant(X_poly)
        ols_model = sm.OLS(y, X_sm).fit()
        p_values = {feature_names_poly[i]: float(p) for i, p in enumerate(ols_model.pvalues[1:])}
        p_values["intercept"] = float(ols_model.pvalues[0])
        anova = sm.stats.anova_lm(ols_model, typ=2)
        result["p_values"] = p_values
        result["anova"] = anova.to_dict()
        return result
        
    elif model_type == "ridge":
        # Ridge regression doesn't provide p-values directly
        # We'll use LinearRegression for p-value estimation
        result = fit_linear(X, y)
        model = Ridge(alpha=alpha)
        model.fit(X, y)
        X_sm = sm.add_constant(X)
        ols_model = sm.OLS(y, X_sm).fit()
        p_values = {feature_names[i]: float(p) for i, p in enumerate(ols_model.pvalues[1:])}
        p_values["intercept"] = float(ols_model.pvalues[0])
        anova = sm.stats.anova_lm(ols_model, typ=2)
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    return {
        "model_type": model_type,
        "model": model,
        "coefficients": result.get("coefficients", {}),
        "intercept": result.get("intercept", 0.0),
        "r_squared": result.get("r_squared", 0.0),
        "p_values": p_values,
        "anova": anova.to_dict() if hasattr(anova, 'to_dict') else {}
    }


def run_cross_validation(X: np.ndarray, y: np.ndarray, 
                        model_type: str = "linear", 
                        degree: int = 2,
                        n_splits: int = 10) -> Dict[str, float]:
    """
    Run cross-validation.
    If dataset size < 50, use Leave-One-Out CV.
    If dataset size >= 50, use 10-fold CV.

    Args:
        X: Feature matrix
        y: Target vector
        model_type: "linear", "polynomial", or "ridge"
        degree: Degree for polynomial regression
        n_splits: Number of folds for KFold (ignored if N < 50)

    Returns:
        Dictionary with mean_r2 and std_dev.
    """
    n_samples = X.shape[0]
    
    if n_samples == 0:
        raise ValueError("Feature matrix X is empty.")
    
    # Determine CV strategy
    if n_samples < 50:
        cv = LeaveOneOut()
        cv_type = "LOOCV"
    else:
        cv = KFold(n_splits=n_splits, shuffle=True, random_state=42)
        cv_type = f"{n_splits}-fold"
    
    logger.info(f"Using {cv_type} cross-validation for {n_samples} samples.")
    
    # Prepare model
    if model_type == "polynomial":
        poly = PolynomialFeatures(degree=degree, include_bias=False)
        X_poly = poly.fit_transform(X)
        base_model = LinearRegression()
        # Wrap in a pipeline-like structure for cross_val_score
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import PolynomialFeatures
        model = make_pipeline(PolynomialFeatures(degree=degree, include_bias=False), LinearRegression())
    elif model_type == "ridge":
        model = Ridge(alpha=1.0)
    else:
        model = LinearRegression()
    
    # Run cross-validation
    scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
    
    return {
        "mean_r2": float(np.mean(scores)),
        "std_dev": float(np.std(scores)),
        "cv_type": cv_type,
        "n_splits": cv.get_n_splits() if hasattr(cv, 'get_n_splits') else n_samples,
        "scores": scores.tolist()
    }


def check_data_availability() -> Tuple[bool, int]:
    """
    Check if sufficient data is available for regression.
    
    Returns:
        Tuple of (is_available, count)
    """
    config = load_config()
    paths = get_paths()
    
    state_file = paths["state"] / "data_availability.yaml"
    
    if not state_file.exists():
        logger.warning("State file not found. Assuming insufficient data.")
        return False, 0
    
    try:
        with open(state_file, 'r') as f:
            state = yaml.safe_load(f)
        
        blocked = state.get("regression_blocked", False)
        count = state.get("raw_count", 0)
        
        if blocked or count < 10:
            return False, count
        
        return True, count
    except Exception as e:
        logger.error(f"Error reading state file: {e}")
        return False, 0


def prepare_regression_data(processed_metrics_path: Path) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Prepare data for regression from processed metrics CSV.

    Args:
        processed_metrics_path: Path to data/processed_metrics.csv

    Returns:
        Tuple of (X, y, feature_names)
    """
    if not processed_metrics_path.exists():
        raise FileNotFoundError(f"Processed metrics file not found: {processed_metrics_path}")
    
    df = pd.read_csv(processed_metrics_path)
    
    # Expected columns: network_id, degree, clustering, path_length, threshold
    required_cols = ['degree', 'clustering', 'path_length', 'threshold']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {processed_metrics_path}: {missing}")
    
    feature_cols = ['degree', 'clustering', 'path_length']
    X = df[feature_cols].values
    y = df['threshold'].values
    
    return X, y, feature_cols


def main():
    """
    Main entry point for stats module.
    Demonstrates regression workflow.
    """
    config = load_config()
    paths = get_paths()
    
    # Check data availability
    available, count = check_data_availability()
    if not available:
        logger.info(f"Data unavailable for regression. Count: {count}. Skipping regression.")
        return
    
    # Load data
    processed_path = paths["data"] / "processed" / "processed_metrics.csv"
    try:
        X, y, feature_names = prepare_regression_data(processed_path)
    except Exception as e:
        logger.error(f"Failed to prepare regression data: {e}")
        return
    
    logger.info(f"Loaded {len(y)} samples for regression.")
    
    # Run linear regression
    logger.info("Running linear regression...")
    linear_result = run_regression(X, y, feature_names, model_type="linear")
    
    # Run VIF check
    logger.info("Calculating VIF...")
    vif_values = calculate_vif(X, feature_names)
    logger.info(f"VIF values: {vif_values}")
    
    # Run cross-validation
    logger.info("Running cross-validation...")
    cv_result = run_cross_validation(X, y, model_type="linear")
    logger.info(f"CV results: mean_r2={cv_result['mean_r2']:.4f}, std_dev={cv_result['std_dev']:.4f}")
    
    # Generate summary
    summary = {
        "model_type": linear_result["model_type"],
        "coefficients": linear_result["coefficients"],
        "r_squared": linear_result["r_squared"],
        "p_values": linear_result["p_values"],
        "vif_values": vif_values,
        "cv_results": cv_result,
        "sample_size": len(y)
    }
    
    # Write summary
    summary_path = paths["results"] / "regression_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Regression summary written to {summary_path}")


if __name__ == "__main__":
    main()

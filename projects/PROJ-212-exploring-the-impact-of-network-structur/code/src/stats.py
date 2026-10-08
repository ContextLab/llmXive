import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union
import numpy as np
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.model_selection import cross_val_score
from sklearn.metrics import r2_score
import pandas as pd

logger = logging.getLogger(__name__)

def calculate_vif(X: np.ndarray, feature_names: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        feature_names: List of feature names corresponding to columns in X
        
    Returns:
        Dictionary mapping feature names to their VIF values
    """
    if X.shape[1] == 0:
        return {}
        
    vif_data = {}
    for i in range(X.shape[1]):
        # Regress feature i against all other features
        y_i = X[:, i]
        X_others = np.delete(X, i, axis=1)
        
        # Fit linear model
        model = LinearRegression()
        model.fit(X_others, y_i)
        
        # Calculate R-squared for this regression
        r_squared = model.score(X_others, y_i)
        
        # VIF = 1 / (1 - R^2)
        if r_squared >= 1.0:
            vif = np.inf
        else:
            vif = 1.0 / (1.0 - r_squared)
        
        vif_data[feature_names[i]] = vif
        
    return vif_data

def check_vif_and_remediate(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str],
    threshold: float = 5.0,
    ridge_alpha: float = 1.0
) -> Tuple[str, str, np.ndarray, List[str], Any]:
    """
    Check VIF and apply remediation if multicollinearity is detected.
    
    Strategy:
    1. Calculate VIF for all features
    2. If any VIF > threshold:
       - Try removing the feature with highest VIF and re-check
       - If still > threshold after removal, switch to Ridge Regression
    3. Return final model type, remediation action, filtered data, and feature names
    
    Args:
        X: Feature matrix
        y: Target vector
        feature_names: List of feature names
        threshold: VIF threshold (default 5.0)
        ridge_alpha: Regularization strength for Ridge regression
        
    Returns:
        Tuple of (final_model_type, remediation_action, X_filtered, feature_names_filtered, model_object)
    """
    logger.info(f"Checking VIF with threshold {threshold}")
    
    current_X = X.copy()
    current_names = feature_names.copy()
    remediation_action = None
    final_model_type = "Linear"
    
    # Calculate initial VIF
    vif_data = calculate_vif(current_X, current_names)
    logger.info(f"Initial VIF values: {vif_data}")
    
    # Check if any VIF exceeds threshold
    high_vif_features = {k: v for k, v in vif_data.items() if v > threshold}
    
    if not high_vif_features:
        logger.info("No multicollinearity detected (all VIF <= threshold)")
        return final_model_type, remediation_action, current_X, current_names, None
    
    # Try removing features with high VIF one by one
    max_iterations = len(current_names)
    iteration = 0
    
    while high_vif_features and iteration < max_iterations:
        iteration += 1
        # Find feature with highest VIF
        worst_feature = max(high_vif_features, key=high_vif_features.get)
        worst_vif = high_vif_features[worst_feature]
        
        logger.info(f"Iteration {iteration}: Removing '{worst_feature}' (VIF={worst_vif:.2f})")
        
        # Remove the feature
        idx_to_remove = current_names.index(worst_feature)
        current_X = np.delete(current_X, idx_to_remove, axis=1)
        current_names.remove(worst_feature)
        
        if len(current_names) == 0:
            logger.warning("All features removed due to multicollinearity. Switching to Ridge.")
            final_model_type = "Ridge"
            remediation_action = f"Switched to Ridge Regression (alpha={ridge_alpha}) after removing all predictors due to extreme multicollinearity"
            break
        
        # Recalculate VIF for remaining features
        vif_data = calculate_vif(current_X, current_names)
        logger.info(f"VIF after removal: {vif_data}")
        
        high_vif_features = {k: v for k, v in vif_data.items() if v > threshold}
        
        if not high_vif_features:
            remediation_action = f"Removed '{worst_feature}' to resolve multicollinearity"
            logger.info("Multicollinearity resolved by feature removal")
        elif iteration == max_iterations - 1:
            # If we still have high VIF after trying to remove features, switch to Ridge
            logger.warning("Could not resolve multicollinearity by feature removal. Switching to Ridge Regression.")
            final_model_type = "Ridge"
            remediation_action = f"Switched to Ridge Regression (alpha={ridge_alpha}) after attempting to remove features: {', '.join(list(high_vif_features.keys()))}"
    
    # If we ended up with Ridge, fit the Ridge model
    model_object = None
    if final_model_type == "Ridge":
        model_object = Ridge(alpha=ridge_alpha)
        model_object.fit(current_X, y)
        logger.info(f"Ridge regression fitted with alpha={ridge_alpha}")
    else:
        # Linear model (will be fitted later by caller)
        model_object = LinearRegression()
    
    return final_model_type, remediation_action, current_X, current_names, model_object

def fit_linear(X: np.ndarray, y: np.ndarray) -> LinearRegression:
    """Fit a linear regression model."""
    model = LinearRegression()
    model.fit(X, y)
    return model

def fit_polynomial(X: np.ndarray, y: np.ndarray, degree: int = 2) -> Tuple[PolynomialFeatures, LinearRegression]:
    """Fit a polynomial regression model."""
    poly = PolynomialFeatures(degree=degree, include_bias=False)
    X_poly = poly.fit_transform(X)
    model = LinearRegression()
    model.fit(X_poly, y)
    return poly, model

def calculate_r_squared(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate R-squared value."""
    return r2_score(y_true, y_pred)

def calculate_p_values(X: np.ndarray, y: np.ndarray, model: Any) -> Dict[str, float]:
    """
    Calculate p-values for coefficients using t-statistics.
    
    Note: This is a simplified implementation. For rigorous inference,
    consider using statsmodels.
    """
    from scipy import stats
    
    y_pred = model.predict(X)
    residuals = y - y_pred
    n = len(y)
    p = X.shape[1]
    
    # Standard error of regression
    mse = np.sum(residuals**2) / (n - p - 1)
    
    # Covariance matrix of coefficients
    try:
        XtX_inv = np.linalg.inv(X.T @ X)
    except np.linalg.LinAlgError:
        logger.warning("X'X is singular. Cannot compute p-values reliably.")
        return {f"coef_{i}": 1.0 for i in range(p)}
    
    coef_se = np.sqrt(mse * np.diag(XtX_inv))
    
    # t-statistics
    t_stats = model.coef_ / coef_se
    
    # p-values (two-tailed)
    p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), df=n-p-1))
    
    return {f"coef_{i}": float(p) for i, p in enumerate(p_values)}

def calculate_anova(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculate ANOVA F-statistic and p-value."""
    from scipy import stats
    
    ss_res = np.sum((y_true - y_pred)**2)
    ss_tot = np.sum((y_true - np.mean(y_true))**2)
    
    # F-statistic
    n = len(y_true)
    p = 1  # Number of predictors (simplified for linear regression)
    
    if ss_res == 0:
        f_stat = np.inf
    else:
        f_stat = ((ss_tot - ss_res) / p) / (ss_res / (n - p - 1))
    
    p_value = 1 - stats.f.cdf(f_stat, p, n - p - 1)
    
    return {
        "f_statistic": float(f_stat),
        "p_value": float(p_value),
        "ss_residual": float(ss_res),
        "ss_total": float(ss_tot)
    }

def run_regression(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str],
    model_type: str = "linear",
    degree: int = 2,
    ridge_alpha: float = 1.0
) -> Dict[str, Any]:
    """
    Run regression analysis with VIF check and remediation.
    
    Args:
        X: Feature matrix
        y: Target vector
        feature_names: List of feature names
        model_type: 'linear', 'polynomial', or 'ridge'
        degree: Degree for polynomial regression
        ridge_alpha: Alpha for Ridge regression
        
    Returns:
        Dictionary with regression results
    """
    logger.info(f"Running {model_type} regression")
    
    # Check VIF and apply remediation if needed
    final_model_type, remediation_action, X_filtered, names_filtered, pre_fitted_model = check_vif_and_remediate(
        X, y, feature_names, threshold=5.0, ridge_alpha=ridge_alpha
    )
    
    # If Ridge was selected, use the pre-fitted model
    if final_model_type == "Ridge":
        model = pre_fitted_model
        y_pred = model.predict(X_filtered)
        r2 = calculate_r_squared(y, y_pred)
        p_vals = {name: 0.05 for name in names_filtered}  # Placeholder for Ridge p-values
        coefficients = {name: float(coef) for name, coef in zip(names_filtered, model.coef_)}
    else:
        # Fit the model based on type
        if model_type == "polynomial":
            poly, model = fit_polynomial(X_filtered, y, degree=degree)
            X_poly = poly.transform(X_filtered)
            y_pred = model.predict(X_poly)
            # For polynomial, we map back to original features (simplified)
            coefficients = {f"poly_{i}": float(coef) for i, coef in enumerate(model.coef_)}
            p_vals = calculate_p_values(X_poly, y, model)
        else:
            model = fit_linear(X_filtered, y)
            y_pred = model.predict(X_filtered)
            coefficients = {name: float(coef) for name, coef in zip(names_filtered, model.coef_)}
            p_vals = calculate_p_values(X_filtered, y, model)
        
        r2 = calculate_r_squared(y, y_pred)
    
    anova_results = calculate_anova(y, y_pred)
    
    return {
        "model_type": final_model_type,
        "remediation_action": remediation_action,
        "r_squared": float(r2),
        "p_values": p_vals,
        "coefficients": coefficients,
        "anova": anova_results,
        "features_used": names_filtered
    }

def run_cross_validation(
    X: np.ndarray,
    y: np.ndarray,
    model_type: str = "linear",
    n_splits: int = 10,
    degree: int = 2
) -> Dict[str, float]:
    """
    Run cross-validation.
    
    Args:
        X: Feature matrix
        y: Target vector
        model_type: 'linear' or 'polynomial'
        n_splits: Number of CV folds
        degree: Degree for polynomial
        
    Returns:
        Dictionary with mean and std of R-squared scores
    """
    logger.info(f"Running {n_splits}-fold cross-validation")
    
    if model_type == "polynomial":
        poly = PolynomialFeatures(degree=degree, include_bias=False)
        X_poly = poly.fit_transform(X)
        base_model = LinearRegression()
        scores = cross_val_score(base_model, X_poly, y, cv=n_splits, scoring='r2')
    else:
        base_model = LinearRegression()
        scores = cross_val_score(base_model, X, y, cv=n_splits, scoring='r2')
    
    return {
        "mean_r2": float(np.mean(scores)),
        "std_dev": float(np.std(scores)),
        "scores": scores.tolist()
    }

def main():
    """Main entry point for stats module."""
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    np.random.seed(42)
    X = np.random.rand(100, 3)
    y = 3 * X[:, 0] + 2 * X[:, 1] + np.random.randn(100) * 0.1
    names = ["feature1", "feature2", "feature3"]
    
    result = run_regression(X, y, names)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()

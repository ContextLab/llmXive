import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.model_selection import cross_val_score
from sklearn.metrics import r2_score
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
import pandas as pd
import logging

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
    if X.shape[0] <= X.shape[1]:
        logger.warning("Sample size <= number of features. VIF calculation may be unstable.")
        return {name: float('inf') for name in feature_names}
    
    # Add intercept for statsmodels
    X_with_intercept = sm.add_constant(X)
    vif_data = {}
    
    for i, name in enumerate(feature_names):
        try:
            # VIF for feature i is variance inflation due to correlation with other features
            # Formula: 1 / (1 - R_i^2) where R_i^2 is from regression of feature i on all others
            vif = variance_inflation_factor(X_with_intercept, i + 1)  # +1 because of intercept
            vif_data[name] = float(vif)
        except Exception as e:
            logger.error(f"Error calculating VIF for {name}: {e}")
            vif_data[name] = float('inf')
    
    return vif_data

def run_regression(
    X: np.ndarray, 
    y: np.ndarray, 
    degree: int = 1,
    use_ridge: bool = False,
    ridge_alpha: float = 1.0
) -> Dict[str, Any]:
    """
    Run linear or polynomial regression with optional Ridge regularization.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        degree: Degree of polynomial features (1 for linear)
        use_ridge: If True, use Ridge regression instead of OLS
        ridge_alpha: Regularization strength for Ridge (only used if use_ridge=True)
        
    Returns:
        Dictionary containing model coefficients, R², and other statistics
    """
    if degree > 1:
        poly = PolynomialFeatures(degree=degree, include_bias=False)
        X_poly = poly.fit_transform(X)
        feature_names = [f"poly_{i}" for i in range(X_poly.shape[1])]
    else:
        X_poly = X
        feature_names = [f"feature_{i}" for i in range(X.shape[1])]
    
    # Add constant for statsmodels if not using Ridge
    if not use_ridge:
        X_sm = sm.add_constant(X_poly)
    else:
        X_sm = X_poly
    
    if use_ridge:
        model = Ridge(alpha=ridge_alpha)
        model.fit(X_poly, y)
        y_pred = model.predict(X_poly)
        r2 = r2_score(y, y_pred)
        coefficients = dict(zip(feature_names, model.coef_))
        # Ridge doesn't provide p-values directly, so we set them to None
        p_values = {name: None for name in feature_names}
        intercept = model.intercept_
        logger.info(f"Ridge regression used with alpha={ridge_alpha}")
    else:
        model = sm.OLS(y, X_sm).fit()
        y_pred = model.predict(X_sm)
        r2 = model.rsquared
        coefficients = dict(zip(feature_names, model.params[1:]))  # Skip intercept
        p_values = {name: float(p) for name, p in zip(feature_names, model.pvalues[1:])}
        intercept = float(model.params[0])
    
    return {
        "model_type": "Ridge" if use_ridge else "OLS",
        "coefficients": coefficients,
        "intercept": intercept,
        "r_squared": float(r2),
        "p_values": p_values,
        "feature_names": feature_names
    }

def calculate_anova_table(
    X: np.ndarray, 
    y: np.ndarray, 
    model_type: str = "OLS"
) -> pd.DataFrame:
    """
    Calculate ANOVA table for the regression model.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        model_type: Type of model ("OLS" or "Ridge")
        
    Returns:
        pandas DataFrame containing ANOVA table
    """
    if model_type != "OLS":
        logger.warning("ANOVA table is primarily meaningful for OLS models. Results for Ridge may be approximate.")
    
    # Add constant
    X_sm = sm.add_constant(X)
    model = sm.OLS(y, X_sm).fit()
    
    # Get ANOVA table
    anova = sm.stats.anova_lm(model, typ=2)
    
    # Reset index to make 'term' a column
    anova = anova.reset_index()
    anova.columns = ['term', 'df', 'sum_sq', 'mean_sq', 'F', 'PR(>F)']
    
    return anova

def run_cross_validation(
    X: np.ndarray, 
    y: np.ndarray, 
    n_splits: int = 10,
    use_ridge: bool = False,
    ridge_alpha: float = 1.0,
    random_state: int = 42
) -> Dict[str, float]:
    """
    Run cross-validation and return mean R² and standard deviation.
    
    For N < 50, uses Leave-One-Out (n_splits = n_samples).
    For N >= 50, uses k-fold (default n_splits = 10).
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        n_splits: Number of folds (will be overridden for LOOCV if n_samples < 50)
        use_ridge: If True, use Ridge regression
        ridge_alpha: Regularization strength for Ridge
        random_state: Random seed for reproducibility
        
    Returns:
        Dictionary with 'mean_r2' and 'std_r2'
    """
    n_samples = X.shape[0]
    
    # Determine CV strategy based on sample size (FR-005)
    if n_samples < 50:
        actual_n_splits = n_samples
        logger.info(f"Small dataset (N={n_samples}). Using Leave-One-Out Cross-Validation.")
    else:
        actual_n_splits = max(5, min(n_splits, n_samples))
        logger.info(f"Using {actual_n_splits}-fold Cross-Validation.")
    
    # Choose estimator
    if use_ridge:
        from sklearn.linear_model import Ridge
        estimator = Ridge(alpha=ridge_alpha, random_state=random_state)
    else:
        from sklearn.linear_model import LinearRegression
        estimator = LinearRegression()
    
    # Run cross-validation
    scores = cross_val_score(
        estimator, 
        X, 
        y, 
        cv=actual_n_splits, 
        scoring='r2',
        n_jobs=-1
    )
    
    mean_r2 = float(np.mean(scores))
    std_r2 = float(np.std(scores))
    
    logger.info(f"Cross-validation R²: mean={mean_r2:.4f}, std={std_r2:.4f}")
    
    return {
        "mean_r2": mean_r2,
        "std_r2": std_r2,
        "n_splits": actual_n_splits,
        "strategy": "LOOCV" if n_samples < 50 else f"{actual_n_splits}-fold CV"
    }

def filter_authorized_features(
    features: List[str], 
    authorized: Optional[List[str]] = None
) -> List[str]:
    """
    Filter features to only include authorized ones (per spec).
    
    By default, only degree, clustering, and path length are authorized.
    
    Args:
        features: List of all available feature names
        authorized: Optional list of authorized features (defaults to spec)
        
    Returns:
        List of authorized features present in the input
    """
    if authorized is None:
        # Default authorized features per spec
        authorized = ['degree', 'clustering', 'path_length']
    
    authorized_lower = [f.lower() for f in authorized]
    filtered = [f for f in features if f.lower() in authorized_lower]
    
    excluded = [f for f in features if f.lower() not in authorized_lower]
    if excluded:
        logger.warning(f"Excluding non-authorized features: {excluded}")
    
    return filtered

def prepare_regression_data(
    data: List[Dict[str, Any]], 
    target_key: str = 'threshold',
    feature_keys: Optional[List[str]] = None
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Prepare data for regression from a list of simulation results.
    
    Args:
        data: List of dictionaries containing network metrics and thresholds
        target_key: Key name for the target variable (default: 'threshold')
        feature_keys: Optional list of feature keys to use (defaults to all numeric keys except target)
        
    Returns:
        Tuple of (X, y, feature_names)
    """
    if not data:
        raise ValueError("Input data is empty")
    
    # Determine feature keys if not provided
    if feature_keys is None:
        # Get all keys from first record, exclude target and non-numeric
        sample = data[0]
        feature_keys = [
            k for k in sample.keys() 
            if k != target_key and isinstance(sample[k], (int, float, np.floating, np.integer))
        ]
    
    # Filter out any None values in feature_keys
    feature_keys = [k for k in feature_keys if k is not None]
    
    if not feature_keys:
        raise ValueError("No valid feature keys found")
    
    # Extract arrays
    X = []
    y = []
    
    for record in data:
        if target_key not in record:
            logger.warning(f"Missing target key '{target_key}' in record, skipping.")
            continue
        
        row = []
        valid = True
        for key in feature_keys:
            val = record.get(key)
            if val is None or (isinstance(val, float) and np.isnan(val)):
                logger.warning(f"Missing or NaN value for '{key}' in record, skipping.")
                valid = False
                break
            row.append(float(val))
        
        if valid:
            X.append(row)
            y.append(float(record[target_key]))
    
    if len(X) == 0:
        raise ValueError("No valid records found after filtering")
    
    return np.array(X), np.array(y), feature_keys
"""
Statistical utilities for the plant disease resistance pipeline.

Provides Benjamini-Hochberg correction for multiple testing and
Variance Inflation Factor (VIF) calculation for multicollinearity detection.
"""
import numpy as np
import pandas as pd
from typing import List, Union, Optional
from scipy import stats as scipy_stats

# Import logger from existing module
from utils.logging import get_logger

logger = get_logger(__name__)


def benjamini_hochberg(
    p_values: Union[List[float], np.ndarray, pd.Series],
    alpha: float = 0.05,
    method: str = "indep"
) -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg correction to a list of p-values.
    
    Args:
        p_values: List or array of raw p-values.
        alpha: Significance level (default 0.05).
        method: "indep" for independent tests, "poscorr" for positive dependence.
    
    Returns:
        DataFrame with columns:
            - 'raw_p': Original p-value
            - 'bh_p': BH-adjusted p-value
            - 'is_significant': Boolean indicating if adjusted p < alpha
            - 'rank': Rank of the p-value (1-based)
    
    Raises:
        ValueError: If p-values are not in [0, 1] or empty.
    """
    if not isinstance(p_values, (list, np.ndarray, pd.Series)):
        raise TypeError("p_values must be a list, numpy array, or pandas Series")
    
    p_array = np.asarray(p_values, dtype=float)
    
    if p_array.size == 0:
        raise ValueError("p_values cannot be empty")
    
    if np.any((p_array < 0) | (p_array > 1)):
        raise ValueError("All p-values must be between 0 and 1")
    
    n = len(p_array)
    sorted_indices = np.argsort(p_array)
    sorted_p = p_array[sorted_indices]
    
    # Calculate BH adjusted p-values
    ranks = np.arange(1, n + 1)
    
    if method == "indep":
        # Standard BH for independent tests
        bh_p = sorted_p * n / ranks
    elif method == "poscorr":
        # Benjamini-Yekutieli for positive dependence
        c_n = np.sum(1.0 / np.arange(1, n + 1))
        bh_p = sorted_p * n / (ranks * c_n)
    else:
        raise ValueError("method must be 'indep' or 'poscorr'")
    
    # Ensure monotonicity (cumulative min from the end)
    bh_p = np.minimum.accumulate(bh_p[::-1])[::-1]
    bh_p = np.minimum(bh_p, 1.0)  # Cap at 1.0
    
    # Restore original order
    result_df = pd.DataFrame({
        'raw_p': p_array,
        'bh_p': np.empty(n),
        'is_significant': np.empty(n, dtype=bool),
        'rank': np.empty(n, dtype=int)
    })
    
    result_df.loc[sorted_indices, 'bh_p'] = bh_p
    result_df.loc[sorted_indices, 'is_significant'] = bh_p < alpha
    result_df.loc[sorted_indices, 'rank'] = ranks
    
    logger.debug(f"Applied BH correction to {n} p-values. "
                 f"Significant at alpha={alpha}: {np.sum(result_df['is_significant'])}")
    
    return result_df


def calculate_vif(
    features: Union[pd.DataFrame, np.ndarray],
    feature_names: Optional[List[str]] = None,
    threshold: float = 5.0
) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    
    VIF measures multicollinearity. A VIF > 5 or 10 indicates high multicollinearity.
    
    Args:
        features: DataFrame or array of features (samples x features).
        feature_names: Optional list of feature names. If None, uses column names 
                       if DataFrame, else generates generic names.
        threshold: Threshold above which to flag high multicollinearity (default 5.0).
    
    Returns:
        DataFrame with columns:
            - 'feature': Feature name
            - 'vif': VIF value
            - 'high_multicollinearity': Boolean indicating if VIF > threshold
    
    Raises:
        ValueError: If features are constant or singular matrix encountered.
        TypeError: If input cannot be converted to a valid feature matrix.
    """
    if isinstance(features, pd.DataFrame):
        X = features.values
        if feature_names is None:
            feature_names = list(features.columns)
    elif isinstance(features, np.ndarray):
        X = features
        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(X.shape[1])]
    else:
        raise TypeError("features must be a pandas DataFrame or numpy array")
    
    if X.shape[0] < X.shape[1]:
        logger.warning(f"Number of samples ({X.shape[0]}) is less than number of features ({X.shape[1]}). "
                       "VIF calculation may be unstable.")
    
    # Check for constant features (zero variance)
    variances = np.var(X, axis=0)
    if np.any(variances == 0):
        zero_var_features = [feature_names[i] for i, v in enumerate(variances) if v == 0]
        raise ValueError(f"Constant features detected (zero variance): {zero_var_features}. "
                         "Remove these before calculating VIF.")
    
    vif_results = []
    
    # Add intercept for regression
    X_with_intercept = np.column_stack([np.ones(X.shape[0]), X])
    
    for i in range(X.shape[1]):
        # Regress feature i against all other features
        y = X[:, i]
        # Other features (excluding feature i)
        X_other = np.delete(X_with_intercept, i + 1, axis=1)  # +1 because of intercept
        
        try:
            # Fit linear regression: y = X_other * beta + error
            # Using least squares
            beta, residuals, rank, s = np.linalg.lstsq(X_other, y, rcond=None)
            
            # Calculate R-squared
            y_pred = X_other @ beta
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            
            if ss_tot == 0:
                # Constant y (should have been caught above, but safety check)
                r_squared = 0.0
            else:
                r_squared = 1.0 - (ss_res / ss_tot)
            
            # VIF = 1 / (1 - R^2)
            if r_squared >= 1.0:
                # Perfect multicollinearity
                vif = np.inf
            else:
                vif = 1.0 / (1.0 - r_squared)
            
        except np.linalg.LinAlgError:
            logger.warning(f"Singular matrix encountered for feature {feature_names[i]}. "
                           "Setting VIF to infinity.")
            vif = np.inf
        
        vif_results.append({
            'feature': feature_names[i],
            'vif': vif,
            'high_multicollinearity': vif > threshold
        })
    
    result_df = pd.DataFrame(vif_results)
    result_df = result_df.sort_values('vif', ascending=False)
    
    high_vif_count = result_df['high_multicollinearity'].sum()
    if high_vif_count > 0:
        logger.warning(f"Found {high_vif_count} features with VIF > {threshold}: "
                       f"{result_df.loc[result_df['high_multicollinearity'], 'feature'].tolist()}")
    
    return result_df


def filter_high_vif_features(
    features: pd.DataFrame,
    vif_threshold: float = 5.0,
    remove_method: str = "iterative"
) -> pd.DataFrame:
    """
    Iteratively remove features with high VIF until all remaining features are below threshold.
    
    Args:
        features: DataFrame of features.
        vif_threshold: VIF threshold for removal (default 5.0).
        remove_method: Currently only "iterative" is supported.
    
    Returns:
        DataFrame containing only features with VIF <= threshold.
    """
    if remove_method != "iterative":
        raise ValueError("Only 'iterative' removal method is supported.")
    
    current_features = features.copy()
    removed_features = []
    
    while True:
        vif_df = calculate_vif(current_features, threshold=vif_threshold)
        high_vif = vif_df[vif_df['high_multicollinearity']]
        
        if high_vif.empty:
            break
        
        # Remove the feature with the highest VIF
        worst_feature = high_vif.iloc[0]['feature']
        logger.info(f"Removing feature '{worst_feature}' with VIF={high_vif.iloc[0]['vif']:.2f}")
        
        current_features = current_features.drop(columns=[worst_feature])
        removed_features.append(worst_feature)
        
        if current_features.shape[1] == 0:
            logger.error("All features removed due to high multicollinearity.")
            break
    
    if removed_features:
        logger.info(f"Removed {len(removed_features)} features due to high VIF: {removed_features}")
    
    return current_features
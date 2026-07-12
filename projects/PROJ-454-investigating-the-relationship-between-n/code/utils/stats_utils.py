"""
Statistical utilities for the llmXive project.
Implements Multiple Linear Regression (OLS) and FDR correction (Benjamini-Hochberg).
"""
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant
from typing import Tuple, List, Dict, Optional, Union
import logging

logger = logging.getLogger(__name__)


def calculate_vif(df: pd.DataFrame, features: List[str]) -> pd.Series:
    """
    Calculate Variance Inflation Factor (VIF) for a set of features.

    Args:
        df: DataFrame containing the features.
        features: List of column names to calculate VIF for.

    Returns:
        A pandas Series with VIF values indexed by feature name.
    """
    if not features:
        return pd.Series(dtype=float)

    X = df[features].dropna()
    if X.empty:
        return pd.Series(dtype=float)

    # Add constant for intercept
    X_const = add_constant(X)
    
    vif_data = {}
    for i, col in enumerate(X_const.columns):
        if col == 'const':
            continue
        try:
            vif_data[col] = variance_inflation_factor(X_const.values, i)
        except np.linalg.LinAlgError:
            logger.warning(f"Singularity detected in VIF calculation for {col}, setting VIF to infinity.")
            vif_data[col] = np.inf

    return pd.Series(vif_data)


def check_multicollinearity(df: pd.DataFrame, features: List[str], threshold: float = 5.0) -> Tuple[bool, pd.Series]:
    """
    Check for multicollinearity using VIF.

    Args:
        df: DataFrame containing the features.
        features: List of column names to check.
        threshold: VIF threshold above which multicollinearity is considered high (default 5.0).

    Returns:
        Tuple of (has_high_vif: bool, vif_series: pd.Series).
    """
    vif_series = calculate_vif(df, features)
    if vif_series.empty:
        return False, vif_series
    
    has_high_vif = (vif_series > threshold).any()
    return has_high_vif, vif_series


def fit_ols_model(
    y: Union[pd.Series, np.ndarray], 
    X: Union[pd.DataFrame, np.ndarray], 
    feature_names: Optional[List[str]] = None
) -> Dict:
    """
    Fit an Ordinary Least Squares (OLS) regression model.

    Args:
        y: Dependent variable (target).
        X: Independent variables (features).
        feature_names: Optional list of feature names for the model.

    Returns:
        Dictionary containing model results:
            - 'params': Model coefficients
            - 'pvalues': P-values for coefficients
            - 'rsquared': R-squared value
            - 'rsquared_adj': Adjusted R-squared
            - 'f_pvalue': P-value for the F-statistic
            - 'model': The fitted OLS model object
    """
    if isinstance(y, np.ndarray):
        y = pd.Series(y)
    
    if isinstance(X, np.ndarray):
        if feature_names is None:
            feature_names = [f'feature_{i}' for i in range(X.shape[1])]
        X = pd.DataFrame(X, columns=feature_names)

    # Drop rows with NaN in either X or y
    combined = pd.concat([X, y], axis=1)
    combined = combined.dropna()
    
    if combined.empty:
        raise ValueError("No valid data remaining after dropping NaNs for OLS fitting.")

    X_clean = combined[X.columns]
    y_clean = combined[y.name if isinstance(y, pd.Series) else y]

    X_const = add_constant(X_clean)
    
    try:
        model = OLS(y_clean, X_const).fit()
    except np.linalg.LinAlgError as e:
        logger.error(f"OLS fitting failed due to singularity: {e}")
        raise

    return {
        'params': model.params,
        'pvalues': model.pvalues,
        'rsquared': model.rsquared,
        'rsquared_adj': model.rsquared_adj,
        'f_pvalue': model.f_pvalue,
        'model': model,
        'summary': model.summary()
    }


def fdr_benjamini_hochberg(p_values: np.ndarray, alpha: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
    """
    Perform Benjamini-Hochberg FDR correction on a set of p-values.

    Args:
        p_values: Array of p-values to correct.
        alpha: Significance level (default 0.05).

    Returns:
        Tuple of (reject: bool array, p_values_corrected: float array).
        'reject' indicates which hypotheses are rejected (significant).
    """
    p_values = np.asarray(p_values)
    n = len(p_values)
    if n == 0:
        return np.array([]), np.array([])

    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = p_values[sorted_indices]

    # Calculate critical values
    ranks = np.arange(1, n + 1)
    critical_values = (ranks / n) * alpha

    # Determine rejection
    # Find the largest k such that p_(k) <= (k/n) * alpha
    # We work backwards from the largest rank
    reject_sorted = np.zeros(n, dtype=bool)
    for i in range(n - 1, -1, -1):
        if sorted_p_values[i] <= critical_values[i]:
            reject_sorted[i:] = True
            break

    # Map back to original order
    reject = np.zeros(n, dtype=bool)
    reject[sorted_indices] = reject_sorted

    # Calculate adjusted p-values (q-values)
    # q_i = min( (n/k) * p_k, q_{i+1} ) for k >= i
    adjusted_p = np.zeros(n)
    current_min = 1.0
    for i in range(n - 1, -1, -1):
        val = (n / (i + 1)) * sorted_p_values[i]
        current_min = min(current_min, val)
        adjusted_p[sorted_indices[i]] = current_min

    # Ensure adjusted p-values do not exceed 1.0
    adjusted_p = np.minimum(adjusted_p, 1.0)

    return reject, adjusted_p


def bonferroni_correction(p_values: np.ndarray, alpha: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
    """
    Perform Bonferroni correction on a set of p-values.
    Note: This is retained for historical tracking as per project plan, 
    but FDR is the primary method.

    Args:
        p_values: Array of p-values to correct.
        alpha: Significance level (default 0.05).

    Returns:
        Tuple of (reject: bool array, p_values_corrected: float array).
    """
    p_values = np.asarray(p_values)
    n = len(p_values)
    if n == 0:
        return np.array([]), np.array([])

    corrected_p = np.minimum(p_values * n, 1.0)
    reject = corrected_p < alpha

    return reject, corrected_p


def calculate_partial_r(results: Dict, feature_name: str) -> float:
    """
    Calculate partial correlation coefficient (r) from OLS results.
    
    Formula: r = sign(beta) * sqrt( t^2 / (t^2 + df_resid) )
    
    Args:
        results: Dictionary from fit_ols_model containing 'params', 'pvalues', 'model'.
        feature_name: Name of the feature to calculate partial r for.

    Returns:
        Partial correlation coefficient.
    """
    model = results['model']
    params = model.params
    tvalues = model.tvalues
    df_resid = model.df_resid

    if feature_name not in params.index:
        raise ValueError(f"Feature '{feature_name}' not found in model results.")

    t_stat = tvalues[feature_name]
    beta = params[feature_name]
    
    # Avoid division by zero or negative under sqrt due to precision issues
    term = (t_stat ** 2) / (t_stat ** 2 + df_resid)
    if term < 0:
        term = 0
        
    r = np.sign(beta) * np.sqrt(term)
    return r


def classify_effect_size(r: float) -> str:
    """
    Classify effect size based on partial r.
    Threshold: >= 0.3 is considered clinically meaningful.
    
    Args:
        r: Partial correlation coefficient.

    Returns:
        String classification: 'negligible', 'small', 'medium', 'large', or 'clinically_meaningful'.
    """
    abs_r = abs(r)
    if abs_r < 0.1:
        return "negligible"
    elif abs_r < 0.3:
        return "small"
    elif abs_r < 0.5:
        return "medium"
    else:
        return "large"
    
    # Specific check for clinical meaningfulness as per spec
    if abs_r >= 0.3:
        return "clinically_meaningful"
    return "not_clinically_meaningful"


def run_regression_with_fdr(
    df: pd.DataFrame,
    target_col: str,
    feature_cols: List[str],
    fdr_alpha: float = 0.05
) -> Dict:
    """
    Run a full regression analysis with FDR correction as per project plan.
    
    Steps:
    1. Fit OLS model.
    2. Calculate VIFs.
    3. If any VIF > 5, log warning (handling of dropping features is done externally).
    4. Apply Benjamini-Hochberg FDR correction to p-values.
    5. Calculate partial r and effect sizes.

    Args:
        df: DataFrame with target and features.
        target_col: Name of the target column.
        feature_cols: List of feature column names.
        fdr_alpha: Alpha level for FDR correction.

    Returns:
        Dictionary with:
            - 'ols_results': Output from fit_ols_model
            - 'vif_results': VIF series
            - 'fdr_results': Tuple (reject, adjusted_p)
            - 'effect_sizes': Dict of feature -> partial r and classification
    """
    # Prepare data
    X = df[feature_cols]
    y = df[target_col]
    
    # Fit OLS
    ols_res = fit_ols_model(y, X, feature_names=feature_cols)
    
    # Check VIF
    vif_res, vif_series = check_multicollinearity(df, feature_cols, threshold=5.0)
    
    # FDR Correction
    p_vals = ols_res['pvalues'].drop('const').values
    fdr_reject, fdr_adj_p = fdr_benjamini_hochberg(p_vals, alpha=fdr_alpha)
    
    # Map back to feature names
    features_no_const = [f for f in feature_cols if f in ols_res['pvalues'].index]
    # Ensure alignment
    if len(features_no_const) != len(p_vals):
        # Fallback to index alignment
        features_no_const = list(ols_res['pvalues'].drop('const').index)
        p_vals = ols_res['pvalues'].drop('const').values
        fdr_reject, fdr_adj_p = fdr_benjamini_hochberg(p_vals, alpha=fdr_alpha)

    fdr_dict = {
        'rejected': dict(zip(features_no_const, fdr_reject)),
        'adjusted_pvalues': dict(zip(features_no_const, fdr_adj_p))
    }
    
    # Effect Sizes
    effect_sizes = {}
    for feat in features_no_const:
        r_val = calculate_partial_r(ols_res, feat)
        classification = classify_effect_size(r_val)
        effect_sizes[feat] = {
            'partial_r': r_val,
            'classification': classification
        }

    return {
        'ols_results': ols_res,
        'vif_results': vif_series,
        'fdr_results': fdr_dict,
        'effect_sizes': effect_sizes
    }
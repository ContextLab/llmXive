"""
Analysis module for Gut Microbiome-Sleep Architecture Correlation Study.

Implements correlation method selection, ZINB modeling, and statistical tests.
Ensures reproducibility via explicit seed pinning per Constitution Principle I.
"""
import os
import random
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import shapiro
import statsmodels.api as sm
from statsmodels.discrete.discrete_model import ZeroInflatedNegativeBinomialP
from statsmodels.stats.multitest import multipletests

# Explicitly pin random seeds for reproducibility
# This satisfies Constitution Principle I
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
os.environ['PYTHONHASHSEED'] = str(SEED)

# Statsmodels specific seed pinning if applicable
# Note: Some statsmodels estimators use internal random states
# We ensure global numpy seed is set before any random operations

def set_analysis_seed(seed: int = SEED) -> None:
    """
    Re-pins all random seeds for the analysis module.
    Useful for ensuring reproducibility across multiple runs or sub-processes.
    
    Args:
        seed: Integer seed value (default: 42)
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def check_zero_inflation(series: pd.Series, threshold: float = 0.3) -> bool:
    """
    Check if a series has excessive zeros (> threshold proportion).
    
    Args:
        series: Input pandas Series
        threshold: Proportion threshold for zero-inflation (default: 0.3)
        
    Returns:
        bool: True if zero-inflated, False otherwise
    """
    zero_count = (series == 0).sum()
    zero_proportion = zero_count / len(series)
    return zero_proportion > threshold

def check_normality(series: pd.Series, alpha: float = 0.05) -> bool:
    """
    Perform Shapiro-Wilk test for normality.
    
    Args:
        series: Input pandas Series
        alpha: Significance level (default: 0.05)
        
    Returns:
        bool: True if normally distributed (p >= alpha), False otherwise
    """
    if len(series) < 3:
        return False  # Cannot perform test
    
    try:
        _, p_value = shapiro(series.dropna())
        return p_value >= alpha
    except Exception:
        return False

def detect_compositionality(df: pd.DataFrame, taxa_columns: list) -> bool:
    """
    Detect if data exhibits compositional properties.
    
    Compositional data sums to a constant (e.g., relative abundances sum to 1 or 100).
    
    Args:
        df: Input DataFrame
        taxa_columns: List of column names representing taxa
        
    Returns:
        bool: True if compositional, False otherwise
    """
    if not taxa_columns:
        return False
    
    # Check if sums are constant across rows
    row_sums = df[taxa_columns].sum(axis=1)
    unique_sums = row_sums.nunique()
    
    # If all rows sum to the same value (within floating point tolerance), it's compositional
    return unique_sums == 1 or row_sums.std() / row_sums.mean() < 1e-6

def select_correlation_method(
    df: pd.DataFrame,
    predictor_cols: list,
    outcome_cols: list,
    zero_threshold: float = 0.3,
    normality_alpha: float = 0.05
) -> dict:
    """
    Select appropriate correlation method based on data characteristics.
    
    Decision Logic:
    1. If compositionality detected -> SparCC/SpiecEasi (placeholder for now)
    2. Else if zeros > threshold OR Shapiro-Wilk p < alpha -> ZINB/Hurdle
    3. Else if non-normal -> Spearman
    4. Else -> Pearson
    
    Args:
        df: Input DataFrame
        predictor_cols: List of predictor (taxa) column names
        outcome_cols: List of outcome (sleep) column names
        zero_threshold: Zero-inflation threshold (default: 0.3)
        normality_alpha: Normality test significance level (default: 0.05)
        
    Returns:
        dict: Method selection results with details
    """
    results = {
        'method': None,
        'reason': None,
        'details': {}
    }
    
    # Check for compositionality
    is_compositional = detect_compositionality(df, predictor_cols)
    
    if is_compositional:
        results['method'] = 'sparcc'
        results['reason'] = 'Compositionality detected in taxa data'
        results['details']['is_compositional'] = True
        return results
    
    # Check zero-inflation and normality for each predictor-outcome pair
    # For simplicity, we check overall data characteristics
    all_predictors = df[predictor_cols]
    all_outcomes = df[outcome_cols]
    
    # Check zero inflation across all predictors
    zero_flags = [check_zero_inflation(all_predictors[col], zero_threshold) for col in predictor_cols]
    is_zero_inflated = any(zero_flags)
    
    # Check normality for outcomes
    normality_flags = [check_normality(all_outcomes[col], normality_alpha) for col in outcome_cols]
    is_non_normal = not all(normality_flags)
    
    if is_zero_inflated:
        results['method'] = 'zinb'
        results['reason'] = 'Zero-inflation detected in taxa data'
        results['details']['is_zero_inflated'] = True
        results['details']['zero_flags'] = dict(zip(predictor_cols, zero_flags))
        return results
    
    if is_non_normal:
        results['method'] = 'spearman'
        results['reason'] = 'Non-normal distribution detected in outcomes'
        results['details']['is_non_normal'] = True
        results['details']['normality_flags'] = dict(zip(outcome_cols, normality_flags))
        return results
    
    results['method'] = 'pearson'
    results['reason'] = 'Data meets assumptions for Pearson correlation'
    results['details']['is_zero_inflated'] = False
    results['details']['is_non_normal'] = False
    
    return results

def fit_zinb_model(
    predictors: pd.DataFrame,
    outcome: pd.Series,
    formula: str = None
) -> dict:
    """
    Fit Zero-Inflated Negative Binomial model.
    
    Args:
        predictors: DataFrame of predictor variables
        outcome: Series of outcome variable
        formula: Optional formula string for model specification
        
    Returns:
        dict: Model results including coefficients and p-values
    """
    # Ensure reproducibility by setting seed before fitting
    set_analysis_seed(SEED)
    
    # Prepare data
    X = predictors.values
    y = outcome.values
    
    # Add constant for intercept
    X_with_const = sm.add_constant(X)
    
    try:
        # Fit ZINB model
        # Note: statsmodels ZINB requires specific initialization
        model = ZeroInflatedNegativeBinomialP(
            endog=y,
            exog=X_with_const,
            exog_infl=X_with_const,  # Same predictors for inflation part
            method='bfgs'
        )
        
        result = model.fit(disp=False)
        
        return {
            'success': True,
            'coefficients': result.params,
            'pvalues': result.pvalues,
            'log_likelihood': result.llf,
            'aic': result.aic,
            'bic': result.bic
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def calculate_pearson_correlation(
    x: pd.Series,
    y: pd.Series
) -> dict:
    """
    Calculate Pearson correlation coefficient.
    
    Args:
        x: First variable
        y: Second variable
        
    Returns:
        dict: Correlation coefficient, p-value, and sample size
    """
    # Remove NaN values
    mask = ~(x.isna() | y.isna())
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 3:
        return {
            'correlation': None,
            'p_value': None,
            'n': len(x_clean),
            'success': False
        }
    
    try:
        corr, p_value = stats.pearsonr(x_clean, y_clean)
        return {
            'correlation': corr,
            'p_value': p_value,
            'n': len(x_clean),
            'success': True
        }
    except Exception as e:
        return {
            'correlation': None,
            'p_value': None,
            'n': len(x_clean),
            'success': False,
            'error': str(e)
        }

def calculate_spearman_correlation(
    x: pd.Series,
    y: pd.Series
) -> dict:
    """
    Calculate Spearman rank correlation coefficient.
    
    Args:
        x: First variable
        y: Second variable
        
    Returns:
        dict: Correlation coefficient, p-value, and sample size
    """
    # Remove NaN values
    mask = ~(x.isna() | y.isna())
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 3:
        return {
            'correlation': None,
            'p_value': None,
            'n': len(x_clean),
            'success': False
        }
    
    try:
        corr, p_value = stats.spearmanr(x_clean, y_clean)
        return {
            'correlation': corr,
            'p_value': p_value,
            'n': len(x_clean),
            'success': True
        }
    except Exception as e:
        return {
            'correlation': None,
            'p_value': None,
            'n': len(x_clean),
            'success': False,
            'error': str(e)
        }

def apply_fdr_correction(
    p_values: list,
    alpha: float = 0.05,
    method: str = 'fdr_bh'
) -> dict:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.
    
    Args:
        p_values: List of raw p-values
        alpha: Significance level (default: 0.05)
        method: FDR correction method (default: 'fdr_bh')
        
    Returns:
        dict: Corrected p-values, rejection decisions, and summary statistics
    """
    if not p_values:
        return {
            'corrected_p_values': [],
            'rejections': [],
            'summary': {
                'total_tests': 0,
                'significant': 0,
                'not_significant': 0
            }
        }
    
    try:
        # Apply FDR correction
        corrected_p, reject, _, _ = multipletests(p_values, alpha=alpha, method=method)
        
        return {
            'corrected_p_values': corrected_p.tolist(),
            'rejections': reject.tolist(),
            'summary': {
                'total_tests': len(p_values),
                'significant': int(reject.sum()),
                'not_significant': int((~reject).sum())
            }
        }
    except Exception as e:
        return {
            'corrected_p_values': [],
            'rejections': [],
            'summary': {
                'total_tests': len(p_values),
                'significant': 0,
                'not_significant': 0
            },
            'error': str(e)
        }

def run_correlation_analysis(
    df: pd.DataFrame,
    predictor_cols: list,
    outcome_cols: list,
    method: str = None
) -> list:
    """
    Run correlation analysis between predictors and outcomes.
    
    Args:
        df: Input DataFrame
        predictor_cols: List of predictor column names
        outcome_cols: List of outcome column names
        method: Correlation method ('pearson', 'spearman', 'zinb')
        
    Returns:
        list: List of correlation results for each predictor-outcome pair
    """
    results = []
    
    # If method not specified, select automatically
    if method is None:
        selection = select_correlation_method(df, predictor_cols, outcome_cols)
        method = selection['method']
    
    for pred_col in predictor_cols:
        for outcome_col in outcome_cols:
            if method == 'pearson':
                result = calculate_pearson_correlation(df[pred_col], df[outcome_col])
            elif method == 'spearman':
                result = calculate_spearman_correlation(df[pred_col], df[outcome_col])
            elif method == 'zinb':
                # For ZINB, we need to fit a model
                predictors = df[[pred_col]]
                outcome = df[outcome_col]
                model_result = fit_zinb_model(predictors, outcome)
                result = {
                    'method': 'zinb',
                    'success': model_result['success'],
                    'coefficient': model_result.get('coefficients', {}).get('const', None) if model_result['success'] else None,
                    'p_value': model_result.get('pvalues', {}).get('const', None) if model_result['success'] else None
                }
            else:
                result = {'success': False, 'error': f'Unknown method: {method}'}
            
            result['predictor'] = pred_col
            result['outcome'] = outcome_col
            results.append(result)
    
    return results
import pandas as pd
import numpy as np
import logging
from typing import Tuple, Dict, Any, Optional, Literal
from scipy import stats
import statsmodels.api as sm

from validity import check_construct_validity
from exceptions import MathematicalCouplingError

logger = logging.getLogger(__name__)

def calculate_correlation(
    df: pd.DataFrame,
    var1: str,
    var2: str,
    method: Literal['pearson', 'spearman'] = 'pearson'
) -> Tuple[float, float]:
    """
    Calculate correlation coefficient and p-value between two variables.

    Args:
        df: DataFrame containing the variables
        var1: Name of first variable
        var2: Name of second variable
        method: 'pearson' or 'spearman'

    Returns:
        Tuple of (correlation coefficient, p-value)
    """
    if var1 not in df.columns or var2 not in df.columns:
        raise ValueError(f"Variables {var1} or {var2} not found in DataFrame")

    # Drop rows with missing values in either variable
    subset = df[[var1, var2]].dropna()
    
    if len(subset) < 2:
        raise ValueError("Insufficient data to calculate correlation")

    corr, p_value = stats.pearsonr(subset[var1], subset[var2]) if method == 'pearson' else stats.spearmanr(subset[var1], subset[var2])
    
    logger.info(f"Correlation ({method}) between {var1} and {var2}: r={corr:.4f}, p={p_value:.4f}")
    return corr, p_value

def run_initial_correlations(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run initial correlations between key variables.

    Args:
        df: Cleaned DataFrame

    Returns:
        Dictionary of correlation results
    """
    results = {}
    predictor = 'news_exposure_freq'
    outcome = 'anxiety_score'
    
    # Correlation between predictor and outcome
    corr, p_val = calculate_correlation(df, predictor, outcome)
    results[f'{predictor}_vs_{outcome}'] = {
        'correlation': corr,
        'p_value': p_val,
        'method': 'pearson'
    }
    
    # Correlation with control variables
    for var in ['baseline_anxiety', 'age']:
        if var in df.columns:
            corr, p_val = calculate_correlation(df, predictor, var)
            results[f'{predictor}_vs_{var}'] = {
                'correlation': corr,
                'p_value': p_val,
                'method': 'pearson'
            }
            
    return results

def fit_regression_model(
    df: pd.DataFrame,
    formula: str = None,
    check_validity: bool = True
) -> Dict[str, Any]:
    """
    Fit a multiple linear regression model.

    Args:
        df: DataFrame containing the variables
        formula: Regression formula (default: anxiety_score ~ news_exposure_freq + baseline_anxiety + age + gender)
        check_validity: Whether to run construct validity check before fitting

    Returns:
        Dictionary containing model results and diagnostics
    """
    if formula is None:
        formula = 'anxiety_score ~ news_exposure_freq + baseline_anxiety + age + gender'
    
    # Check construct validity if requested
    if check_validity:
        try:
            check_construct_validity(df, 'anxiety_score', 'baseline_anxiety')
        except MathematicalCouplingError as e:
            logger.error(f"Construct validity check failed: {e}")
            raise
    
    logger.info(f"Fitting regression model with formula: {formula}")
    
    # Prepare data for statsmodels
    # Handle categorical variables if present (e.g., gender)
    if 'gender' in df.columns:
        df_model = df.copy()
        # Convert gender to numeric if it's categorical
        if df_model['gender'].dtype == 'object':
            df_model['gender'] = df_model['gender'].astype('category').cat.codes
            logger.info("Converted 'gender' to numeric codes for regression")
    else:
        df_model = df.copy()
    
    # Drop rows with any missing values in the variables used in the formula
    # Extract variable names from formula
    formula_vars = formula.replace('~', '').replace('+', ' ').split()
    formula_vars = [v.strip() for v in formula_vars if v.strip()]
    
    df_model = df_model.dropna(subset=formula_vars)
    
    if len(df_model) < 10:
        raise ValueError("Insufficient data after dropping NaNs for regression")
    
    # Fit model using statsmodels formula API
    model = sm.OLS.from_formula(formula, data=df_model)
    results = model.fit()
    
    logger.info(f"Regression model fitted on {len(df_model)} observations")
    logger.info(results.summary().as_text())
    
    # Extract coefficients and p-values
    coeffs = results.params.to_dict()
    p_values = results.pvalues.to_dict()
    
    # Calculate R-squared and adjusted R-squared
    r_squared = results.rsquared
    adj_r_squared = results.rsquared_adj
    
    # Check for multicollinearity (VIF)
    vif_data = {}
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    # Prepare design matrix (excluding intercept)
    X = results.model.exog
    # Add column names for VIF calculation
    # statsmodels adds an intercept column, we need to handle it
    col_names = results.model.data.param_names
    
    for i, col in enumerate(col_names):
        if col != 'Intercept':
            vif = variance_inflation_factor(X, i)
            vif_data[col] = vif
            logger.debug(f"VIF for {col}: {vif:.2f}")
    
    # Compile results
    model_results = {
        'formula': formula,
        'n_observations': len(df_model),
        'coefficients': coeffs,
        'p_values': p_values,
        'r_squared': r_squared,
        'adjusted_r_squared': adj_r_squared,
        'vif': vif_data,
        'f_statistic': results.fvalue,
        'f_p_value': results.f_pvalue
    }
    
    return model_results

def check_proxy_anxiety(df: pd.DataFrame, general_col: str = 'general_anxiety', anticipatory_col: str = 'anticipatory_anxiety') -> Dict[str, Any]:
    """
    Implement proxy flagging logic for general_anxiety vs anticipatory_anxiety (FR-008).
    
    This function checks if the dataset contains variables that could serve as proxies
    for the target construct (anticipatory anxiety). It flags whether:
    1. The direct measure (anticipatory_anxiety) is available
    2. A proxy measure (general_anxiety) is available
    3. The relationship between them suggests one can proxy the other
    
    Args:
        df: DataFrame containing anxiety variables
        general_col: Column name for general anxiety measure
        anticipatory_col: Column name for anticipatory anxiety measure
        
    Returns:
        Dictionary with proxy flagging results and recommendations
    """
    results = {
        'has_anticipatory': False,
        'has_general': False,
        'proxy_recommendation': None,
        'correlation_if_both': None,
        'notes': []
    }
    
    # Check availability
    has_anticipatory = anticipatory_col in df.columns
    has_general = general_col in df.columns
    
    results['has_anticipatory'] = has_anticipatory
    results['has_general'] = has_general
    
    if has_anticipatory:
        results['notes'].append(f"Direct measure '{anticipatory_col}' is available. Use this as primary outcome.")
        results['proxy_recommendation'] = 'direct'
    elif has_general:
        results['notes'].append(f"Direct measure '{anticipatory_col}' not found. Proxy measure '{general_col}' is available.")
        results['proxy_recommendation'] = 'proxy'
        
        # Calculate correlation if we have both to validate proxy potential
        if has_anticipatory and has_general:
            # Subset for correlation check
            subset = df[[general_col, anticipatory_col]].dropna()
            if len(subset) > 10:
                corr, p_val = stats.pearsonr(subset[general_col], subset[anticipatory_col])
                results['correlation_if_both'] = {
                    'correlation': corr,
                    'p_value': p_val
                }
                if corr > 0.7:
                    results['notes'].append(f"High correlation ({corr:.2f}) between general and anticipatory anxiety supports proxy usage.")
                else:
                    results['notes'].append(f"Moderate/low correlation ({corr:.2f}) between measures. Proxy usage may introduce measurement error.")
        else:
            results['notes'].append("Only proxy measure available; cannot validate proxy relationship.")
    else:
        results['notes'].append(f"Neither '{anticipatory_col}' nor '{general_col}' found in dataset.")
        results['proxy_recommendation'] = 'none'
        
    logger.info(f"Proxy check completed: {results['notes']}")
    return results

def run_full_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run the full analysis pipeline: correlations, regression, and proxy check.
    
    Args:
        df: Cleaned DataFrame
        
    Returns:
        Dictionary containing all analysis results
    """
    analysis_results = {
        'correlations': run_initial_correlations(df),
        'regression': fit_regression_model(df),
        'proxy_check': check_proxy_anxiety(df)
    }
    
    return analysis_results

def main():
    """Main entry point for model analysis."""
    from config import load_config, set_seed
    from clean import load_cleaned_data
    
    config = load_config()
    set_seed(config.get('random_seed', 42))
    
    # Load cleaned data
    df = load_cleaned_data(config)
    
    # Run analysis
    results = run_full_analysis(df)
    
    # Save results (to be handled by a separate task or script)
    import json
    output_path = config.get('output_dir', 'outputs')
    with open(f'{output_path}/model_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
        
    logger.info("Analysis complete. Results saved to outputs/model_results.json")

if __name__ == '__main__':
    main()
import pandas as pd
import numpy as np
import logging
from typing import Tuple, Dict, Any, Optional, Literal
from scipy import stats
import statsmodels.api as sm
from pathlib import Path
import json

from config import load_config
from exceptions import MathematicalCouplingError
from validity import check_construct_validity

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
        method: Correlation method ('pearson' or 'spearman')
        
    Returns:
        Tuple of (correlation coefficient, p-value)
    """
    if var1 not in df.columns or var2 not in df.columns:
        raise ValueError(f"Variables {var1} or {var2} not found in DataFrame")
    
    # Drop rows with missing values for these variables
    subset = df[[var1, var2]].dropna()
    
    if len(subset) < 2:
        raise ValueError("Insufficient data for correlation calculation")
    
    corr, p_value = stats.pearsonr(subset[var1], subset[var2]) if method == 'pearson' else stats.spearmanr(subset[var1], subset[var2])
    return float(corr), float(p_value)

def run_initial_correlations(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run initial correlations between main variables of interest.
    
    Args:
        df: Cleaned DataFrame
        
    Returns:
        Dictionary of correlation results
    """
    logger.info("Running initial correlations")
    
    results = {}
    main_vars = ['news_exposure_freq', 'anxiety_score', 'baseline_anxiety', 'age']
    
    for i, var1 in enumerate(main_vars):
        for var2 in main_vars[i+1:]:
            try:
                corr, p_val = calculate_correlation(df, var1, var2)
                results[f"{var1}_vs_{var2}"] = {
                    'correlation': corr,
                    'p_value': p_val,
                    'n': len(df[[var1, var2]].dropna())
                }
                logger.info(f"Correlation {var1} vs {var2}: r={corr:.3f}, p={p_val:.3f}")
            except Exception as e:
                logger.warning(f"Could not calculate correlation for {var1} vs {var2}: {e}")
    
    return results

def fit_regression_model(
    df: pd.DataFrame,
    formula: Optional[str] = None,
    dependent_var: str = 'anxiety_score',
    independent_vars: Optional[list] = None
) -> Dict[str, Any]:
    """
    Fit a multiple linear regression model.
    
    Args:
        df: DataFrame containing the variables
        formula: Optional statsmodels formula string
        dependent_var: Name of dependent variable (default: anxiety_score)
        independent_vars: List of independent variable names
        
    Returns:
        Dictionary containing model results and diagnostics
    """
    logger.info(f"Fitting regression model: {dependent_var} ~ {independent_vars}")
    
    if independent_vars is None:
        independent_vars = ['news_exposure_freq', 'baseline_anxiety', 'age']
    
    # Check for NaN values and drop rows
    vars_to_check = [dependent_var] + independent_vars
    df_clean = df[vars_to_check].dropna()
    
    if len(df_clean) < 30:
        from exceptions import PowerLimitationError
        raise PowerLimitationError(f"Sample size {len(df_clean)} is below minimum threshold of 30 for regression analysis.")
    
    X = df_clean[independent_vars]
    y = df_clean[dependent_var]
    
    # Add constant for intercept
    X_with_const = sm.add_constant(X)
    
    # Fit model
    model = sm.OLS(y, X_with_const).fit()
    
    results = {
        'formula': f"{dependent_var} ~ {' + '.join(independent_vars)}",
        'n_obs': len(df_clean),
        'r_squared': float(model.rsquared),
        'adj_r_squared': float(model.rsquared_adj),
        'f_statistic': float(model.fvalue),
        'f_pvalue': float(model.f_pvalue),
        'coefficients': {},
        'assumption_checks': {}
    }
    
    for name, param in model.params.items():
        results['coefficients'][name] = {
            'coef': float(param),
            'std_err': float(model.bse[name]),
            't_stat': float(model.tvalues[name]),
            'p_value': float(model.pvalues[name]),
            'conf_int_lower': float(model.conf_int().loc[name, 0]),
            'conf_int_upper': float(model.conf_int().loc[name, 1])
        }
    
    logger.info(f"Regression completed. R²={model.rsquared:.3f}, F-stat={model.fvalue:.3f}, p={model.f_pvalue:.3f}")
    return results

def check_proxy_anxiety(df: pd.DataFrame, anxiety_col: str = 'anxiety_score') -> Dict[str, Any]:
    """
    Implement proxy flagging logic for general_anxiety vs anticipatory_anxiety (FR-008).
    
    This function analyzes the `anxiety_score` variable to determine if it likely
    represents a proxy for general anxiety rather than the specific construct of
    anticipatory anxiety (the target outcome).
    
    Logic:
    1. Checks if the column name suggests a proxy (contains 'general').
    2. If the column name is ambiguous, it checks the correlation with 'baseline_anxiety'.
       - High correlation (> 0.7) suggests the variable is a general measure of anxiety
         rather than a specific anticipatory measure.
    3. Returns a flag and explanation.
    
    Args:
        df: DataFrame containing the anxiety variable
        anxiety_col: Name of the anxiety variable column
        
    Returns:
        Dictionary with 'is_proxy' (bool), 'confidence' (float), and 'reasoning' (str)
    """
    logger.info(f"Checking proxy status for anxiety variable: {anxiety_col}")
    
    result = {
        'is_proxy': False,
        'confidence': 0.0,
        'reasoning': '',
        'variable_name': anxiety_col
    }
    
    # Heuristic 1: Column name analysis
    name_lower = anxiety_col.lower()
    if 'general' in name_lower:
        result['is_proxy'] = True
        result['confidence'] = 0.95
        result['reasoning'] = "Variable name contains 'general', suggesting it measures general anxiety rather than anticipatory anxiety."
        logger.warning(f"Proxy detected: '{anxiety_col}' appears to be a general anxiety measure.")
        return result
    
    # Heuristic 2: Correlation with baseline (if baseline exists)
    if 'baseline_anxiety' in df.columns:
        # Calculate correlation
        subset = df[[anxiety_col, 'baseline_anxiety']].dropna()
        if len(subset) > 2:
            try:
                corr, _ = stats.pearsonr(subset[anxiety_col], subset['baseline_anxiety'])
                # If correlation is extremely high, it suggests the measure is redundant
                # with baseline/general state, rather than capturing the specific anticipatory component.
                if corr > 0.7:
                    result['is_proxy'] = True
                    result['confidence'] = min(0.85, abs(corr))
                    result['reasoning'] = f"High correlation ({corr:.3f}) with baseline_anxiety suggests '{anxiety_col}' may be a general anxiety proxy rather than a specific anticipatory measure."
                    logger.warning(f"Proxy detected: '{anxiety_col}' correlates {corr:.3f} with baseline_anxiety.")
                    return result
            except Exception as e:
                logger.warning(f"Could not compute correlation for proxy check: {e}")
    
    result['is_proxy'] = False
    result['confidence'] = 0.0
    result['reasoning'] = "No strong evidence found that this variable is a proxy for general anxiety. Proceeding with caution."
    logger.info("Proxy check passed: No clear evidence of general anxiety proxy.")
    return result

def check_assumptions(model_results: Dict[str, Any], df: pd.DataFrame, formula: str) -> Dict[str, Any]:
    """
    Check regression assumptions: Linearity, Homoscedasticity, Normality, VIF.
    
    Args:
        model_results: Results from fit_regression_model
        df: Original DataFrame used for fitting
        formula: Model formula string
        
    Returns:
        Dictionary of assumption check results
    """
    logger.info("Checking regression assumptions")
    
    assumptions = {
        'linearity': {'passed': True, 'details': 'Visual inspection recommended'},
        'homoscedasticity': {'passed': True, 'details': ''},
        'normality': {'passed': True, 'details': ''},
        'multicollinearity': {'passed': True, 'details': ''}
    }
    
    # 1. Homoscedasticity: Breusch-Pagan test
    # We need residuals and fitted values. Re-fit to get them if not stored, 
    # or extract from model_results if we stored the fitted model object (we didn't, so re-calc).
    # For simplicity, we'll re-calculate residuals here based on the formula.
    # In a real pipeline, we might pass the fitted model object instead of dict.
    
    # Parse formula to get vars (simple parsing)
    # Expected format: "anxiety_score ~ news_exposure_freq + baseline_anxiety + age"
    parts = formula.split('~')
    if len(parts) == 2:
        dep_var = parts[0].strip()
        indep_vars = [v.strip() for v in parts[1].split('+')]
        
        X = df[indep_vars].dropna()
        y = df[dep_var].loc[X.index]
        X = sm.add_constant(X)
        model = sm.OLS(y, X).fit()
        residuals = model.resid
        fitted = model.fittedvalues
        
        # Breusch-Pagan test
        try:
            from statsmodels.stats.diagnostic import het_breuschpagan
            bp_test = het_breuschpagan(residuals, model.model.exog)
            # bp_test[1] is p-value
            if bp_test[1] < 0.05:
                assumptions['homoscedasticity']['passed'] = False
                assumptions['homoscedasticity']['details'] = f"Breusch-Pagan test rejected homoscedasticity (p={bp_test[1]:.3f})"
                logger.warning(f"Homoscedasticity assumption failed: p={bp_test[1]:.3f}")
            else:
                assumptions['homoscedasticity']['details'] = f"Breusch-Pagan test passed (p={bp_test[1]:.3f})"
        except Exception as e:
            logger.warning(f"Could not perform Breusch-Pagan test: {e}")
        
        # 2. Normality: Shapiro-Wilk test on residuals
        try:
            shapiro_stat, shapiro_p = stats.shapiro(residuals)
            if shapiro_p < 0.05:
                assumptions['normality']['passed'] = False
                assumptions['normality']['details'] = f"Shapiro-Wilk test rejected normality (p={shapiro_p:.3f})"
                logger.warning(f"Normality assumption failed: p={shapiro_p:.3f}")
            else:
                assumptions['normality']['details'] = f"Shapiro-Wilk test passed (p={shapiro_p:.3f})"
        except Exception as e:
            logger.warning(f"Could not perform Shapiro-Wilk test: {e}")
        
        # 3. Multicollinearity: VIF
        vif_data = []
        for i, col in enumerate(X.columns):
            if col == 'const':
                continue
            vif = sm.stats.variance_inflation_factor(X.values, i)
            vif_data.append({'variable': col, 'vif': vif})
            if vif > 10:
                assumptions['multicollinearity']['passed'] = False
                assumptions['multicollinearity']['details'] += f"High VIF for {col}: {vif:.2f} "
                logger.warning(f"Multicollinearity detected for {col}: VIF={vif:.2f}")
        
        assumptions['multicollinearity']['vif_details'] = vif_data
        
    return assumptions

def run_full_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run the full analysis pipeline: validity check, correlations, regression, assumptions.
    
    Args:
        df: Cleaned DataFrame
        
    Returns:
        Dictionary containing all analysis results
    """
    logger.info("Starting full analysis pipeline")
    
    # 1. Construct Validity Check
    try:
        check_construct_validity(df, 'baseline_anxiety', 'anxiety_score')
        logger.info("Construct validity check passed.")
    except MathematicalCouplingError as e:
        logger.error(f"Construct validity check failed: {e}")
        raise
    
    # 2. Proxy Check
    proxy_result = check_proxy_anxiety(df, 'anxiety_score')
    
    # 3. Correlations
    correlations = run_initial_correlations(df)
    
    # 4. Regression
    regression_results = fit_regression_model(df)
    
    # 5. Assumption Checks
    assumptions = check_assumptions(regression_results, df, regression_results['formula'])
    regression_results['assumption_checks'] = assumptions
    
    # 6. Compile final report
    final_results = {
        'proxy_check': proxy_result,
        'correlations': correlations,
        'regression': regression_results
    }
    
    logger.info("Full analysis pipeline completed successfully.")
    return final_results

def main():
    """Main entry point for model analysis."""
    config = load_config()
    data_path = Path(config['data']['processed_path'])
    
    if not data_path.exists():
        logger.error(f"Processed data file not found at {data_path}")
        return
    
    df = pd.read_csv(data_path)
    results = run_full_analysis(df)
    
    # Save results
    output_path = Path(config['outputs']['regression_results_path'])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")

if __name__ == '__main__':
    main()
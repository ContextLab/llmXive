import logging
import sys
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, List, Union
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests

logger = logging.getLogger(__name__)

def calculate_skewness(series: pd.Series) -> float:
    """Calculate skewness of a series."""
    return series.skew()

def shapiro_wilk_test(series: pd.Series) -> Tuple[float, float]:
    """Perform Shapiro-Wilk test for normality."""
    if len(series) < 3:
        return 0.0, 1.0
    stat, p_value = sm.stats.shapiro(series.dropna())
    return float(stat), float(p_value)

def should_switch_to_spearman(series_x: pd.Series, series_y: pd.Series) -> bool:
    """
    Determine if Spearman correlation should be used instead of Pearson.
    Switch if skewness > 1.0 or Shapiro-Wilk p < 0.05 for either variable.
    """
    skew_x = calculate_skewness(series_x)
    skew_y = calculate_skewness(series_y)
    
    if abs(skew_x) > 1.0 or abs(skew_y) > 1.0:
        logger.info(f"High skewness detected (x: {skew_x:.2f}, y: {skew_y:.2f}). Switching to Spearman.")
        return True
        
    stat_x, p_x = shapiro_wilk_test(series_x)
    stat_y, p_y = shapiro_wilk_test(series_y)
    
    if p_x < 0.05 or p_y < 0.05:
        logger.info(f"Non-normal distribution detected (p_x: {p_x:.4f}, p_y: {p_y:.4f}). Switching to Spearman.")
        return True
        
    return False

def pearson_correlation_with_ci(series_x: pd.Series, series_y: pd.Series) -> Dict[str, float]:
    """Calculate Pearson correlation with confidence interval."""
    valid_mask = series_x.notna() & series_y.notna()
    x = series_x[valid_mask]
    y = series_y[valid_mask]
    
    if len(x) < 3:
        return {"correlation": np.nan, "p_value": np.nan, "ci_lower": np.nan, "ci_upper": np.nan}
        
    corr, p_value = sm.stats.pearsonr(x, y)
    n = len(x)
    # Fisher transformation for CI
    z = 0.5 * np.log((1 + corr) / (1 - corr + 1e-10))
    se = 1 / np.sqrt(n - 3)
    z_lower = z - 1.96 * se
    z_upper = z + 1.96 * se
    ci_lower = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
    ci_upper = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)
    
    return {
        "correlation": float(corr),
        "p_value": float(p_value),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper)
    }

def spearman_correlation_with_ci(series_x: pd.Series, series_y: pd.Series) -> Dict[str, float]:
    """Calculate Spearman correlation with confidence interval (approximate)."""
    valid_mask = series_x.notna() & series_y.notna()
    x = series_x[valid_mask]
    y = series_y[valid_mask]
    
    if len(x) < 3:
        return {"correlation": np.nan, "p_value": np.nan, "ci_lower": np.nan, "ci_upper": np.nan}
        
    corr, p_value = sm.stats.spearmanr(x, y)
    n = len(x)
    # Approximate CI using Fisher transformation
    z = 0.5 * np.log((1 + corr) / (1 - corr + 1e-10))
    se = 1 / np.sqrt(n - 3)
    z_lower = z - 1.96 * se
    z_upper = z + 1.96 * se
    ci_lower = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
    ci_upper = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)
    
    return {
        "correlation": float(corr),
        "p_value": float(p_value),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper)
    }

def apply_benjamini_hochberg(p_values: List[float]) -> List[float]:
    """Apply Benjamini-Hochberg correction to a list of p-values."""
    if not p_values:
        return []
    n = len(p_values)
    sorted_indices = sorted(range(n), key=lambda i: p_values[i])
    sorted_p = [p_values[i] for i in sorted_indices]
    
    corrected = [0.0] * n
    prev_corrected = 1.0
    
    for i in range(n - 1, -1, -1):
        rank = i + 1
        adjusted = sorted_p[i] * n / rank
        corrected_val = min(adjusted, prev_corrected)
        corrected_val = min(corrected_val, 1.0)
        corrected[sorted_indices[i]] = corrected_val
        prev_corrected = corrected_val
        
    return corrected

def run_regression_analysis(df: pd.DataFrame, 
                            dependent_var: str, 
                            independent_vars: List[str], 
                            include_intercept: bool = True) -> Dict[str, Any]:
    """
    Run a linear regression analysis.
    
    Args:
        df: DataFrame containing the data
        dependent_var: Name of the dependent variable
        independent_vars: List of independent variable names
        include_intercept: Whether to include an intercept term
        
    Returns:
        Dictionary with regression results
    """
    # Handle missing values
    cols = [dependent_var] + independent_vars
    valid_df = df[cols].dropna()
    
    if len(valid_df) < 3:
        logger.warning("Insufficient data for regression analysis.")
        return {
            "r_squared": np.nan,
            "coefficients": {},
            "p_values": {},
            "model": None
        }
        
    y = valid_df[dependent_var].values
    X = valid_df[independent_vars].values
    
    if include_intercept:
        X = sm.add_constant(X)
        
    model = sm.OLS(y, X).fit()
    
    coefficients = {}
    p_values = {}
    
    for i, var in enumerate(independent_vars):
        idx = i + 1 if include_intercept else i
        coefficients[var] = float(model.params[idx])
        p_values[var] = float(model.pvalues[idx])
        
    if include_intercept:
        coefficients['intercept'] = float(model.params[0])
        
    return {
        "r_squared": float(model.rsquared),
        "coefficients": coefficients,
        "p_values": p_values,
        "model": model
    }

def run_multiple_regressions(df: pd.DataFrame, 
                             dependent_var: str, 
                             diversity_var: str, 
                             covariates: List[str]) -> Dict[str, Any]:
    """
    Run multiple regression models:
    1. Baseline model: Cognitive ~ Covariates only
    2. Full model: Cognitive ~ Diversity + Covariates
    
    Calculates delta R-squared (Full - Baseline).
    
    Args:
        df: DataFrame containing the data
        dependent_var: Name of the dependent variable (e.g., cognitive_flexibility_score)
        diversity_var: Name of the diversity metric variable
        covariates: List of covariate names
        
    Returns:
        Dictionary with results from both models and delta R-squared
    """
    logger.info(f"Running multiple regression analysis for {dependent_var} ~ {diversity_var} + {covariates}")
    
    # Baseline model: Cognitive ~ Covariates only
    baseline_vars = covariates
    baseline_result = run_regression_analysis(df, dependent_var, baseline_vars)
    baseline_r_squared = baseline_result.get("r_squared", np.nan)
    
    # Full model: Cognitive ~ Diversity + Covariates
    full_vars = [diversity_var] + covariates
    full_result = run_regression_analysis(df, dependent_var, full_vars)
    full_r_squared = full_result.get("r_squared", np.nan)
    
    # Calculate delta R-squared
    delta_r_squared = np.nan
    if not np.isnan(baseline_r_squared) and not np.isnan(full_r_squared):
        delta_r_squared = full_r_squared - baseline_r_squared
        logger.info(f"Baseline R²: {baseline_r_squared:.4f}, Full R²: {full_r_squared:.4f}, Delta R²: {delta_r_squared:.4f}")
    else:
        logger.warning("Could not calculate delta R-squared due to missing values.")
        
    return {
        "baseline_model": {
            "r_squared": baseline_r_squared,
            "coefficients": baseline_result.get("coefficients", {}),
            "p_values": baseline_result.get("p_values", {})
        },
        "full_model": {
            "r_squared": full_r_squared,
            "coefficients": full_result.get("coefficients", {}),
            "p_values": full_result.get("p_values", {})
        },
        "delta_r_squared": float(delta_r_squared) if not np.isnan(delta_r_squared) else None
    }

def main():
    """Main entry point for running correlation analysis."""
    from code.src.utils.config import get_processed_data_dir, get_results_dir, setup_logging
    import json
    
    setup_logging()
    logger.info("Starting correlation analysis pipeline.")
    
    processed_dir = get_processed_data_dir()
    results_dir = get_results_dir()
    
    # Load filtered cohort
    cohort_path = processed_dir / "filtered_cohort.csv"
    if not cohort_path.exists():
        logger.error(f"Filtered cohort file not found: {cohort_path}")
        sys.exit(1)
        
    df = pd.read_csv(cohort_path)
    logger.info(f"Loaded {len(df)} records from {cohort_path}")
    
    # Define covariates as per spec FR-002
    covariates = ['age', 'sex', 'bmi', 'dietary_fiber_intake', 'antibiotic_use_history']
    dependent_var = 'cognitive_flexibility_score'
    
    # Diversity metrics to analyze
    diversity_metrics = ['shannon_diversity', 'simpson_diversity', 'chao1']
    
    results = {}
    
    for metric in diversity_metrics:
        if metric not in df.columns:
            logger.warning(f"Diversity metric {metric} not found in dataset. Skipping.")
            continue
            
        logger.info(f"Analyzing {metric}")
        
        # Run regression analysis
        regression_results = run_multiple_regressions(df, dependent_var, metric, covariates)
        
        results[metric] = {
            "baseline_r_squared": regression_results["baseline_model"]["r_squared"],
            "full_r_squared": regression_results["full_model"]["r_squared"],
            "delta_r_squared": regression_results["delta_r_squared"],
            "full_model_coefficients": regression_results["full_model"]["coefficients"],
            "full_model_p_values": regression_results["full_model"]["p_values"]
        }
    
    # Save results
    output_path = results_dir / "correlation_results.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Results saved to {output_path}")
    return results

if __name__ == "__main__":
    main()

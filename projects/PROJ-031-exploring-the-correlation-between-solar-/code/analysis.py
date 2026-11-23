"""
Statistical analysis module for solar flare and geomagnetic storm correlation.

Implements Spearman correlation, linear regression, VIF checks, and power analysis.
"""
import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant
import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import warnings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_mdes(n: int, alpha: float = 0.05, power: float = 0.80) -> float:
    """
    Calculate the Minimum Detectable Effect Size (MDES) for a given sample size.
    
    Uses the approximation for Pearson correlation coefficient:
    MDES ≈ t_alpha/2 * sqrt((1 - r^2) / (n - 2)) for large n,
    but we use a more direct inversion of power analysis for correlation.
    
    Args:
        n: Sample size
        alpha: Significance level (default 0.05)
        power: Desired statistical power (default 0.80)
        
    Returns:
        Minimum detectable effect size (correlation coefficient r)
    """
    if n < 3:
        return float('inf')
        
    # Use a simplified approximation based on the non-centrality parameter
    # For correlation, we use the Fisher z-transformation approach
    # t_crit = t_{1-alpha/2, n-2}
    t_crit = stats.t.ppf(1 - alpha/2, n - 2)
    
    # Approximate MDES using the formula: r = sqrt(t^2 / (t^2 + df))
    # This is derived from the t-statistic for correlation: t = r*sqrt((n-2)/(1-r^2))
    # Solving for r when t = t_crit gives the minimum detectable r
    df = n - 2
    mdes = np.sqrt((t_crit ** 2) / (t_crit ** 2 + df))
    
    return mdes

def power_analysis(n: int, effect_size: float = 0.30, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Perform post-hoc power analysis for correlation.
    
    Args:
        n: Sample size
        effect_size: Expected effect size (correlation r)
        alpha: Significance level
        
    Returns:
        Dictionary with power analysis results
    """
    if n < 3:
        return {
            'sample_size': n,
            'effect_size': effect_size,
            'power': 0.0,
            'warning': 'Sample size too small for power analysis'
        }
    
    # Calculate non-centrality parameter
    # For correlation test: t = r * sqrt((n-2)/(1-r^2))
    t_stat = effect_size * np.sqrt((n - 2) / (1 - effect_size ** 2))
    
    # Critical t-value
    t_crit = stats.t.ppf(1 - alpha/2, n - 2)
    
    # Power is the probability that |t| > t_crit under the alternative
    # Using non-central t-distribution approximation
    # For simplicity, we use the normal approximation for large n
    if n > 30:
        z_stat = t_stat
        z_crit = stats.norm.ppf(1 - alpha/2)
        power = stats.norm.cdf(z_stat - z_crit) + stats.norm.cdf(-z_stat - z_crit)
    else:
        # For small samples, use t-distribution
        # Power = P(|T| > t_crit | non-centrality parameter)
        # Approximate using the non-central t-distribution
        from scipy.stats import nct
        df = n - 2
        ncp = t_stat  # Non-centrality parameter
        power = 1 - (nct.cdf(t_crit, df, ncp) - nct.cdf(-t_crit, df, ncp))
    
    return {
        'sample_size': n,
        'effect_size': effect_size,
        'power': float(power),
        'alpha': alpha,
        't_statistic': float(t_stat),
        't_critical': float(t_crit)
    }

def spearman_correlation(x: pd.Series, y: pd.Series) -> Dict[str, float]:
    """
    Compute Spearman rank correlation with p-value.
    
    Args:
        x: First variable
        y: Second variable
        
    Returns:
        Dictionary with correlation coefficient and p-value
    """
    # Remove NaN pairs
    mask = ~(x.isna() | y.isna())
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 3:
        return {
            'correlation': np.nan,
            'p_value': np.nan,
            'n': len(x_clean)
        }
    
    corr, p_val = stats.spearmanr(x_clean, y_clean)
    
    return {
        'correlation': float(corr),
        'p_value': float(p_val),
        'n': len(x_clean)
    }

def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor for each predictor.
    
    Args:
        df: DataFrame with predictors
        predictors: List of predictor column names
        
    Returns:
        Dictionary mapping predictor names to VIF values
    """
    X = df[predictors].dropna()
    if X.shape[0] < 5:
        return {p: float('inf') for p in predictors}
        
    X = add_constant(X)
    vif_data = {}
    
    for i, col in enumerate(predictors):
        # Skip constant if it's in predictors
        if col == 'const':
            continue
            
        try:
            vif = variance_inflation_factor(X.values, i + 1)  # +1 because of constant
            vif_data[col] = float(vif)
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_data[col] = float('inf')
    
    return vif_data

def linear_regression_r2(df: pd.DataFrame, predictor: str, target: str) -> Dict[str, Any]:
    """
    Perform simple linear regression and return R².
    
    Args:
        df: DataFrame with data
        predictor: Name of predictor column
        target: Name of target column
        
    Returns:
        Dictionary with R², coefficients, and p-values
    """
    data = df[[predictor, target]].dropna()
    if len(data) < 3:
        return {
            'r2': np.nan,
            'coefficients': {},
            'p_values': {},
            'n': len(data)
        }
    
    X = add_constant(data[predictor])
    y = data[target]
    
    model = OLS(y, X).fit()
    
    return {
        'r2': float(model.rsquared),
        'coefficients': {
            'intercept': float(model.params['const']),
            predictor: float(model.params[predictor])
        },
        'p_values': {
            'intercept': float(model.pvalues['const']),
            predictor: float(model.pvalues[predictor])
        },
        'n': len(data)
    }

def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Bonferroni correction for multiple comparisons.
    
    Args:
        p_values: List of p-values
        alpha: Significance level
        
    Returns:
        Dictionary with corrected p-values and significance flags
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return {'corrected_p_values': [], 'significant': []}
    
    corrected_p = [min(p * n_tests, 1.0) for p in p_values]
    significant = [p < alpha for p in corrected_p]
    
    return {
        'corrected_p_values': corrected_p,
        'significant': significant,
        'alpha': alpha,
        'n_tests': n_tests
    }

def test_piecewise_model(df: pd.DataFrame, x_col: str, y_col: str, 
                         break_point: Optional[float] = None) -> Dict[str, Any]:
    """
    Test a piecewise linear regression model.
    
    Args:
        df: DataFrame with data
        x_col: Predictor column name
        y_col: Target column name
        break_point: Break point for piecewise regression
        
    Returns:
        Dictionary with piecewise model results
    """
    data = df[[x_col, y_col]].dropna()
    if len(data) < 10:
        return {
            'r2': np.nan,
            'improvement': np.nan,
            'n': len(data)
        }
    
    if break_point is None:
        break_point = np.median(data[x_col])
    
    # Create piecewise features
    x = data[x_col].values
    y = data[y_col].values
    
    # Features: x, (x - break_point)_+
    x_piecewise = np.maximum(0, x - break_point)
    X = np.column_stack([np.ones(len(x)), x, x_piecewise])
    
    try:
        # Fit piecewise model
        coeffs = np.linalg.lstsq(X, y, rcond=None)[0]
        y_pred = X @ coeffs
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2_piecewise = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Fit linear model for comparison
        X_linear = np.column_stack([np.ones(len(x)), x])
        coeffs_linear = np.linalg.lstsq(X_linear, y, rcond=None)[0]
        y_pred_linear = X_linear @ coeffs_linear
        ss_res_linear = np.sum((y - y_pred_linear) ** 2)
        r2_linear = 1 - (ss_res_linear / ss_tot) if ss_tot > 0 else 0
        
        improvement = r2_piecewise - r2_linear
        
        return {
            'r2_piecewise': float(r2_piecewise),
            'r2_linear': float(r2_linear),
            'improvement': float(improvement),
            'break_point': float(break_point),
            'n': len(data)
        }
    except Exception as e:
        logger.warning(f"Piecewise regression failed: {e}")
        return {
            'r2_piecewise': np.nan,
            'r2_linear': np.nan,
            'improvement': np.nan,
            'break_point': float(break_point),
            'n': len(data)
        }

def validate_timeseries_split(df: pd.DataFrame, train_end: str = "2020-12-31") -> Dict[str, Any]:
    """
    Validate the time-series split and return train/test masks.
    
    Args:
        df: DataFrame with datetime index or column
        train_end: End date for training set
        
    Returns:
        Dictionary with train/test masks and split info
    """
    if 'timestamp' not in df.columns:
        # Try to find a datetime column
        date_cols = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
        if not date_cols:
            raise ValueError("No datetime column found in DataFrame")
        date_col = date_cols[0]
    else:
        date_col = 'timestamp'
    
    # Ensure date column is datetime
    df[date_col] = pd.to_datetime(df[date_col])
    
    train_mask = df[date_col] <= pd.to_datetime(train_end)
    test_mask = ~train_mask
    
    return {
        'train_mask': train_mask,
        'test_mask': test_mask,
        'train_size': int(train_mask.sum()),
        'test_size': int(test_mask.sum()),
        'train_end': train_end
    }

def calculate_missing_data_counts(df: pd.DataFrame) -> Dict[str, int]:
    """
    Calculate counts of missing data for key columns.
    
    Args:
        df: DataFrame with data
        
    Returns:
        Dictionary with missing counts per column
    """
    key_cols = ['flare_flux', 'cme_speed', 'dst_min', 'kp_index']
    missing_counts = {}
    
    for col in key_cols:
        if col in df.columns:
            missing_counts[col] = int(df[col].isna().sum())
        else:
            missing_counts[col] = 0
    
    return missing_counts

def run_correlation_analysis(df: pd.DataFrame, results_path: str = "results/metrics.json") -> Dict[str, Any]:
    """
    Run the full correlation analysis pipeline.
    
    Args:
        df: DataFrame with aligned events
        results_path: Path to output metrics file
        
    Returns:
        Dictionary with all analysis results
    """
    logger.info("Starting correlation analysis...")
    
    results = {
        'analysis_timestamp': pd.Timestamp.now().isoformat(),
        'sample_size': len(df),
        'correlations': {},
        'regression_models': {},
        'vif_analysis': {},
        'power_analysis': {},
        'missing_data_counts': calculate_missing_data_counts(df),
        'power_limitation': None
    }
    
    # 1. Spearman correlations
    logger.info("Computing Spearman correlations...")
    
    if 'flare_flux' in df.columns and 'dst_min' in df.columns:
        flare_corr = spearman_correlation(df['flare_flux'].apply(np.log10), df['dst_min'])
        results['correlations']['flare_flux_log_dst'] = flare_corr
    
    if 'cme_speed' in df.columns and 'dst_min' in df.columns:
        cme_corr = spearman_correlation(df['cme_speed'], df['dst_min'])
        results['correlations']['cme_speed_dst'] = cme_corr
    
    # 2. Linear regression and VIF
    logger.info("Computing linear regression and VIF...")
    
    if 'flare_flux' in df.columns and 'cme_speed' in df.columns and 'dst_min' in df.columns:
        predictors = ['flare_flux', 'cme_speed']
        available_predictors = [p for p in predictors if p in df.columns]
        
        if len(available_predictors) >= 2:
            # Try multivariate
            vif_results = calculate_vif(df, available_predictors)
            results['vif_analysis'] = vif_results
            
            max_vif = max(vif_results.values()) if vif_results else 0
            
            if max_vif > 5:
                logger.warning("High VIF detected (>5), switching to univariate models")
                # Select univariate model with higher correlation
                univariate_results = {}
                for pred in available_predictors:
                    if pred in df.columns:
                        reg_result = linear_regression_r2(df, pred, 'dst_min')
                        univariate_results[pred] = reg_result
                
                # Select best based on absolute correlation
                best_pred = None
                best_abs_corr = 0
                if 'flare_flux_log_dst' in results['correlations']:
                    best_abs_corr = abs(results['correlations']['flare_flux_log_dst']['correlation'])
                    best_pred = 'flare_flux'
                if 'cme_speed_dst' in results['correlations']:
                    cme_abs = abs(results['correlations']['cme_speed_dst']['correlation'])
                    if cme_abs > best_abs_corr:
                        best_abs_corr = cme_abs
                        best_pred = 'cme_speed'
                
                if best_pred:
                    results['selected_model_type'] = f'univariate_{best_pred}'
                    results['regression_models'] = {best_pred: univariate_results.get(best_pred, {})}
            else:
                # Multivariate model
                df_clean = df[available_predictors + ['dst_min']].dropna()
                if len(df_clean) >= 5:
                    X = add_constant(df_clean[available_predictors])
                    y = df_clean['dst_min']
                    model = OLS(y, X).fit()
                    results['regression_models']['multivariate'] = {
                        'r2': float(model.rsquared),
                        'coefficients': {k: float(v) for k, v in model.params.items()},
                        'p_values': {k: float(v) for k, v in model.pvalues.items()}
                    }
                    results['selected_model_type'] = 'multivariate'
        else:
            # Fallback to univariate
            for pred in available_predictors:
                if pred in df.columns:
                    reg_result = linear_regression_r2(df, pred, 'dst_min')
                    results['regression_models'][pred] = reg_result
    
    # 3. Power Analysis and MDES
    logger.info("Performing power analysis...")
    n = len(df)
    results['power_analysis'] = power_analysis(n)
    
    # Calculate MDES
    mdes = calculate_mdes(n)
    results['minimum_detectable_effect_size'] = float(mdes)
    
    # 4. Power Limitation Check
    if n < 30:
        logger.warning(f"Sample size (n={n}) is below threshold (30). Power limitation noted.")
        results['power_limitation'] = {
            'warning': 'Power Limitation: Sample size is insufficient for definitive threshold claims',
            'sample_size': n,
            'minimum_recommended': 30,
            'interpretation': 'With N < 30, the statistical power is low. Definitive threshold claims cannot be made. The Minimum Detectable Effect Size (MDES) is large, meaning only very strong correlations would be detected.',
            'mdes': float(mdes)
        }
    
    # 5. Piecewise regression test (if R² < 0.1)
    if results.get('regression_models'):
        best_r2 = 0
        for model_name, model_data in results['regression_models'].items():
            if isinstance(model_data, dict) and 'r2' in model_data:
                best_r2 = max(best_r2, model_data.get('r2', 0) or 0)
        
        if best_r2 < 0.1:
            logger.info("R² < 0.1, testing piecewise regression...")
            if 'cme_speed' in df.columns and 'dst_min' in df.columns:
                piecewise_result = test_piecewise_model(df, 'cme_speed', 'dst_min')
                results['piecewise_r2_improvement'] = piecewise_result.get('improvement')
                results['piecewise_analysis'] = piecewise_result
    
    # 6. Save results
    os.makedirs(os.path.dirname(results_path) if os.path.dirname(results_path) else '.', exist_ok=True)
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Analysis complete. Results saved to {results_path}")
    return results

def main():
    """Main entry point for analysis module."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run correlation analysis')
    parser.add_argument('--input', type=str, required=True, help='Input CSV file')
    parser.add_argument('--output', type=str, default='results/metrics.json', help='Output metrics file')
    args = parser.parse_args()
    
    # Load data
    df = pd.read_csv(args.input)
    
    # Run analysis
    results = run_correlation_analysis(df, args.output)
    
    print(f"Analysis complete. Sample size: {results['sample_size']}")
    print(f"Minimum Detectable Effect Size: {results.get('minimum_detectable_effect_size', 'N/A')}")
    if results.get('power_limitation'):
        print("WARNING: Power limitation detected!")
        print(results['power_limitation']['warning'])

if __name__ == '__main__':
    main()
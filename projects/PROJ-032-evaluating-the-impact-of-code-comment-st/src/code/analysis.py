"""
Statistical analysis module for evaluating code comment impact on maintainability.

Implements regression analysis, FDR correction, and sensitivity analysis.
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.sandwich_covariance import cov_hc1

logger = logging.getLogger(__name__)


def run_regression(data_path: str, output_path: str) -> Dict[str, Any]:
    """
    Run Multiple Linear Regression (MLR) with robust standard errors.
    
    Models maintainability (bug_fix_rate) vs comment metrics (readability, sentiment, density),
    controlling for age, LOC (complexity), and contributors.
    
    Args:
        data_path: Path to the input metrics CSV file.
        output_path: Path to save the analysis results JSON.
        
    Returns:
        Dictionary containing model results (R², p-values, coefficients).
    """
    logger.info(f"Loading metrics data from {data_path}")
    df = pd.read_csv(data_path)
    
    # Define dependent and independent variables
    # Dependent: bug_fix_rate (maintainability proxy)
    # Independent: readability, sentiment, density
    # Controls: age, complexity (as proxy for LOC), contributors
    dependent_vars = ['bug_fix_rate']
    independent_vars = ['readability', 'sentiment', 'density']
    control_vars = ['age', 'complexity', 'contributors']
    
    # Check for missing data
    cols_to_use = dependent_vars + independent_vars + control_vars
    available_cols = [col for col in cols_to_use if col in df.columns]
    
    if len(available_cols) < len(cols_to_use):
        missing = set(cols_to_use) - set(available_cols)
        logger.warning(f"Missing columns in data: {missing}. Dropping rows with NaN.")
    
    clean_df = df[available_cols].dropna()
    
    if clean_df.empty:
        raise ValueError("No valid data rows after cleaning.")
    
    y = clean_df['bug_fix_rate']
    X = clean_df[independent_vars + control_vars]
    
    # Add constant for intercept
    X = sm.add_constant(X)
    
    # Fit OLS model
    model = sm.OLS(y, X)
    results = model.fit(cov_type='HC1')  # Robust standard errors (White)
    
    # Extract results
    r_squared = results.rsquared
    p_values = results.pvalues.to_dict()
    coefficients = results.params.to_dict()
    
    # Determine significance for main variables of interest
    main_vars_pvalues = {var: p_values.get(var, 1.0) for var in independent_vars}
    
    analysis_results = {
        'model_type': 'Multiple Linear Regression (HC1 Robust SE)',
        'r_squared': float(r_squared),
        'p_values': p_values,
        'coefficients': coefficients,
        'is_significant': any(p < 0.05 for p in main_vars_pvalues.values()),
        'sample_size': len(clean_df),
        'main_vars_pvalues': main_vars_pvalues
    }
    
    logger.info(f"Regression complete. R²: {r_squared:.4f}")
    
    # Save results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(analysis_results, f, indent=2)
        
    return analysis_results


def apply_fdr_correction(p_values: Dict[str, float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.
    
    Args:
        p_values: Dictionary mapping variable names to p-values.
        alpha: Significance threshold (default 0.05).
        
    Returns:
        Dictionary with corrected p-values and significance flags.
    """
    if not p_values:
        return {'corrected_p_values': {}, 'is_significant': {}}
    
    vars_list = list(p_values.keys())
    p_vals = np.array([p_values[v] for v in vars_list])
    
    # Apply BH correction
    reject, p_corrected, _, _ = multipletests(p_vals, alpha=alpha, method='fdr_bh')
    
    corrected_p_values = {vars_list[i]: float(p_corrected[i]) for i in range(len(vars_list))}
    is_significant = {vars_list[i]: bool(reject[i]) for i in range(len(vars_list))}
    
    return {
        'corrected_p_values': corrected_p_values,
        'is_significant': is_significant,
        'alpha': alpha,
        'method': 'Benjamini-Hochberg'
    }


def run_sensitivity(
    data_path: str, 
    output_path: str, 
    thresholds: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis by sweeping significance thresholds.
    
    This function tests the stability of results across a range of p-value thresholds
    (e.g., 0.01, 0.05, 0.10) to ensure findings are not artifacts of a specific cutoff.
    
    Note: The final report must use the fixed p < 0.05 threshold. This analysis
    is for exploratory purposes only.
    
    Args:
        data_path: Path to the input metrics CSV file.
        output_path: Path to save the sensitivity report JSON.
        thresholds: List of p-value thresholds to test. Defaults to [0.01, 0.05, 0.10].
        
    Returns:
        Dictionary containing sensitivity analysis results.
    """
    if thresholds is None:
        thresholds = [0.01, 0.05, 0.10]
    
    logger.info(f"Starting sensitivity analysis with thresholds: {thresholds}")
    
    # Run the regression first to get p-values
    regression_results = run_regression(data_path, output_path.replace('sensitivity_report.json', 'analysis_results.json'))
    
    p_values = regression_results.get('p_values', {})
    main_vars = ['readability', 'sentiment', 'density']
    
    sensitivity_data = []
    
    for threshold in thresholds:
        significant_count = 0
        significant_vars = []
        
        for var in main_vars:
            if var in p_values and p_values[var] < threshold:
                significant_count += 1
                significant_vars.append(var)
        
        sensitivity_data.append({
            'threshold': threshold,
            'significant_count': significant_count,
            'significant_variables': significant_vars,
            'total_tested': len(main_vars)
        })
        
        logger.info(f"Threshold {threshold}: {significant_count}/{len(main_vars)} significant")
    
    # Prepare final report
    report = {
        'model_type': regression_results['model_type'],
        'r_squared': regression_results['r_squared'],
        'p_values': p_values,
        'is_significant_fixed': any(p_values.get(v, 1.0) < 0.05 for v in main_vars),
        'sensitivity_data': sensitivity_data,
        'note': "Sensitivity analysis for exploratory purposes. Final report uses fixed p < 0.05."
    }
    
    # Save report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"Sensitivity report saved to {output_path}")
    return report


def main():
    """Main entry point for running the sensitivity analysis."""
    # Configure logging
    from utils import configure_logging
    configure_logging()
    
    # Define paths
    # Assuming standard project structure: data/processed/metrics.csv
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')
    metrics_path = os.path.join(data_dir, 'metrics.csv')
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')
    output_path = os.path.join(output_dir, 'sensitivity_report.json')
    
    if not os.path.exists(metrics_path):
        logger.error(f"Data file not found: {metrics_path}")
        logger.info("Please ensure metrics.csv has been generated by the metric computation phase.")
        return
    
    # Run sensitivity analysis
    try:
        result = run_sensitivity(metrics_path, output_path)
        print(f"Sensitivity analysis complete. Results written to {output_path}")
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"Error during sensitivity analysis: {e}")
        raise


if __name__ == '__main__':
    main()
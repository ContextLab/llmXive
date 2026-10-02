import os
import json
import logging
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests

from utils import configure_logging

# Configure logging
logger = logging.getLogger(__name__)

def load_metrics_data(csv_path: str) -> List[Dict[str, Any]]:
    """Load metrics from a CSV file into a list of dictionaries."""
    data = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            numeric_fields = ['readability', 'sentiment', 'density', 'churn', 
                              'bug_fix_rate', 'complexity', 'age', 'contributors']
            for field in numeric_fields:
                if field in row:
                    try:
                        row[field] = float(row[field])
                    except ValueError:
                        row[field] = 0.0
            data.append(row)
    return data

def run_regression(data: List[Dict[str, Any]], 
                   dependent_var: str = 'churn',
                   independent_vars: List[str] = None,
                   controls: List[str] = None) -> Dict[str, Any]:
    """
    Run Multiple Linear Regression with robust standard errors.
    
    Args:
        data: List of metric dictionaries
        dependent_var: Name of the dependent variable
        independent_vars: List of independent variables (comment metrics)
        controls: List of control variables (age, complexity, etc.)
        
    Returns:
        Dictionary with regression results
    """
    if independent_vars is None:
        independent_vars = ['readability', 'sentiment', 'density']
    if controls is None:
        controls = ['age', 'complexity', 'contributors']
    
    # Prepare feature matrix and target
    features = independent_vars + controls
    X = []
    y = []
    
    for row in data:
        # Check for missing values
        if any(row.get(f) is None for f in features + [dependent_var]):
            continue
        
        x_row = [row[f] for f in features]
        X.append(x_row)
        y.append(row[dependent_var])
    
    if len(X) == 0:
        logger.warning("No valid data points for regression")
        return {
            'model_type': 'MLR',
            'r_squared': 0.0,
            'coefficients': {},
            'p_values': {},
            'is_significant': False,
            'error': 'No valid data'
        }
    
    X = np.array(X)
    y = np.array(y)
    
    # Add constant for intercept
    X = sm.add_constant(X)
    
    # Fit model with robust standard errors (HC1)
    model = sm.OLS(y, X)
    results = model.fit(cov_type='HC1')
    
    # Extract results
    coef_dict = {
        'const': float(results.params[0])
    }
    p_values = {}
    
    for i, var in enumerate(features):
        coef_dict[var] = float(results.params[i + 1])
        p_values[var] = float(results.pvalues[i + 1])
    
    return {
        'model_type': 'MLR',
        'r_squared': float(results.rsquared),
        'coefficients': coef_dict,
        'p_values': p_values,
        'is_significant': False, # Will be updated after FDR
        'n_observations': len(y),
        'f_statistic': float(results.fvalue),
        'f_pvalue': float(results.f_pvalue)
    }

def apply_fdr_correction(p_values: Dict[str, float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.
    
    Args:
        p_values: Dictionary mapping variable names to their p-values
        alpha: Significance threshold (default 0.05)
        
    Returns:
        Dictionary containing:
        - corrected_p_values: FDR-adjusted p-values
        - is_significant: Dictionary mapping variables to significance status
        - num_significant: Count of significant variables
        - threshold: The alpha threshold used
    """
    if not p_values:
        return {
            'corrected_p_values': {},
            'is_significant': {},
            'num_significant': 0,
            'threshold': alpha
        }
    
    # Extract p-values and labels
    labels = list(p_values.keys())
    p_vals = np.array(list(p_values.values()))
    
    # Apply Benjamini-Hochberg correction
    # multipletests returns (reject, pvals_corrected, alphacSidak, alphacBonf)
    reject, corrected_pvals, _, _ = multipletests(p_vals, alpha=alpha, method='fdr_bh')
    
    # Map results back to original labels
    corrected_p_values = {label: float(p) for label, p in zip(labels, corrected_pvals)}
    is_significant = {label: bool(rej) for label, rej in zip(labels, reject)}
    
    num_significant = sum(is_significant.values())
    
    logger.info(f"FDR correction applied: {num_significant}/{len(labels)} variables significant at alpha={alpha}")
    
    return {
        'corrected_p_values': corrected_p_values,
        'is_significant': is_significant,
        'num_significant': num_significant,
        'threshold': alpha
    }

def run_sensitivity_analysis(data: List[Dict[str, Any]], 
                             dependent_var: str = 'churn',
                             independent_vars: List[str] = None) -> Dict[str, Any]:
    """
    Run sensitivity analysis by sweeping significance thresholds.
    
    Args:
        data: List of metric dictionaries
        dependent_var: Name of the dependent variable
        independent_vars: List of independent variables
        
    Returns:
        Dictionary with sensitivity analysis results
    """
    thresholds = [0.01, 0.05, 0.10]
    results = {}
    
    # Run regression first
    regression_results = run_regression(data, dependent_var, independent_vars)
    
    if 'error' in regression_results:
        return {'error': regression_results['error']}
    
    p_values = regression_results['p_values']
    
    for alpha in thresholds:
        fdr_result = apply_fdr_correction(p_values, alpha)
        results[f"alpha_{alpha}"] = {
            'num_significant': fdr_result['num_significant'],
            'significant_vars': [k for k, v in fdr_result['is_significant'].items() if v],
            'corrected_p_values': fdr_result['corrected_p_values']
        }
    
    return {
        'thresholds_tested': thresholds,
        'results': results,
        'base_regression': regression_results
    }

def save_analysis_results(results: Dict[str, Any], output_path: str):
    """Save analysis results to a JSON file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Analysis results saved to {output_path}")

def save_sensitivity_report(report: Dict[str, Any], output_path: str):
    """Save sensitivity report to a JSON file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    logger.info(f"Sensitivity report saved to {output_path}")

def main():
    """Main entry point for analysis pipeline."""
    configure_logging()
    
    # Load metrics data
    metrics_path = "data/processed/metrics.csv"
    if not os.path.exists(metrics_path):
        logger.error(f"Metrics file not found: {metrics_path}")
        return
    
    logger.info(f"Loading metrics from {metrics_path}")
    data = load_metrics_data(metrics_path)
    logger.info(f"Loaded {len(data)} records")
    
    # Run regression
    logger.info("Running regression analysis...")
    regression_results = run_regression(data)
    
    # Apply FDR correction
    logger.info("Applying FDR correction...")
    fdr_results = apply_fdr_correction(regression_results['p_values'])
    
    # Update regression results with FDR findings
    regression_results['is_significant'] = fdr_results['is_significant']
    regression_results['fdr_corrected'] = True
    regression_results['num_significant_vars'] = fdr_results['num_significant']
    
    # Save main analysis results
    output_path = "data/processed/analysis_results.json"
    save_analysis_results(regression_results, output_path)
    
    # Run and save sensitivity analysis
    logger.info("Running sensitivity analysis...")
    sensitivity_results = run_sensitivity_analysis(data)
    sensitivity_path = "data/processed/sensitivity_report.json"
    save_sensitivity_report(sensitivity_results, sensitivity_path)
    
    logger.info("Analysis pipeline completed successfully")

if __name__ == "__main__":
    main()

import os
import json
import logging
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import time
import tracemalloc
import statsmodels.api as sm
from statsmodels.stats.weightstats import DescrStatsW
from statsmodels.stats.multitest import multipletests
import pandas as pd
import numpy as np

from utils import configure_logging, timeit

logger = configure_logging()

def load_metrics_data(csv_path: str) -> pd.DataFrame:
    """Load metrics from CSV file."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Metrics file not found: {csv_path}")
    return pd.read_csv(csv_path)

@timeit
def run_regression(data: pd.DataFrame) -> Dict[str, Any]:
    """Run Multiple Linear Regression with robust standard errors."""
    # Ensure required columns exist
    required_cols = ['readability', 'sentiment', 'density', 'churn', 'bug_fix_rate', 'complexity', 'age', 'contributors']
    missing = [c for c in required_cols if c not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Define features and target
    # Target: maintainability proxy (e.g., bug_fix_rate or churn - depending on definition)
    # For this task, let's assume we model 'bug_fix_rate' as the target for maintainability
    # Features: readability, sentiment, density, complexity, age, contributors
    X = data[['readability', 'sentiment', 'density', 'complexity', 'age', 'contributors']].copy()
    y = data['bug_fix_rate'].copy()

    # Add constant for intercept
    X = sm.add_constant(X)

    # Fit model with robust standard errors
    model = sm.OLS(y, X)
    results = model.fit(cov_type='HC3') # Robust standard errors

    # Extract results
    r_squared = results.rsquared
    p_values = results.pvalues.tolist()
    params = results.params.tolist()
    is_significant = any(p < 0.05 for p in p_values[1:]) # Exclude intercept

    return {
        "model_type": "Multiple Linear Regression (HC3)",
        "r_squared": r_squared,
        "p_values": p_values,
        "params": params,
        "is_significant": is_significant,
        "sensitivity_data": []
    }

def apply_fdr_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """Apply Benjamini-Hochberg FDR correction."""
    reject, pvals_corrected, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')
    return pvals_corrected, reject

@timeit
def run_sensitivity_analysis(data: pd.DataFrame, thresholds: List[float] = [0.01, 0.05, 0.1]) -> Dict[str, Any]:
    """Sweep significance thresholds for exploratory analysis."""
    results = {}
    for threshold in thresholds:
        # Re-run regression (simplified for sensitivity)
        # In a real scenario, we might vary the model or data subset
        # Here we just re-evaluate significance at different thresholds
        reg_result = run_regression(data)
        p_values = reg_result['p_values']
        # Count significant predictors (excluding intercept)
        sig_count = sum(1 for p in p_values[1:] if p < threshold)
        results[str(threshold)] = {
            "significant_predictors": sig_count,
            "total_predictors": len(p_values) - 1,
            "threshold": threshold
        }
    return results

@timeit
def save_analysis_results(results: Dict[str, Any], output_path: str):
    """Save analysis results to JSON."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Analysis results saved to {output_path}")

@timeit
def save_sensitivity_report(report: Dict[str, Any], output_path: str):
    """Save sensitivity report to JSON."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Sensitivity report saved to {output_path}")

@timeit
def main():
    """Main entry point for analysis pipeline."""
    metrics_path = "data/processed/metrics.csv"
    analysis_output = "data/processed/analysis_results.json"
    sensitivity_output = "data/processed/sensitivity_report.json"

    if not os.path.exists(metrics_path):
        logger.error(f"Metrics file not found: {metrics_path}")
        return

    data = load_metrics_data(metrics_path)
    logger.info(f"Loaded {len(data)} records")

    # Run regression
    reg_results = run_regression(data)
    save_analysis_results(reg_results, analysis_output)

    # Apply FDR correction
    p_values = reg_results['p_values']
    corrected_p, reject = apply_fdr_correction(p_values)
    reg_results['corrected_p_values'] = corrected_p
    reg_results['fdr_rejected'] = reject.tolist()
    
    # Update significant flag based on corrected p-values (excluding intercept)
    reg_results['is_significant'] = any(p < 0.05 for p in corrected_p[1:])
    
    # Re-save with corrected values
    save_analysis_results(reg_results, analysis_output)

    # Run sensitivity analysis
    sens_results = run_sensitivity_analysis(data)
    save_sensitivity_report(sens_results, sensitivity_output)

    logger.info("Analysis pipeline completed successfully.")

if __name__ == "__main__":
    main()

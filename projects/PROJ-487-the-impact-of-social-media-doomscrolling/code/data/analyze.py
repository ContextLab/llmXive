import os
import sys
import logging
import json
from datetime import datetime
from typing import Dict, Tuple, Optional, List

import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import grangercausalitytests, adfuller
from scipy import stats

from utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Constants
LAGS_TO_TEST = [1, 2, 3, 7, 14]
ALPHA_BASE = 0.05
ALPHA_BONFERRONI = ALPHA_BASE / len(LAGS_TO_TEST)  # 0.01

def load_processed_data(filepath: str) -> pd.DataFrame:
    """
    Load the processed, aligned, and normalized time-series data.
    Expects columns: 'date', 'gdelt_neg_events', 'anxiety_trends' (or similar normalized names).
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Processed data file not found: {filepath}")
    
    df = pd.read_csv(filepath, parse_dates=['date'])
    df.set_index('date', inplace=True)
    df.sort_index(inplace=True)
    return df

def run_granger_causality_fixed_sweep(df: pd.DataFrame, maxlag: int = 14) -> pd.DataFrame:
    """
    Perform Granger causality tests for a fixed set of lags: {1, 2, 3, 7, 14}.
    
    Args:
        df: DataFrame with time-series data.
        maxlag: Maximum lag to consider (used for internal statsmodels logic if needed, 
                though we iterate explicitly).
                
    Returns:
        DataFrame with columns: 'lag', 'p_value' (from the 'ssr_ftest' or similar metric).
    """
    logger.info(f"Running Granger causality fixed sweep for lags: {LAGS_TO_TEST}")
    
    # Ensure we have exactly two columns for the test: [Y, X] where X is the potential cause
    # Assuming columns are normalized: 'gdelt_neg_events' (X) -> 'anxiety_trends' (Y)
    # The test checks if X Granger-causes Y.
    if len(df.columns) < 2:
        raise ValueError("DataFrame must have at least 2 columns for Granger causality.")
    
    # Let's assume the second column is the dependent variable (Y) and first is independent (X)
    # Or explicitly name them if the schema is known. Based on T011/T012:
    # gdelt -> anxiety.
    # We need to handle potential NaNs if the differencing/alignment wasn't perfect, 
    # though T022 ensures completeness.
    data_matrix = df.dropna().values
    
    results = []
    
    for lag in LAGS_TO_TEST:
        try:
            # grangercausalitytests returns a dict of test results
            # We are interested in the p-value of the F-test (ssr_ftest)
            test_result = grangercausalitytests(data_matrix, maxlag=lag, verbose=False)
            
            # The result for specific lag `lag` is at key `lag`
            # The F-test p-value is in 'ssr_ftest' at index [1]
            p_val = test_result[lag]['ssr_ftest'][1]
            results.append({'lag': lag, 'p_value': p_val})
            logger.info(f"Lag {lag}: p-value = {p_val:.6f}")
        except Exception as e:
            logger.error(f"Error computing Granger causality for lag {lag}: {e}")
            results.append({'lag': lag, 'p_value': np.nan})
    
    return pd.DataFrame(results)

def save_results(results_df: pd.DataFrame, output_path: str):
    """Save Granger causality results to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    results_df.to_csv(output_path, index=False)
    logger.info(f"Granger causality results saved to {output_path}")

def perform_sensitivity_analysis(results_df: pd.DataFrame) -> Dict:
    """
    Perform sensitivity analysis on the Granger causality results.
    Calculates significance rates at alpha=0.05 and alpha=0.01 (Bonferroni).
    """
    if results_df.empty:
        logger.warning("Results DataFrame is empty, skipping sensitivity analysis.")
        return {}
    
    p_values = results_df['p_value'].dropna()
    if p_values.empty:
        return {}
    
    # Count significant lags at base alpha (0.05)
    sig_05 = (p_values < ALPHA_BASE).sum()
    # Count significant lags at Bonferroni alpha (0.01)
    sig_01 = (p_values < ALPHA_BONFERRONI).sum()
    
    total_tests = len(LAGS_TO_TEST)
    
    analysis = {
        'total_lags_tested': total_tests,
        'significant_at_0_05': int(sig_05),
        'rate_0_05': float(sig_05 / total_tests),
        'significant_at_bonferroni_0_01': int(sig_01),
        'rate_bonferroni_0_01': float(sig_01 / total_tests),
        'alpha_base': ALPHA_BASE,
        'alpha_bonferroni': ALPHA_BONFERRONI
    }
    
    logger.info(f"Sensitivity Analysis: {sig_05}/{total_tests} significant at 0.05; "
                f"{sig_01}/{total_tests} significant at Bonferroni 0.01.")
                
    return analysis

def statistical_validity_check(results_df: pd.DataFrame, log_path: str) -> Dict:
    """
    T028: Implement Statistical Validity Check.
    Checks if at least one lag has p < 0.01 (Bonferroni-corrected).
    Reports result (pass/fail) but does NOT exit with error code.
    
    Args:
        results_df: DataFrame with 'lag' and 'p_value'.
        log_path: Path to write the validation result log.
                
    Returns:
        Dict with 'passed' (bool), 'min_p_value', 'significant_lags'.
    """
    logger.info("Starting Statistical Validity Check (T028)...")
    
    if results_df.empty:
        logger.error("No results to validate.")
        result = {
            'passed': False,
            'reason': 'No results available',
            'min_p_value': None,
            'significant_lags': []
        }
    else:
        p_values = results_df['p_value'].dropna()
        if p_values.empty:
            logger.error("No valid p-values found.")
            result = {
                'passed': False,
                'reason': 'No valid p-values',
                'min_p_value': None,
                'significant_lags': []
            }
        else:
            min_p = p_values.min()
            significant_lags = results_df[results_df['p_value'] < ALPHA_BONFERRONI]['lag'].tolist()
            
            passed = min_p < ALPHA_BONFERRONI
            
            result = {
                'passed': passed,
                'min_p_value': float(min_p),
                'significant_lags': significant_lags,
                'threshold': ALPHA_BONFERRONI
            }
            
            status_str = "PASSED" if passed else "FAILED"
            logger.info(f"Validity Check {status_str}: Min p-value = {min_p:.6f}, Threshold = {ALPHA_BONFERRONI:.4f}")
            if passed:
                logger.info(f"Significant lags at Bonferroni level: {significant_lags}")
    
    # Write to log file
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'w') as f:
        f.write(f"Statistical Validity Check (T028) - {datetime.now().isoformat()}\n")
        f.write(f"Threshold (Bonferroni): {ALPHA_BONFERRONI}\n")
        f.write(f"Result: {'PASSED' if result['passed'] else 'FAILED'}\n")
        if result.get('min_p_value') is not None:
            f.write(f"Minimum p-value observed: {result['min_p_value']:.6f}\n")
        if result.get('significant_lags'):
            f.write(f"Significant lags: {result['significant_lags']}\n")
        else:
            f.write("Significant lags: None\n")
        
    return result

def main():
    """
    Main execution function for User Story 3 Analysis.
    Orchestrates loading, Granger sweep, sensitivity, and validity check.
    """
    logger.info("Starting Analysis Pipeline (T025-T028)...")
    
    # Paths
    input_path = "data/processed/aligned_timeseries.csv"
    granger_output_path = "data/processed/granger_results.csv"
    validity_log_path = "data/reports/validation_result.log"
    
    # 1. Load Data
    try:
        df = load_processed_data(input_path)
        logger.info(f"Loaded {len(df)} rows from {input_path}")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)
    
    # 2. Run Granger Causality Fixed Sweep (T026)
    try:
        granger_results = run_granger_causality_fixed_sweep(df)
        save_results(granger_results, granger_output_path)
    except Exception as e:
        logger.error(f"Granger causality test failed: {e}")
        sys.exit(1)
    
    # 3. Sensitivity Analysis (T027)
    try:
        sensitivity = perform_sensitivity_analysis(granger_results)
        # Save sensitivity results to a JSON file for the report
        sens_path = "data/processed/sensitivity_analysis.json"
        os.makedirs(os.path.dirname(sens_path), exist_ok=True)
        with open(sens_path, 'w') as f:
            json.dump(sensitivity, f, indent=2)
        logger.info(f"Sensitivity analysis saved to {sens_path}")
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        # Continue even if this fails, as per "proceed regardless" logic, but log error
    
    # 4. Statistical Validity Check (T028)
    try:
        validity_result = statistical_validity_check(granger_results, validity_log_path)
        logger.info(f"Validity check completed. Passed: {validity_result['passed']}")
        
        # Save validity result to JSON for report generation
        validity_path = "data/processed/validity_check.json"
        with open(validity_path, 'w') as f:
            json.dump(validity_result, f, indent=2)
            
    except Exception as e:
        logger.error(f"Validity check failed: {e}")
        # Do not exit, as per spec: "Do not exit with an error code if the condition fails"
        # But unexpected exceptions should be logged.
    
    logger.info("Analysis Pipeline completed successfully.")

if __name__ == "__main__":
    main()
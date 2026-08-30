"""
code/06_fit_gls_with_r2.py

Implements Fixed-Effects GLS fitting with Variance Explained (ΔR²) calculation.

This module extends the original GLS fitting logic to:
1. Fit the full model: Y ~ weighted_ΔPeakSignal + Covariates
2. Fit the reduced model: Y ~ Covariates (null model)
3. Calculate ΔR² = R²_full - R²_reduced
4. Perform Likelihood-Ratio Test (LRT)
5. Apply Benjamini-Hochberg FDR correction
6. Output results including β₁, p-value, q-value, and ΔR²

Input: 
  - data/processed/cre_features.tsv (from T015 output)
Output:
  - data/processed/gls_results.csv (includes β₁, p-value, q-value, ΔR²)
"""
import os
import sys
import argparse
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/gls_fitting.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_cre_features(input_path: str) -> pd.DataFrame:
    """
    Load the CRE features dataframe from T015 output.
    
    Expected columns:
      - cre_id: CRE identifier
      - stress: Stress condition
      - tf: Transcription factor
      - weighted_delta_signal: Weighted ΔPeakSignal
      - log2fc: log2 fold change
      - beta1: Previously calculated beta (if any)
      - q_value: Previously calculated q-value (if any)
      - ... other covariates
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path, sep='\t')
    logger.info(f"Loaded {len(df)} CREs from {input_path}")
    
    # Validate required columns
    required_cols = ['cre_id', 'stress', 'weighted_delta_signal', 'log2fc']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    return df

def fit_gls_model(df: pd.DataFrame, stress_condition: str, 
                  covariates: Optional[List[str]] = None) -> Dict:
    """
    Fit Fixed-Effects GLS model for a specific stress condition.
    
    Model: Y ~ weighted_ΔPeakSignal + Covariates
    
    Returns:
      Dictionary containing model results, parameters, and statistics.
    """
    stress_df = df[df['stress'] == stress_condition].copy()
    
    if len(stress_df) == 0:
        logger.warning(f"No data for stress condition: {stress_condition}")
        return None
    
    # Define outcome and predictor
    y = stress_df['log2fc'].values
    X_signal = stress_df['weighted_delta_signal'].values.reshape(-1, 1)
    
    # Prepare covariates
    X_covariates = np.ones((len(stress_df), 1))  # Intercept
    if covariates:
        for cov in covariates:
            if cov in stress_df.columns:
                X_covariates = np.hstack([X_covariates, stress_df[cov].values.reshape(-1, 1)])
            else:
                logger.warning(f"Covariate {cov} not found in data, skipping")
    
    X = np.hstack([X_covariates, X_signal])
    
    # Fit full model (with signal)
    try:
        full_model = sm.GLS(y, X)
        full_results = full_model.fit()
    except Exception as e:
        logger.error(f"Failed to fit full model for {stress_condition}: {e}")
        return None
    
    # Fit reduced model (without signal)
    try:
        reduced_model = sm.GLS(y, X_covariates)
        reduced_results = reduced_model.fit()
    except Exception as e:
        logger.error(f"Failed to fit reduced model for {stress_condition}: {e}")
        return None
    
    # Extract parameters
    # The coefficient for weighted_delta_signal is at index: len(covariates) + 1 (including intercept)
    signal_idx = len(X_covariates[0])
    beta1 = full_results.params[signal_idx]
    beta1_se = full_results.bse[signal_idx]
    p_value = full_results.pvalues[signal_idx]
    
    # Calculate R² for both models
    # R² = 1 - (SS_res / SS_tot)
    y_mean = np.mean(y)
    ss_tot = np.sum((y - y_mean) ** 2)
    
    ss_res_full = np.sum(full_results.resid ** 2)
    ss_res_reduced = np.sum(reduced_results.resid ** 2)
    
    r2_full = 1 - (ss_res_full / ss_tot) if ss_tot > 0 else 0
    r2_reduced = 1 - (ss_res_reduced / ss_tot) if ss_tot > 0 else 0
    delta_r2 = r2_full - r2_reduced
    
    # Likelihood-Ratio Test
    # LRT statistic = 2 * (logLik_full - logLik_reduced)
    # For GLS, we can use the residual sum of squares approximation
    # LRT ~ χ²(df_diff) where df_diff = 1 (one additional parameter)
    log_likelihood_full = -0.5 * len(y) * (np.log(2 * np.pi) + np.log(ss_res_full / len(y)) + 1)
    log_likelihood_reduced = -0.5 * len(y) * (np.log(2 * np.pi) + np.log(ss_res_reduced / len(y)) + 1)
    
    lrt_stat = 2 * (log_likelihood_full - log_likelihood_reduced)
    lrt_p_value = 1 - stats.chi2.cdf(lrt_stat, df=1)
    
    return {
        'stress': stress_condition,
        'n_samples': len(stress_df),
        'beta1': beta1,
        'beta1_se': beta1_se,
        'p_value': p_value,
        'r2_full': r2_full,
        'r2_reduced': r2_reduced,
        'delta_r2': delta_r2,
        'lrt_statistic': lrt_stat,
        'lrt_p_value': lrt_p_value,
        'full_model': full_results,
        'reduced_model': reduced_results
    }

def apply_fdr_correction(results: List[Dict]) -> List[Dict]:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.
    """
    if not results:
        return results
    
    p_values = [r['p_value'] for r in results]
    _, q_values, _, _ = multipletests(p_values, method='fdr_bh')
    
    for i, result in enumerate(results):
        result['q_value'] = q_values[i]
    
    return results

def write_results(results: List[Dict], output_path: str):
    """
    Write GLS results to CSV file.
    """
    if not results:
        logger.warning("No results to write")
        return
    
    # Flatten results for CSV
    rows = []
    for r in results:
        row = {
            'stress': r['stress'],
            'n_samples': r['n_samples'],
            'beta1': r['beta1'],
            'beta1_se': r['beta1_se'],
            'p_value': r['p_value'],
            'r2_full': r['r2_full'],
            'r2_reduced': r['r2_reduced'],
            'delta_r2': r['delta_r2'],
            'lrt_statistic': r['lrt_statistic'],
            'lrt_p_value': r['lrt_p_value'],
            'q_value': r['q_value']
        }
        rows.append(row)
    
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    logger.info(f"Wrote {len(df)} results to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Fit GLS models and calculate variance explained (ΔR²)')
    parser.add_argument('--input', type=str, required=True, 
                        help='Input TSV file with CRE features (from T015)')
    parser.add_argument('--output', type=str, required=True, 
                        help='Output CSV file with GLS results')
    parser.add_argument('--covariates', type=str, default=None,
                        help='Comma-separated list of covariates to include')
    
    args = parser.parse_args()
    
    # Load data
    df = load_cre_features(args.input)
    
    # Get unique stress conditions
    stress_conditions = df['stress'].unique()
    logger.info(f"Processing {len(stress_conditions)} stress conditions: {stress_conditions}")
    
    # Parse covariates
    covariates = None
    if args.covariates:
        covariates = [c.strip() for c in args.covariates.split(',')]
    
    # Fit models for each stress condition
    results = []
    for stress in stress_conditions:
        logger.info(f"Fitting model for stress condition: {stress}")
        result = fit_gls_model(df, stress, covariates)
        if result:
            results.append(result)
    
    if not results:
        logger.error("No models were successfully fitted")
        sys.exit(1)
    
    # Apply FDR correction
    results = apply_fdr_correction(results)
    
    # Write results
    write_results(results, args.output)
    
    # Print summary
    logger.info("=== GLS Fitting Summary ===")
    for r in results:
        logger.info(f"Stress: {r['stress']}, "
                    f"β₁: {r['beta1']:.4f} ± {r['beta1_se']:.4f}, "
                    f"p: {r['p_value']:.4g}, "
                    f"q: {r['q_value']:.4g}, "
                    f"ΔR²: {r['delta_r2']:.4f}")
    
    logger.info("GLS fitting complete")

if __name__ == '__main__':
    main()

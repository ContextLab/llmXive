"""
Bootstrap Correction and FDR Adjustment Script (T021)

This script implements bootstrap resampling for 95% confidence intervals,
applies FDR correction for multiple comparisons, and generates the final
Correlation Result output with region_type fields.

Design Choice: Uses Newey-West standard errors for robust inference per plan.md.
"""
import os
import sys
import logging
import json
from pathlib import Path
import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.sandwich_covariance import cov_hac1
from statsmodels.regression.linear_model import OLS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BOOTSTRAP_ITERATIONS = 1000
RANDOM_SEED = 42
FDR_METHOD = 'fdr_bh'  # Benjamini-Hochberg
CONFIDENCE_LEVEL = 0.95

def load_merged_data(input_path: str) -> pd.DataFrame:
    """
    Load the merged monthly dataset.
    Expects columns: 'date', 'grace_anomaly', 'ar_intensity', 'region_type' (optional)
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    
    # Ensure numeric columns
    required_cols = ['grace_anomaly', 'ar_intensity']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Drop rows with NaN in required columns
    initial_count = len(df)
    df = df.dropna(subset=required_cols)
    if len(df) < initial_count:
        logger.warning(f"Dropped {initial_count - len(df)} rows with NaN values")
    
    # Default region_type if not present
    if 'region_type' not in df.columns:
        df['region_type'] = 'target'
        logger.info("Added default 'target' region_type column")
    
    return df

def compute_pearson_correlation(x: np.ndarray, y: np.ndarray) -> float:
    """Compute Pearson correlation coefficient."""
    if len(x) != len(y) or len(x) == 0:
        return np.nan
    return np.corrcoef(x, y)[0, 1]

def bootstrap_confidence_interval(
    x: np.ndarray, 
    y: np.ndarray, 
    n_iterations: int = BOOTSTRAP_ITERATIONS, 
    seed: int = RANDOM_SEED
) -> tuple:
    """
    Perform bootstrap resampling to compute 95% confidence intervals.
    
    Returns: (mean_corr, lower_ci, upper_ci)
    """
    np.random.seed(seed)
    n = len(x)
    if n == 0:
        return np.nan, np.nan, np.nan
    
    bootstrap_corrs = []
    for _ in range(n_iterations):
        # Resample with replacement
        indices = np.random.choice(n, size=n, replace=True)
        x_resampled = x[indices]
        y_resampled = y[indices]
        
        corr = compute_pearson_correlation(x_resampled, y_resampled)
        if not np.isnan(corr):
            bootstrap_corrs.append(corr)
    
    if len(bootstrap_corrs) == 0:
        return np.nan, np.nan, np.nan
    
    mean_corr = np.mean(bootstrap_corrs)
    lower_ci = np.percentile(bootstrap_corrs, (1 - CONFIDENCE_LEVEL) / 2 * 100)
    upper_ci = np.percentile(bootstrap_corrs, (1 + CONFIDENCE_LEVEL) / 2 * 100)
    
    return mean_corr, lower_ci, upper_ci

def apply_newey_west_correction(x: np.ndarray, y: np.ndarray) -> tuple:
    """
    Apply Newey-West standard errors for robust inference.
    Returns the OLS coefficient, standard error, and p-value.
    """
    if len(x) != len(y) or len(x) < 2:
        return np.nan, np.nan, np.nan
    
    # Prepare data for OLS (intercept + slope)
    X = np.column_stack([np.ones(len(x)), x])
    y_vec = y
    
    try:
        model = OLS(y_vec, X)
        results = model.fit(cov_type='HAC', cov_kwds={'maxlags': 1})
        
        # We are interested in the slope coefficient (index 1)
        coef = results.params[1]
        std_err = results.bse[1]
        p_value = results.pvalues[1]
        
        return coef, std_err, p_value
    except Exception as e:
        logger.warning(f"Newey-West correction failed: {e}")
        return np.nan, np.nan, np.nan

def analyze_correlation_with_bootstrap(
    grace_data: np.ndarray, 
    ar_data: np.ndarray,
    region_type: str = 'target'
) -> dict:
    """
    Analyze correlation with bootstrap resampling and Newey-West correction.
    
    Returns a dictionary with correlation statistics.
    """
    # Bootstrap CI
    mean_corr, lower_ci, upper_ci = bootstrap_confidence_interval(
        grace_data, ar_data, n_iterations=BOOTSTRAP_ITERATIONS, seed=RANDOM_SEED
    )
    
    # Newey-West robust inference
    coef, std_err, p_value = apply_newey_west_correction(grace_data, ar_data)
    
    # If Newey-West fails, fall back to standard Pearson p-value for informational use
    if np.isnan(p_value):
        if len(grace_data) > 2:
            from scipy import stats
            _, p_value = stats.pearsonr(grace_data, ar_data)
        else:
            p_value = np.nan
    
    # Significance flag (informational only, NOT a pre-specified success criterion)
    significance_flag = p_value < 0.05 if not np.isnan(p_value) else False
    
    return {
        'region_type': region_type,
        'correlation_coefficient': float(mean_corr) if not np.isnan(mean_corr) else None,
        'ci_lower': float(lower_ci) if not np.isnan(lower_ci) else None,
        'ci_upper': float(upper_ci) if not np.isnan(upper_ci) else None,
        'newey_west_coef': float(coef) if not np.isnan(coef) else None,
        'newey_west_std_err': float(std_err) if not np.isnan(std_err) else None,
        'p_value': float(p_value) if not np.isnan(p_value) else None,
        'significance_flag': significance_flag,
        'bootstrap_iterations': BOOTSTRAP_ITERATIONS,
        'sample_size': len(grace_data)
    }

def apply_fdr_correction(results_list: list) -> list:
    """
    Apply FDR (Benjamini-Hochberg) correction to a list of p-values.
    
    Returns the list of results with 'fdr_corrected_p_value' and 'fdr_significant' added.
    """
    p_values = [r['p_value'] for r in results_list if r['p_value'] is not None]
    
    if len(p_values) == 0:
        logger.warning("No valid p-values for FDR correction")
        return results_list
    
    # Perform FDR correction
    reject, pvals_corrected, _, _ = multipletests(
        p_values, 
        alpha=0.05, 
        method=FDR_METHOD, 
        returnsorted=False
    )
    
    # Map corrected values back to results
    p_value_idx = 0
    for i, result in enumerate(results_list):
        if result['p_value'] is not None:
            result['fdr_corrected_p_value'] = float(pvals_corrected[p_value_idx])
            result['fdr_significant'] = bool(reject[p_value_idx])
            p_value_idx += 1
        else:
            result['fdr_corrected_p_value'] = None
            result['fdr_significant'] = False
    
    return results_list

def save_results(results: list, output_path: str):
    """Save results to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved {len(results)} results to {output_path}")

def main():
    """Main entry point for the bootstrap correction script."""
    # Default paths
    input_path = os.environ.get('MERGED_DATA_PATH', 'data/processed/merged_monthly.csv')
    output_path = os.environ.get('OUTPUT_PATH', 'data/processed/correlation_results.json')
    
    logger.info(f"Starting bootstrap correction analysis")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    try:
        # Load data
        df = load_merged_data(input_path)
        
        # Group by region_type if multiple regions exist
        if 'region_type' in df.columns:
            groups = df.groupby('region_type')
        else:
            groups = [('target', df)]
        
        results = []
        
        for region_type, group_df in groups:
            logger.info(f"Processing region: {region_type}")
            
            grace_data = group_df['grace_anomaly'].values
            ar_data = group_df['ar_intensity'].values
            
            # Analyze correlation
            result = analyze_correlation_with_bootstrap(
                grace_data, ar_data, region_type=region_type
            )
            results.append(result)
        
        # Apply FDR correction across all results
        if len(results) > 1:
            logger.info(f"Applying FDR correction to {len(results)} results")
            results = apply_fdr_correction(results)
        
        # Save results
        save_results(results, output_path)
        
        # Print summary
        logger.info("Analysis Summary:")
        for res in results:
            logger.info(f"  Region: {res['region_type']}")
            logger.info(f"    Correlation: {res['correlation_coefficient']:.4f}")
            logger.info(f"    95% CI: [{res['ci_lower']:.4f}, {res['ci_upper']:.4f}]")
            logger.info(f"    FDR Significant: {res['fdr_significant']}")
            logger.info(f"    (Note: p < 0.05 is informational only)")
        
        logger.info("Bootstrap correction completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"Data file error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
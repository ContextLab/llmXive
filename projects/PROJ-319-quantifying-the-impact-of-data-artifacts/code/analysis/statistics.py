"""
Statistical analysis module for quantifying artifact-induced bias.

This module implements regression analysis linking artifact magnitude (noise/saturation)
to parameter deviation (bias) with appropriate statistical corrections.
"""

import csv
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
from scipy import stats

from code.config import get_project_root

logger = logging.getLogger(__name__)

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values from statistical tests.
        alpha: Significance level (default 0.05).
        
    Returns:
        Tuple of (adjusted_p_values, significant_flags) where significant_flags
        indicates whether each adjusted p-value is below alpha.
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return [], []
    
    # Bonferroni correction: multiply p-values by number of tests, cap at 1.0
    adjusted_p_values = [min(p * n_tests, 1.0) for p in p_values]
    significant_flags = [p < alpha for p in adjusted_p_values]
    
    return adjusted_p_values, significant_flags

def run_noise_regression(
    noise_data_path: Optional[str] = None,
    output_path: Optional[str] = None,
    alpha: float = 0.05
) -> List[Dict[str, Any]]:
    """
    Perform linear regression linking noise sigma to ellipticity bias.
    
    Reads noise sweep results from data/processed/noise_trend_report.csv (or specified path),
    performs linear regression for each noise level, applies Bonferroni correction,
    and outputs statistics to data/processed/noise_stats.csv.
    
    Args:
        noise_data_path: Path to noise trend report CSV. Defaults to 
            'data/processed/noise_trend_report.csv'.
        output_path: Path to output stats CSV. Defaults to 
            'data/processed/noise_stats.csv'.
        alpha: Significance level for hypothesis testing.
        
    Returns:
        List of dictionaries containing regression results for each sigma level.
        
    Schema:
        {
            "sigma": float,
            "mean_bias": float,
            "p_value": float (Bonferroni-adjusted),
            "significant": bool,
            "slope": float
        }
        
    Raises:
        FileNotFoundError: If input data file does not exist.
        ValueError: If input data is malformed or empty.
    """
    project_root = get_project_root()
    
    if noise_data_path is None:
        noise_data_path = project_root / "data" / "processed" / "noise_trend_report.csv"
    else:
        noise_data_path = Path(noise_data_path)
        
    if output_path is None:
        output_path = project_root / "data" / "processed" / "noise_stats.csv"
    else:
        output_path = Path(output_path)
    
    if not noise_data_path.exists():
        raise FileNotFoundError(
            f"Noise trend report not found at {noise_data_path}. "
            "Ensure T014 (noise injection) has completed successfully."
        )
    
    logger.info(f"Reading noise trend data from {noise_data_path}")
    
    # Read noise trend data
    # Expected schema: sigma, mean_bias, std_bias, n_samples
    data = []
    with open(noise_data_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                data.append({
                    'sigma': float(row['sigma']),
                    'mean_bias': float(row['mean_bias']),
                    'std_bias': float(row.get('std_bias', 0.0)),
                    'n_samples': int(row.get('n_samples', 0))
                })
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping malformed row in {noise_data_path}: {e}")
                continue
    
    if len(data) == 0:
        raise ValueError(f"No valid data rows found in {noise_data_path}")
    
    logger.info(f"Processing {len(data)} noise levels")
    
    # Prepare data for regression
    sigmas = [d['sigma'] for d in data]
    mean_biases = [d['mean_bias'] for d in data]
    
    # Perform linear regression: bias = slope * sigma + intercept
    # We expect a positive slope if noise increases bias
    slope, intercept, r_value, p_value_raw, std_err = stats.linregress(sigmas, mean_biases)
    
    logger.info(f"Linear regression results: slope={slope:.6f}, intercept={intercept:.6f}, "
               f"r_squared={r_value**2:.4f}, raw_p_value={p_value_raw:.6f}")
    
    # For each sigma level, we also want to test if the bias is significantly different from zero
    # We'll perform a t-test for each level against zero bias
    p_values = []
    for d in data:
        if d['n_samples'] < 2:
            # Cannot compute t-test with n < 2
            p_values.append(1.0)
            continue
        
        # Simulate t-test: we need individual measurements, but we only have mean and std
        # We'll use the mean and std to compute a t-statistic against zero
        # t = (mean - 0) / (std / sqrt(n))
        t_stat = d['mean_bias'] / (d['std_bias'] / np.sqrt(d['n_samples']))
        # Two-tailed p-value
        p_val = 2 * (1 - stats.t.cdf(abs(t_stat), df=d['n_samples'] - 1))
        p_values.append(p_val)
    
    # Apply Bonferroni correction
    adjusted_p_values, significant_flags = apply_bonferroni_correction(p_values, alpha)
    
    # Build results
    results = []
    for i, d in enumerate(data):
        results.append({
            'sigma': d['sigma'],
            'mean_bias': d['mean_bias'],
            'p_value': adjusted_p_values[i],
            'significant': significant_flags[i],
            'slope': slope  # Global slope from regression
        })
    
    # Write output CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['sigma', 'mean_bias', 'p_value', 'significant', 'slope']
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Wrote noise regression statistics to {output_path}")
    logger.info(f"Bonferroni-corrected significance threshold: alpha/n = {alpha}/{len(data)} = {alpha/len(data):.4f}")
    
    # Summary
    significant_count = sum(1 for r in results if r['significant'])
    logger.info(f"Significant results: {significant_count}/{len(data)} noise levels")
    
    if slope > 0:
        logger.info("Positive slope indicates noise increases ellipticity bias (as expected)")
    elif slope < 0:
        logger.warning("Negative slope suggests noise decreases ellipticity bias (unexpected)")
    else:
        logger.warning("Zero slope suggests no linear relationship between noise and bias")
    
    return results

def run_saturation_regression(
    saturation_data_path: Optional[str] = None,
    output_path: Optional[str] = None,
    alpha: float = 0.05
) -> List[Dict[str, Any]]:
    """
    Perform linear regression linking saturation fraction to asymmetry bias.
    
    Reads saturation sweep results from data/processed/saturation_sweep.csv (or specified path),
    performs linear regression for each saturation level, applies Bonferroni correction,
    and outputs statistics to data/processed/saturation_stats.csv.
    
    Args:
        saturation_data_path: Path to saturation sweep CSV. Defaults to 
            'data/processed/saturation_sweep.csv'.
        output_path: Path to output stats CSV. Defaults to 
            'data/processed/saturation_stats.csv'.
        alpha: Significance level for hypothesis testing.
        
    Returns:
        List of dictionaries containing regression results for each saturation level.
        
    Schema:
        {
            "saturation_fraction": float,
            "mean_bias": float,
            "p_value": float (Bonferroni-adjusted),
            "significant": bool,
            "slope": float
        }
        
    Raises:
        FileNotFoundError: If input data file does not exist.
        ValueError: If input data is malformed or empty.
    """
    project_root = get_project_root()
    
    if saturation_data_path is None:
        saturation_data_path = project_root / "data" / "processed" / "saturation_sweep.csv"
    else:
        saturation_data_path = Path(saturation_data_path)
        
    if output_path is None:
        output_path = project_root / "data" / "processed" / "saturation_stats.csv"
    else:
        output_path = Path(output_path)
    
    if not saturation_data_path.exists():
        raise FileNotFoundError(
            f"Saturation sweep data not found at {saturation_data_path}. "
            "Ensure T021 (saturation injection) has completed successfully."
        )
    
    logger.info(f"Reading saturation sweep data from {saturation_data_path}")
    
    # Read saturation sweep data
    # Expected schema: saturation_fraction, asymmetry_mean, asymmetry_std, valid
    data = []
    with open(saturation_data_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip invalid entries
            if row.get('valid', 'True').lower() == 'false':
                continue
            
            try:
                data.append({
                    'saturation_fraction': float(row['saturation_fraction']),
                    'mean_bias': float(row['asymmetry_mean']),  # Using asymmetry as bias proxy
                    'std_bias': float(row.get('asymmetry_std', 0.0)),
                    'n_samples': int(row.get('n_samples', 0))
                })
            except (KeyError, ValueError) as e:
                logger.warning(f"Skipping malformed row in {saturation_data_path}: {e}")
                continue
    
    if len(data) == 0:
        raise ValueError(f"No valid data rows found in {saturation_data_path}")
    
    logger.info(f"Processing {len(data)} saturation levels")
    
    # Prepare data for regression
    sat_fractions = [d['saturation_fraction'] for d in data]
    mean_biases = [d['mean_bias'] for d in data]
    
    # Perform linear regression: bias = slope * saturation + intercept
    slope, intercept, r_value, p_value_raw, std_err = stats.linregress(sat_fractions, mean_biases)
    
    logger.info(f"Linear regression results: slope={slope:.6f}, intercept={intercept:.6f}, "
               f"r_squared={r_value**2:.4f}, raw_p_value={p_value_raw:.6f}")
    
    # T-test for each level against zero bias
    p_values = []
    for d in data:
        if d['n_samples'] < 2:
            p_values.append(1.0)
            continue
        
        t_stat = d['mean_bias'] / (d['std_bias'] / np.sqrt(d['n_samples']))
        p_val = 2 * (1 - stats.t.cdf(abs(t_stat), df=d['n_samples'] - 1))
        p_values.append(p_val)
    
    # Apply Bonferroni correction
    adjusted_p_values, significant_flags = apply_bonferroni_correction(p_values, alpha)
    
    # Build results
    results = []
    for i, d in enumerate(data):
        results.append({
            'saturation_fraction': d['saturation_fraction'],
            'mean_bias': d['mean_bias'],
            'p_value': adjusted_p_values[i],
            'significant': significant_flags[i],
            'slope': slope
        })
    
    # Write output CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['saturation_fraction', 'mean_bias', 'p_value', 'significant', 'slope']
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Wrote saturation regression statistics to {output_path}")
    logger.info(f"Bonferroni-corrected significance threshold: alpha/n = {alpha}/{len(data)} = {alpha/len(data):.4f}")
    
    significant_count = sum(1 for r in results if r['significant'])
    logger.info(f"Significant results: {significant_count}/{len(data)} saturation levels")
    
    return results

def main():
    """
    Main entry point for running statistical regression analyses.
    
    This function runs both noise and saturation regression analyses if their
    respective input files exist.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    project_root = get_project_root()
    
    # Run noise regression
    noise_trend_path = project_root / "data" / "processed" / "noise_trend_report.csv"
    if noise_trend_path.exists():
        try:
            noise_results = run_noise_regression()
            logger.info(f"Noise regression complete. {len(noise_results)} results generated.")
        except Exception as e:
            logger.error(f"Noise regression failed: {e}")
    else:
        logger.warning(f"Noise trend report not found at {noise_trend_path}. Skipping noise regression.")
    
    # Run saturation regression
    saturation_sweep_path = project_root / "data" / "processed" / "saturation_sweep.csv"
    if saturation_sweep_path.exists():
        try:
            sat_results = run_saturation_regression()
            logger.info(f"Saturation regression complete. {len(sat_results)} results generated.")
        except Exception as e:
            logger.error(f"Saturation regression failed: {e}")
    else:
        logger.warning(f"Saturation sweep data not found at {saturation_sweep_path}. Skipping saturation regression.")
    
    logger.info("Statistical analysis complete.")

if __name__ == "__main__":
    main()
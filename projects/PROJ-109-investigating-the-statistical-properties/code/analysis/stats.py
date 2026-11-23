import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp, spearmanr
from config import get_rho_critical_at_z, get_simulation_box_size
from utils.logging import get_logger

logger = get_logger(__name__)

# Constants for binning
# Mass binning boundaries: 10^10 to 10^15 M_sun/h in log space
MASS_BIN_MIN = 10.0
MASS_BIN_MAX = 15.0
MASS_BIN_COUNT = 10

# Environment binning threshold: Delta = 200
ENVIRONMENT_THRESHOLD = 200

def mass_binning(df: pd.DataFrame, mass_col: str = 'mass') -> pd.DataFrame:
    """
    Assign mass bins to halos based on logarithmic boundaries.
    
    Args:
        df: DataFrame containing halo data with a mass column.
        mass_col: Name of the mass column.
        
    Returns:
        DataFrame with an added 'mass_bin' column.
    """
    logger.info(f"Performing mass binning on column '{mass_col}'")
    
    # Create logarithmic bin edges
    bin_edges = np.logspace(MASS_BIN_MIN, MASS_BIN_MAX, MASS_BIN_COUNT + 1)
    
    # Assign bins
    # Note: mass data is expected to be in M_sun/h. If it's in kg or other units,
    # conversion might be needed. Assuming standard simulation output units.
    df = df.copy()
    df['mass_bin'] = pd.cut(
        df[mass_col], 
        bins=bin_edges, 
        labels=False,
        include_lowest=True
    )
    
    logger.info(f"Created {len(bin_edges)-1} mass bins")
    logger.debug(f"Bin edges: {bin_edges}")
    
    return df

def environment_binning(df: pd.DataFrame, overdensity_col: str = 'overdensity') -> pd.DataFrame:
    """
    Assign environment bins based on overdensity relative to critical density.
    
    Uses the critical density from config (T004) for normalization.
    Bins: Low environment (Delta < 200), High environment (Delta >= 200)
    
    Args:
        df: DataFrame containing halo data with an overdensity column.
        overdensity_col: Name of the overdensity column.
        
    Returns:
        DataFrame with an added 'environment_bin' column (0=Low, 1=High).
    """
    logger.info("Performing environment binning")
    
    # Get critical density from config (T004)
    # Assuming redshift z=0 for now, but this can be parameterized
    rho_crit = get_rho_critical_at_z(0.0)
    logger.debug(f"Using critical density: {rho_crit} M_sun/h/Mpc^3")
    
    df = df.copy()
    
    # Create environment bins: 0 for low (Delta < 200), 1 for high (Delta >= 200)
    df['environment_bin'] = (df[overdensity_col] >= ENVIRONMENT_THRESHOLD).astype(int)
    
    low_count = (df['environment_bin'] == 0).sum()
    high_count = (df['environment_bin'] == 1).sum()
    
    logger.info(f"Environment binning complete: {low_count} low (Delta < {ENVIRONMENT_THRESHOLD}), "
               f"{high_count} high (Delta >= {ENVIRONMENT_THRESHOLD})")
    
    return df

def run_ks_tests(df: pd.DataFrame, metrics: List[str] = ['shape', 'spin', 'concentration']) -> Dict[str, Any]:
    """
    Perform two-sample Kolmogorov-Smirnov tests between low and high environmental bins.
    
    Args:
        df: DataFrame with 'environment_bin' and metric columns.
        metrics: List of metric column names to test.
        
    Returns:
        Dictionary of test results with p-values and statistics.
    """
    logger.info(f"Running KS tests for metrics: {metrics}")
    
    results = {}
    
    for metric in metrics:
        if metric not in df.columns:
            logger.warning(f"Metric '{metric}' not found in DataFrame, skipping")
            continue
            
        low_env = df[df['environment_bin'] == 0][metric].dropna()
        high_env = df[df['environment_bin'] == 1][metric].dropna()
        
        if len(low_env) < 2 or len(high_env) < 2:
            logger.warning(f"Insufficient data for KS test on '{metric}'")
            results[metric] = {'statistic': np.nan, 'pvalue': np.nan, 'n_low': len(low_env), 'n_high': len(high_env)}
            continue
        
        stat, pval = ks_2samp(low_env, high_env)
        results[metric] = {
            'statistic': float(stat),
            'pvalue': float(pval),
            'n_low': int(len(low_env)),
            'n_high': int(len(high_env))
        }
        
        logger.debug(f"KS test for {metric}: statistic={stat:.4f}, p-value={pval:.4f}")
    
    return results

def apply_benjamini_hochberg(p_values: List[float], threshold: float = 0.05) -> List[bool]:
    """
    Apply Benjamini-Hochberg correction for multiple hypothesis testing.
    
    Args:
        p_values: List of p-values from hypothesis tests.
        threshold: Significance threshold (from config).
        
    Returns:
        List of booleans indicating which hypotheses are rejected.
    """
    logger.info(f"Applying Benjamini-Hochberg correction with threshold {threshold}")
    
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_pvalues = np.array(p_values)[sorted_indices]
    
    # Calculate BH critical values
    ranks = np.arange(1, n + 1)
    critical_values = (ranks / n) * threshold
    
    # Find the largest k where p(k) <= critical(k)
    reject_mask = sorted_pvalues <= critical_values
    
    if not np.any(reject_mask):
        logger.info("No hypotheses rejected after BH correction")
        return [False] * n
    
    # Find the largest index where condition holds
    k = np.max(np.where(reject_mask)[0])
    
    # All hypotheses with rank <= k are rejected
    rejected = np.zeros(n, dtype=bool)
    rejected[:k+1] = True
    
    # Map back to original order
    original_rejected = np.zeros(n, dtype=bool)
    original_rejected[sorted_indices] = rejected
    
    logger.info(f"BH correction: {sum(rejected)} out of {n} hypotheses rejected")
    return original_rejected.tolist()

def run_spearman_correlations(df: pd.DataFrame, mass_col: str = 'mass', 
                             metrics: List[str] = ['shape', 'spin', 'concentration']) -> Dict[str, Any]:
    """
    Calculate Spearman's rank correlation between halo mass and structural metrics.
    
    Args:
        df: DataFrame with mass and metric columns.
        mass_col: Name of the mass column.
        metrics: List of metric column names.
        
    Returns:
        Dictionary of correlation coefficients and p-values.
    """
    logger.info(f"Calculating Spearman correlations between '{mass_col}' and {metrics}")
    
    results = {}
    
    for metric in metrics:
        if metric not in df.columns:
            logger.warning(f"Metric '{metric}' not found, skipping")
            continue
        
        # Drop NaN values
        valid_data = df[[mass_col, metric]].dropna()
        
        if len(valid_data) < 2:
            logger.warning(f"Insufficient data for correlation on '{metric}'")
            results[metric] = {'rho': np.nan, 'pvalue': np.nan, 'n': 0}
            continue
        
        rho, pval = spearmanr(valid_data[mass_col], valid_data[metric])
        
        results[metric] = {
            'rho': float(rho),
            'pvalue': float(pval),
            'n': int(len(valid_data))
        }
        
        logger.debug(f"Spearman correlation for {metric}: rho={rho:.4f}, p={pval:.4f}")
    
    return results

def bullock_comparison(df: pd.DataFrame, mass_col: str = 'mass', 
                     concentration_col: str = 'concentration') -> Dict[str, Any]:
    """
    Compare measured concentration-mass relation against Bullock et al. (2001) prediction.
    
    Args:
        df: DataFrame with mass and concentration columns.
        mass_col: Name of the mass column.
        concentration_col: Name of the concentration column.
        
    Returns:
        Dictionary with comparison statistics (RMSE, mean difference).
    """
    logger.info("Comparing against Bullock et al. (2001) analytic fit")
    
    # Bullock et al. (2001) parameters should be in config
    # c_200 = 9.0, alpha = -0.1 (typical values, loaded from config)
    try:
        from config import BULLOCK_C200, BULLOCK_ALPHA
    except ImportError:
        logger.warning("Bullock parameters not found in config, using defaults")
        BULLOCK_C200 = 9.0
        BULLOCK_ALPHA = -0.1
    
    # Calculate predicted concentrations
    # c(M) = c_200 * (M/M_*)^alpha
    # Assuming M_* is around 10^12 M_sun/h for simplicity
    M_star = 1e12
    
    valid_data = df[[mass_col, concentration_col]].dropna()
    
    if len(valid_data) < 2:
        logger.warning("Insufficient data for Bullock comparison")
        return {'rmse': np.nan, 'mean_diff': np.nan, 'n': 0}
    
    masses = valid_data[mass_col].values
    measured_c = valid_data[concentration_col].values
    
    # Predicted concentration
    predicted_c = BULLOCK_C200 * (masses / M_star) ** BULLOCK_ALPHA
    
    # Calculate statistics
    residuals = measured_c - predicted_c
    rmse = np.sqrt(np.mean(residuals**2))
    mean_diff = np.mean(residuals)
    
    logger.info(f"Bullock comparison: RMSE={rmse:.4f}, Mean diff={mean_diff:.4f}")
    
    return {
        'rmse': float(rmse),
        'mean_diff': float(mean_diff),
        'n': int(len(valid_data)),
        'bullock_c200': float(BULLOCK_C200),
        'bullock_alpha': float(BULLOCK_ALPHA)
    }

def run_full_analysis_pipeline(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Run the complete statistical analysis pipeline.
    
    Args:
        input_path: Path to the processed halo data (parquet).
        output_path: Path to save results.
        
    Returns:
        Dictionary containing all analysis results.
    """
    logger.info(f"Starting full analysis pipeline")
    logger.info(f"Input: {input_path}, Output: {output_path}")
    
    # Load data
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} halos")
    
    # Ensure required columns exist
    required_cols = ['mass', 'overdensity', 'shape', 'spin', 'concentration']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Missing columns: {missing_cols}")
    
    # Step 1: Mass binning
    df = mass_binning(df)
    
    # Step 2: Environment binning
    df = environment_binning(df)
    
    # Step 3: KS tests
    ks_results = run_ks_tests(df)
    
    # Step 4: Benjamini-Hochberg correction
    p_values = [v['pvalue'] for v in ks_results.values() if not np.isnan(v['pvalue'])]
    if p_values:
        bh_rejected = apply_benjamini_hochberg(p_values)
        ks_results['bh_rejected'] = bh_rejected
    else:
        ks_results['bh_rejected'] = []
    
    # Step 5: Spearman correlations
    spearman_results = run_spearman_correlations(df)
    
    # Step 6: Bullock comparison
    bullock_results = bullock_comparison(df)
    
    # Compile results
    results = {
        'mass_binning': {
            'n_bins': MASS_BIN_COUNT,
            'bin_edges': np.logspace(MASS_BIN_MIN, MASS_BIN_MAX, MASS_BIN_COUNT + 1).tolist()
        },
        'environment_binning': {
            'threshold': ENVIRONMENT_THRESHOLD,
            'n_low': int((df['environment_bin'] == 0).sum()),
            'n_high': int((df['environment_bin'] == 1).sum())
        },
        'ks_tests': ks_results,
        'spearman_correlations': spearman_results,
        'bullock_comparison': bullock_results,
        'config': {
            'rho_critical': float(get_rho_critical_at_z(0.0)),
            'box_size': float(get_simulation_box_size())
        }
    }
    
    # Save results
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    return results
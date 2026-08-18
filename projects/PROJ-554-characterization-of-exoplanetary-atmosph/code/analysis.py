import logging
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from config import get_config
import scipy.stats as stats
import os
from pathlib import Path
from utils import setup_logging, CensoredDataError

# Ensure logging is configured if not already
if not logging.getLogger().handlers:
    setup_logging()

logger = logging.getLogger(__name__)

def load_analysis_data(metadata_path: str = None, retrieval_path: str = None) -> pd.DataFrame:
    """
    Load and merge metadata and retrieval results for analysis.
    
    Args:
        metadata_path: Path to metadata CSV (default: data/processed/metadata.csv)
        retrieval_path: Path to retrieval results CSV (default: data/processed/retrieval_results.csv)
        
    Returns:
        Merged DataFrame with all necessary columns for analysis
    """
    config = get_config()
    
    if metadata_path is None:
        metadata_path = str(config['paths']['processed'] / 'metadata.csv')
    if retrieval_path is None:
        retrieval_path = str(config['paths']['processed'] / 'retrieval_results.csv')
        
    logger.info(f"Loading metadata from {metadata_path}")
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    metadata_df = pd.read_csv(metadata_path)
    
    logger.info(f"Loading retrieval results from {retrieval_path}")
    if not os.path.exists(retrieval_path):
        raise FileNotFoundError(f"Retrieval results file not found: {retrieval_path}")
    retrieval_df = pd.read_csv(retrieval_path)
    
    # Merge on planet_name
    merged_df = pd.merge(metadata_df, retrieval_df, on='planet_name', how='inner')
    
    logger.info(f"Loaded {len(merged_df)} records for analysis")
    return merged_df

def quality_control_filter(df: pd.DataFrame, snr_threshold: float = 3.0, 
                           resolution_threshold: float = 50.0) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Apply quality control filter to flag low SNR spectra and include them as censored values.
    
    This function implements FR-002 by:
    1. Flagging spectra with SNR < threshold as censored (upper limits)
    2. Flagging spectra with Resolution < threshold as censored
    3. Returning the filtered dataset with censorship indicators
    
    Args:
        df: DataFrame containing metadata (SNR, Resolution) and retrieval results
        snr_threshold: Minimum acceptable SNR (default: 3.0)
        resolution_threshold: Minimum acceptable spectral resolution (default: 50)
        
    Returns:
        Tuple of (filtered_df, censorship_mask) where:
            - filtered_df: Original DataFrame with censorship indicator columns
            - censorship_mask: Boolean Series where True indicates censored/upper limit
    """
    logger.info(f"Applying quality control filter: SNR >= {snr_threshold}, R >= {resolution_threshold}")
    
    # Validate required columns exist
    required_cols = ['snr', 'resolution', 'water_mixing_ratio']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for QC filter: {missing_cols}")
    
    # Create censorship mask based on SNR and Resolution
    # A spectrum is censored if it fails EITHER criterion
    snr_censored = df['snr'] < snr_threshold
    res_censored = df['resolution'] < resolution_threshold
    censorship_mask = snr_censored | res_censored
    
    # Create a copy to avoid SettingWithCopyWarning
    filtered_df = df.copy()
    
    # Add censorship indicator column
    filtered_df['is_censored'] = censorship_mask
    
    # Log statistics
    total = len(filtered_df)
    censored_count = censorship_mask.sum()
    uncensored_count = total - censored_count
    
    logger.info(f"QC Filter Results: {censored_count}/{total} spectra flagged as censored")
    logger.info(f"  - SNR < {snr_threshold}: {snr_censored.sum()}")
    logger.info(f"  - Resolution < {resolution_threshold}: {res_censored.sum()}")
    logger.info(f"  - Overlap (both): {(snr_censored & res_censored).sum()}")
    logger.info(f"  - Remaining for direct analysis: {uncensored_count}")
    
    # Log specific planets that are censored (for audit trail)
    if censored_count > 0:
        censored_planets = filtered_df.loc[censorship_mask, 'planet_name'].tolist()
        logger.debug(f"Censored planets: {censored_planets[:10]}{'...' if len(censored_planets) > 10 else ''}")
    
    return filtered_df, censorship_mask

def compute_censored_kendall_tau(df: pd.DataFrame, censorship_mask: pd.Series = None) -> Dict[str, Any]:
    """
    Compute Kendall's tau correlation for censored data.
    
    Args:
        df: DataFrame with water mixing ratio and temperature
        censorship_mask: Boolean mask indicating censored values (optional)
        
    Returns:
        Dictionary with tau coefficient, p-value, and sample info
    """
    # If no censorship mask provided, assume no censoring
    if censorship_mask is None:
        censorship_mask = pd.Series([False] * len(df), index=df.index)
    
    logger.info("Computing censored Kendall's tau correlation")
    
    # Prepare data for scikit-survival
    # We need: y (water mixing ratio), event (1=observed, 0=censored), x (temperature)
    y = df['water_mixing_ratio'].values
    event = (~censorship_mask).values.astype(int)  # 1 if observed, 0 if censored
    x = df['temperature'].values
    
    # Use scikit-survival's censored Kendall's tau
    try:
        from sksurv.nonparametric import kendall_tau
        tau, p_value = kendall_tau(event, y, x)
        
        result = {
            'tau': float(tau),
            'p_value': float(p_value),
            'n_observed': int(event.sum()),
            'n_censored': int((~event).sum()),
            'n_total': len(df),
            'method': 'censored_kendall_tau'
        }
        
        logger.info(f"Kendall's tau = {tau:.4f}, p-value = {p_value:.4f}")
        logger.info(f"  Observed: {result['n_observed']}, Censored: {result['n_censored']}")
        
        return result
        
    except ImportError:
        logger.warning("sksurv not available, falling back to standard Kendall's tau (ignoring censoring)")
        # Fallback: standard Kendall's tau on observed values only
        observed_mask = ~censorship_mask
        if observed_mask.sum() < 2:
            raise ValueError("Not enough observed values for correlation")
        
        tau, p_value = stats.kendalltau(x[observed_mask], y[observed_mask])
        
        return {
            'tau': float(tau),
            'p_value': float(p_value),
            'n_observed': int(observed_mask.sum()),
            'n_censored': int(censorship_mask.sum()),
            'n_total': len(df),
            'method': 'standard_kendall_tau_observed_only',
            'note': 'Censoring not properly handled due to missing scikit-survival'
        }

def run_bootstrap_ci(df: pd.DataFrame, n_iterations: int = 1000, 
                    censorship_mask: pd.Series = None) -> Dict[str, Any]:
    """
    Run bootstrap resampling to estimate confidence intervals for correlation.
    
    Args:
        df: DataFrame with analysis data
        n_iterations: Number of bootstrap iterations
        censorship_mask: Boolean mask for censored values
        
    Returns:
        Dictionary with bootstrap results
    """
    logger.info(f"Running bootstrap with {n_iterations} iterations")
    
    if censorship_mask is None:
        censorship_mask = pd.Series([False] * len(df), index=df.index)
    
    tau_values = []
    
    for i in range(n_iterations):
        # Bootstrap sample
        indices = np.random.choice(len(df), size=len(df), replace=True)
        boot_df = df.iloc[indices]
        boot_mask = censorship_mask.iloc[indices]
        
        try:
            result = compute_censored_kendall_tau(boot_df, boot_mask)
            tau_values.append(result['tau'])
        except Exception as e:
            logger.warning(f"Bootstrap iteration {i} failed: {e}")
            continue
    
    if len(tau_values) < 10:
        raise ValueError("Too few successful bootstrap iterations")
    
    tau_array = np.array(tau_values)
    ci_lower = np.percentile(tau_array, 2.5)
    ci_upper = np.percentile(tau_array, 97.5)
    
    result = {
        'iterations': n_iterations,
        'successful_iterations': len(tau_values),
        'ci_lower': float(ci_lower),
        'ci_upper': float(ci_upper),
        'ci_width': float(ci_upper - ci_lower),
        'median_tau': float(np.median(tau_values))
    }
    
    logger.info(f"Bootstrap CI: [{ci_lower:.4f}, {ci_upper:.4f}], width = {ci_upper - ci_lower:.4f}")
    
    return result

def save_bootstrap_results(results: Dict[str, Any], output_path: str = None):
    """
    Save bootstrap results to JSON file.
    
    Args:
        results: Bootstrap results dictionary
        output_path: Path to output file (default: data/processed/bootstrap_ci.json)
    """
    config = get_config()
    if output_path is None:
        output_path = str(config['paths']['processed'] / 'bootstrap_ci.json')
        
    import json
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Bootstrap results saved to {output_path}")

def save_qc_report(filtered_df: pd.DataFrame, output_path: str = None):
    """
    Save quality control report to JSON file.
    
    Args:
        filtered_df: DataFrame with censorship indicators
        output_path: Path to output file
    """
    config = get_config()
    if output_path is None:
        output_path = str(config['paths']['processed'] / 'qc_report.json')
    
    report = {
        'total_spectra': len(filtered_df),
        'censored_count': int(filtered_df['is_censored'].sum()),
        'uncensored_count': int((~filtered_df['is_censored']).sum()),
        'censored_planets': filtered_df.loc[filtered_df['is_censored'], 'planet_name'].tolist(),
        'snr_threshold': 3.0,
        'resolution_threshold': 50.0
    }
    
    import json
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"QC report saved to {output_path}")

def main():
    """
    Main entry point for analysis pipeline with quality control filtering.
    """
    logger.info("Starting analysis pipeline with quality control filtering")
    
    try:
        # Load data
        df = load_analysis_data()
        
        # Apply quality control filter
        filtered_df, censorship_mask = quality_control_filter(df)
        
        # Save QC report
        save_qc_report(filtered_df)
        
        # Compute censored Kendall's tau
        tau_result = compute_censored_kendall_tau(filtered_df, censorship_mask)
        
        # Run bootstrap
        bootstrap_result = run_bootstrap_ci(filtered_df, n_iterations=1000, 
                                            censorship_mask=censorship_mask)
        
        # Save bootstrap results
        save_bootstrap_results(bootstrap_result)
        
        logger.info("Analysis pipeline completed successfully")
        return {
            'tau': tau_result,
            'bootstrap': bootstrap_result,
            'qc_report': {
                'total': len(filtered_df),
                'censored': int(censorship_mask.sum()),
                'uncensored': int((~censorship_mask).sum())
            }
        }
        
    except Exception as e:
        logger.error(f"Analysis pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
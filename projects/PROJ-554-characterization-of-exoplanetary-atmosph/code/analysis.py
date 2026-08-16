import logging
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from config import get_config
import scipy.stats as stats
import json
import os

# Importing scikit-survival for censored data handling (T025a)
try:
    from sksurv.nonparametric import kendall_tau
except ImportError:
    raise ImportError("sksurv is required for T025b/T025c. Install via: pip install scikit-survival")

# Importing data models if needed for type hints or validation
# (Assuming data_models is available as per API surface)
try:
    from data_models import RetrievalResult
except ImportError:
    pass

logger = logging.getLogger(__name__)

def load_analysis_data() -> pd.DataFrame:
    """
    Loads the processed retrieval results and metadata.
    Merges data from T012 (metadata.csv) and T020 (retrieval_results.csv).
    """
    config = get_config()
    processed_dir = config['paths']['processed']
    
    meta_path = os.path.join(processed_dir, 'metadata.csv')
    retrieval_path = os.path.join(processed_dir, 'retrieval_results.csv')

    if not os.path.exists(meta_path) or not os.path.exists(retrieval_path):
        raise FileNotFoundError(
            f"Required data files not found. Expected: {meta_path}, {retrieval_path}. "
            "Ensure T012 and T020 have been completed."
        )

    df_meta = pd.read_csv(meta_path)
    df_retrieval = pd.read_csv(retrieval_path)

    # Merge on planet_name
    df = pd.merge(df_meta, df_retrieval, on='planet_name', how='inner')
    
    # Filter out rows where water mixing ratio is missing or invalid
    # We need to handle upper limits (is_upper_limit=True) as censored data
    logger.info(f"Loaded {len(df)} combined records for analysis.")
    return df

def compute_censored_kendall_tau(df: pd.DataFrame) -> Tuple[float, float]:
    """
    Computes Kendall's tau for censored data using scikit-survival.
    T025b Implementation.
    
    Args:
        df: DataFrame containing 'water_mixing_ratio' and 'is_upper_limit'.
            
    Returns:
        Tuple of (tau, p_value)
    """
    # Prepare survival array for scikit-survival
    # In survival analysis terms:
    # - 'event' is True if we have a detection (not an upper limit)
    # - 'time' is the observed value (log10 mixing ratio)
    
    # Ensure boolean column exists
    if 'is_upper_limit' not in df.columns:
        raise ValueError("Column 'is_upper_limit' missing from data.")
    
    # scikit-survival expects: event=True means the event occurred (detection here)
    # Our data: is_upper_limit=True means we only have a limit (no detection event)
    # So event = ~is_upper_limit
    events = ~df['is_upper_limit'].astype(bool)
    times = df['water_mixing_ratio'].values
    
    # Filter out NaNs in times
    valid_mask = ~np.isnan(times)
    if np.sum(~valid_mask) > 0:
        logger.warning(f"Removed {np.sum(~valid_mask)} rows with NaN mixing ratios.")
        
    times = times[valid_mask]
    events = events[valid_mask]
    
    if len(times) < 2:
        logger.warning("Insufficient data points for Kendall's tau calculation.")
        return 0.0, 1.0

    try:
        # Calculate tau
        tau, p_value = kendall_tau(times, events)
        logger.info(f"Computed Censored Kendall's Tau: {tau:.4f} (p={p_value:.4f})")
        return tau, p_value
    except Exception as e:
        logger.error(f"Error computing Kendall's tau: {e}")
        raise

def run_bootstrap_ci(
    df: pd.DataFrame, 
    n_iterations: int = 1000, 
    random_seed: int = 42
) -> Dict[str, Any]:
    """
    Implements bootstrap resampling to estimate confidence intervals for Kendall's tau.
    T025c Implementation.
    
    Args:
        df: DataFrame with censored data.
        n_iterations: Number of bootstrap iterations.
        random_seed: Seed for reproducibility.
        
    Returns:
        Dictionary with {iterations, ci_lower, ci_upper, tau_estimate}
    """
    logger.info(f"Starting bootstrap resampling with {n_iterations} iterations...")
    np.random.seed(random_seed)
    
    taus = []
    n = len(df)
    
    # Progress logging
    step = max(1, n_iterations // 10)
    
    for i in range(n_iterations):
        # Resample rows with replacement
        # We must resample the entire row to maintain the pairing of value and censor status
        indices = np.random.choice(n, size=n, replace=True)
        sample_df = df.iloc[indices]
        
        # Compute tau for this sample
        try:
            tau, _ = compute_censored_kendall_tau(sample_df)
            taus.append(tau)
        except Exception as e:
            # If a sample fails (e.g., all censored or all same value), skip or handle
            logger.debug(f"Bootstrap iteration {i} failed: {e}")
            continue
        
        if (i + 1) % step == 0:
            logger.debug(f"Bootstrap progress: {i+1}/{n_iterations}")

    if not taus:
        raise RuntimeError("Bootstrap failed: No valid tau values computed.")

    taus = np.array(taus)
    ci_lower = np.percentile(taus, 2.5)
    ci_upper = np.percentile(taus, 97.5)
    tau_estimate = np.median(taus) # Or mean, but median is robust for skewed distributions

    result = {
        "iterations": n_iterations,
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "tau_estimate": float(tau_estimate),
        "sample_size": n
    }
    
    logger.info(f"Bootstrap CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
    return result

def save_bootstrap_results(result: Dict[str, Any], output_path: str) -> None:
    """
    Saves bootstrap results to JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    logger.info(f"Saved bootstrap results to {output_path}")

def main():
    """
    Main entry point for T025c: Bootstrap Resampling.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting T025c: Bootstrap Resampling for Confidence Intervals")
    
    config = get_config()
    output_path = os.path.join(config['paths']['processed'], 'bootstrap_ci.json')
    
    # Load data
    df = load_analysis_data()
    
    # Run bootstrap
    result = run_bootstrap_ci(df, n_iterations=1000)
    
    # Save results
    save_bootstrap_results(result, output_path)
    
    logger.info("T025c completed successfully.")
    return result

if __name__ == "__main__":
    main()

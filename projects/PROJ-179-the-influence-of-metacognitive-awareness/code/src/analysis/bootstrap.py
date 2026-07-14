"""
Bootstrap analysis for correlation confidence intervals.

This script performs bootstrap resampling to generate 95% confidence intervals
for the correlation between metacognitive awareness and reality testing accuracy.
"""
import json
import logging
import os
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DERIVED_DIR = DATA_DIR / "derived"
RESULTS_DIR = DATA_DIR / "results"

def log_info(message):
    """Log info message."""
    logger.info(message)

def log_error(message):
    """Log error message."""
    logger.error(message)

def load_correlation_data():
    """Load trial data for correlation analysis."""
    file_path = DERIVED_DIR / "trial_data.csv"
    if not file_path.exists():
        log_error(f"Trial data not found at {file_path}")
        return None
    
    try:
        df = pd.read_csv(file_path)
        log_info(f"Loaded {len(df)} trials for bootstrap analysis")
        return df
    except Exception as e:
        log_error(f"Error loading trial data: {e}")
        return None

def compute_correlation_statistic(df):
    """Compute correlation statistic for a sample."""
    if df is None or len(df) < 10:
        return np.nan
    
    # Ensure required columns
    if 'confidence_rating' not in df.columns or 'source_label' not in df.columns:
        return np.nan
    
    df['accuracy'] = (df['source_label'] == df['participant_response']).astype(int)
    
    if 'accuracy' not in df.columns or 'confidence_rating' not in df.columns:
        return np.nan
    
    # Compute Pearson correlation
    corr, _ = stats.pearsonr(df['confidence_rating'], df['accuracy'])
    return corr if not np.isnan(corr) else np.nan

def run_bootstrap_analysis(df, n_resamples=1000, max_runtime_hours=5.5):
    """Run bootstrap analysis with runtime monitoring."""
    start_time = time.time()
    
    log_info(f"Starting bootstrap analysis with {n_resamples} resamples...")
    
    bootstrapped_corrs = []
    interval_checks = 100  # Check runtime every N resamples
    
    for i in range(n_resamples):
        # Sample with replacement
        sample = df.sample(n=len(df), replace=True, random_state=np.random.randint(0, 10000))
        corr = compute_correlation_statistic(sample)
        if not np.isnan(corr):
            bootstrapped_corrs.append(corr)
        
        # Check runtime periodically
        if (i + 1) % interval_checks == 0:
            elapsed_hours = (time.time() - start_time) / 3600
            if elapsed_hours > max_runtime_hours:
                log_warning(f"Runtime limit detected ({elapsed_hours:.1f}h > {max_runtime_hours}h), reducing bootstrap count")
                # Save current state and exit
                final_count = len(bootstrapped_corrs)
                break
    else:
        final_count = len(bootstrapped_corrs)
    
    log_info(f"Completed {final_count} bootstrap resamples")
    
    if len(bootstrapped_corrs) == 0:
        log_error("Bootstrap failed to produce valid correlations")
        return None
    
    # Compute statistics
    mean_corr = np.mean(bootstrapped_corrs)
    ci_lower = np.percentile(bootstrapped_corrs, 2.5)
    ci_upper = np.percentile(bootstrapped_corrs, 97.5)
    
    # Compute original correlation
    original_corr = compute_correlation_statistic(df)
    
    # Compute p-value (two-tailed)
    if original_corr is not None and not np.isnan(original_corr):
        # Simplified p-value calculation
        z_score = original_corr / (np.std(bootstrapped_corrs) / np.sqrt(len(bootstrapped_corrs)))
        p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
    else:
        p_value = 1.0
    
    return {
        'r': original_corr,
        'p': p_value,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'bootstrap_count': final_count,
        'mean_bootstrapped_r': mean_corr
    }

def write_results(results):
    """Write bootstrap results to file."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Write bootstrap config
    config_path = RESULTS_DIR / "bootstrap_config.json"
    with open(config_path, 'w') as f:
        json.dump({
            'bootstrap_count': results['bootstrap_count'],
            'confidence_level': 0.95
        }, f, indent=2)
    log_info(f"Bootstrap config written to: {config_path}")
    
    # Write results
    results_path = RESULTS_DIR / "primary_analysis.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    log_info(f"Bootstrap results written to: {results_path}")

def main():
    """Main function."""
    log_info("Starting bootstrap analysis (T015)...")
    
    # Load data
    df = load_correlation_data()
    if df is None:
        return 1
    
    # Run bootstrap analysis
    results = run_bootstrap_analysis(df, n_resamples=1000)
    if results is None:
        return 1
    
    # Write results
    write_results(results)
    
    log_info(f"Bootstrap analysis complete. r={results['r']:.3f}, p={results['p']:.3f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())

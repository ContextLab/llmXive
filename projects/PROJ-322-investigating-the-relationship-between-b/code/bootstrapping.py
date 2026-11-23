"""
Bootstrapping module for contingency analysis when sample size is small (n < 20).
Implements non-parametric bootstrapping to generate confidence intervals for correlation metrics.
"""
import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd

from config import is_synthetic, get_config
from statistical_model import load_preprocessed_data
from memory_monitor import check_and_warn, get_current_ram_gb

# Configure logging
logger = logging.getLogger(__name__)

def load_preprocessed_data() -> pd.DataFrame:
    """
    Load preprocessed data from the results directory.
    Falls back to synthetic data if in methodology validation mode and real data is unavailable.
    
    Returns:
        pd.DataFrame: DataFrame containing subject data with graph metrics and cognitive scores.
    """
    config = get_config()
    data_path = Path(config.get('processed_data_path', 'data/processed'))
    metrics_file = data_path / 'metrics.json'
    
    if not metrics_file.exists():
        # Try to load from statistical model output if available
        model_results_path = Path('data/results/model_results.json')
        if model_results_path.exists():
            with open(model_results_path, 'r') as f:
                data = json.load(f)
            if 'data' in data:
                return pd.DataFrame(data['data'])
        
        # If in synthetic mode and no real data, generate synthetic
        if is_synthetic():
            logger.info("Real data not found. Generating synthetic data for bootstrapping.")
            from synthetic_data import generate_dataset
            dataset = generate_dataset(n_subjects=15, n_timepoints=2)
            return pd.DataFrame(dataset)
        else:
            raise FileNotFoundError(f"Preprocessed data not found at {metrics_file}")
    
    with open(metrics_file, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return pd.DataFrame(data)
    elif 'data' in data:
        return pd.DataFrame(data['data'])
    else:
        raise ValueError(f"Unexpected data format in {metrics_file}")

def calculate_correlation(df: pd.DataFrame, x_col: str, y_col: str) -> float:
    """
    Calculate Pearson correlation between two columns.
    
    Args:
        df: DataFrame containing the data.
        x_col: Name of the first column.
        y_col: Name of the second column.
        
    Returns:
        float: Pearson correlation coefficient.
    """
    if x_col not in df.columns or y_col not in df.columns:
        raise ValueError(f"Columns {x_col} or {y_col} not found in DataFrame. Available: {df.columns.tolist()}")
    
    # Drop rows with NaN in either column
    clean_df = df[[x_col, y_col]].dropna()
    
    if len(clean_df) < 3:
        raise ValueError(f"Insufficient data points for correlation calculation: {len(clean_df)}")
    
    return clean_df[x_col].corr(clean_df[y_col])

def bootstrap_correlation(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    n_iterations: int = 1000,
    confidence_level: float = 0.95,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform non-parametric bootstrapping to estimate confidence intervals for correlation.
    
    Args:
        df: DataFrame containing the data.
        x_col: Name of the first column.
        y_col: Name of the second column.
        n_iterations: Number of bootstrap iterations (default 1000).
        confidence_level: Confidence level for CI (default 0.95).
        random_state: Random seed for reproducibility.
        
    Returns:
        Dict: Dictionary containing observed correlation, bootstrap mean, CI bounds, and iterations.
    """
    if random_state is not None:
        np.random.seed(random_state)
    
    # Calculate observed correlation
    observed_corr = calculate_correlation(df, x_col, y_col)
    
    # Bootstrap iterations
    bootstrap_correlations = []
    n_samples = len(df)
    
    for i in range(n_iterations):
        # Check memory periodically
        if i % 100 == 0:
            check_and_warn()
            if get_current_ram_gb() > 5.5:
                logger.warning("Memory usage high during bootstrapping. Proceeding with caution.")
        
        # Resample with replacement
        resampled_indices = np.random.randint(0, n_samples, size=n_samples)
        resampled_df = df.iloc[resampled_indices]
        
        # Calculate correlation on resampled data
        try:
            corr = calculate_correlation(resampled_df, x_col, y_col)
            bootstrap_correlations.append(corr)
        except ValueError as e:
            # Skip iterations with insufficient data
            logger.debug(f"Skipping iteration {i}: {e}")
            continue
    
    if len(bootstrap_correlations) == 0:
        raise RuntimeError("No valid bootstrap correlations calculated.")
    
    # Calculate statistics
    bootstrap_mean = np.mean(bootstrap_correlations)
    bootstrap_std = np.std(bootstrap_correlations)
    
    # Calculate confidence intervals
    alpha = 1 - confidence_level
    lower_percentile = alpha / 2
    upper_percentile = 1 - alpha / 2
    ci_lower = np.percentile(bootstrap_correlations, lower_percentile * 100)
    ci_upper = np.percentile(bootstrap_correlations, upper_percentile * 100)
    
    return {
        'observed_correlation': float(observed_corr),
        'bootstrap_mean': float(bootstrap_mean),
        'bootstrap_std': float(bootstrap_std),
        'ci_lower': float(ci_lower),
        'ci_upper': float(ci_upper),
        'confidence_level': confidence_level,
        'n_iterations': n_iterations,
        'valid_iterations': len(bootstrap_correlations),
        'sample_size': n_samples
    }

def run_full_bootstrapping(
    n_iterations: int = 1000,
    confidence_level: float = 0.95,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run the full bootstrapping analysis.
    
    This function:
    1. Loads preprocessed data
    2. Checks sample size (n < 20 triggers bootstrapping)
    3. Performs bootstrapping on graph metrics vs cognitive score correlation
    4. Returns results dictionary
    
    Args:
        n_iterations: Number of bootstrap iterations (default 1000).
        confidence_level: Confidence level for CI (default 0.95).
        random_state: Random seed for reproducibility.
        
    Returns:
        Dict: Complete bootstrapping results including metadata.
    """
    logger.info("Starting full bootstrapping analysis...")
    start_time = time.time()
    
    # Load data
    df = load_preprocessed_data()
    n_subjects = len(df)
    
    logger.info(f"Loaded {n_subjects} subjects for bootstrapping analysis.")
    
    # Contingency check: if n < 20, switch to non-parametric bootstrapping
    if n_subjects < 20:
        logger.info(f"Sample size ({n_subjects}) is less than 20. Switching to non-parametric bootstrapping.")
        is_small_sample = True
    else:
        logger.info(f"Sample size ({n_subjects}) is sufficient. Bootstrapping performed for robustness.")
        is_small_sample = False
    
    # Determine columns to analyze
    # Look for efficiency metrics and cognitive scores
    efficiency_cols = [col for col in df.columns if 'efficiency' in col.lower() or 'global_eff' in col.lower()]
    cognitive_cols = [col for col in df.columns if 'cognitive' in col.lower() or 'score' in col.lower() or 'recovery' in col.lower()]
    
    if not efficiency_cols or not cognitive_cols:
        # Fallback to known column names from synthetic data
        efficiency_cols = ['global_efficiency']
        cognitive_cols = ['cognitive_score']
        
        # Verify these columns exist
        for col in efficiency_cols + cognitive_cols:
            if col not in df.columns:
                raise ValueError(f"Required column '{col}' not found in data. Available: {df.columns.tolist()}")
    
    # Use first available efficiency and cognitive columns
    x_col = efficiency_cols[0]
    y_col = cognitive_cols[0]
    
    logger.info(f"Analyzing correlation between '{x_col}' and '{y_col}'")
    
    # Perform bootstrapping
    boot_results = bootstrap_correlation(
        df=df,
        x_col=x_col,
        y_col=y_col,
        n_iterations=n_iterations,
        confidence_level=confidence_level,
        random_state=random_state
    )
    
    elapsed_time = time.time() - start_time
    
    # Compile full results
    results = {
        'analysis_type': 'bootstrapping',
        'triggered_by_small_sample': is_small_sample,
        'sample_size': n_subjects,
        'threshold_n': 20,
        'x_variable': x_col,
        'y_variable': y_col,
        'correlation_results': boot_results,
        'runtime_seconds': elapsed_time,
        'methodology_validation_mode': is_synthetic(),
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    logger.info(f"Bootstrapping completed in {elapsed_time:.2f} seconds.")
    logger.info(f"Observed correlation: {boot_results['observed_correlation']:.4f}")
    logger.info(f"95% CI: [{boot_results['ci_lower']:.4f}, {boot_results['ci_upper']:.4f}]")
    
    return results

def save_results(results: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Save bootstrapping results to JSON file.
    
    Args:
        results: Dictionary containing bootstrapping results.
        output_path: Optional path for output file. Defaults to 'data/results/bootstrapped_ci.json'.
    
    Returns:
        str: Path to the saved file.
    """
    if output_path is None:
        output_path = 'data/results/bootstrapped_ci.json'
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_file}")
    return str(output_file)

def main():
    """
    Main entry point for bootstrapping analysis.
    """
    logger.info("=" * 60)
    logger.info("Starting Bootstrapping Analysis (T016)")
    logger.info("=" * 60)
    
    try:
        # Run full bootstrapping with default parameters
        results = run_full_bootstrapping(
            n_iterations=1000,
            confidence_level=0.95,
            random_state=42
        )
        
        # Save results
        output_path = save_results(results)
        
        logger.info("Bootstrapping analysis completed successfully.")
        return 0
      
    except Exception as e:
        logger.error(f"Bootstrapping analysis failed: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())

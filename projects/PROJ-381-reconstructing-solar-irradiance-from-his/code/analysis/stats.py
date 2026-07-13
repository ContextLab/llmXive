"""
Statistical analysis module for solar irradiance reconstruction.

Implements bootstrap resampling for variance comparison across historical minima
(Maunder, Dalton, Modern) as per FR-005 and Constitution Principle VII.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
import pandas as pd
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BOOTSTRAP_ITERATIONS: int = 1000
RANDOM_SEED: int = 42

# Historical minima definitions (approximate years)
# Maunder Minimum: ~1645-1715
# Dalton Minimum: ~1790-1830
# Modern Minimum: ~1996-2008 (Solar Cycle 23/24 transition)
MINIMA_PERIODS = {
    "Maunder": (1645, 1715),
    "Dalton": (1790, 1830),
    "Modern": (1996, 2008)
}

def load_reconstruction_data(data_path: Path) -> pd.DataFrame:
    """
    Load the reconstructed TSI data from parquet file.
    
    Args:
        data_path: Path to the reconstruction parquet file
        
    Returns:
        DataFrame with TSI reconstruction data
    """
    logger.info(f"Loading reconstruction data from {data_path}")
    if not data_path.exists():
        raise FileNotFoundError(f"Reconstruction file not found: {data_path}")
    
    df = pd.read_parquet(data_path)
    
    # Ensure required columns exist
    required_cols = ['year', 'tsi', 'tsi_lower', 'tsi_upper']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in reconstruction data: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} records with columns: {list(df.columns)}")
    return df

def filter_by_period(df: pd.DataFrame, period_name: str) -> pd.DataFrame:
    """
    Filter the DataFrame to a specific historical minimum period.
    
    Args:
        df: Full reconstruction DataFrame
        period_name: Name of the period ('Maunder', 'Dalton', 'Modern')
        
    Returns:
        Filtered DataFrame for the specified period
    """
    if period_name not in MINIMA_PERIODS:
        raise ValueError(f"Unknown period: {period_name}. Must be one of {list(MINIMA_PERIODS.keys())}")
    
    start_year, end_year = MINIMA_PERIODS[period_name]
    filtered = df[(df['year'] >= start_year) & (df['year'] <= end_year)]
    logger.info(f"Filtered to {period_name} period ({start_year}-{end_year}): {len(filtered)} records")
    return filtered

def bootstrap_variance_estimation(
    tsi_values: np.ndarray,
    n_iterations: int = BOOTSTRAP_ITERATIONS,
    random_seed: int = RANDOM_SEED
) -> Dict[str, Any]:
    """
    Perform bootstrap resampling to estimate variance and confidence intervals.
    
    Args:
        tsi_values: Array of TSI values for a period
        n_iterations: Number of bootstrap iterations (default: 1000)
        random_seed: Random seed for reproducibility
        
    Returns:
        Dictionary with bootstrap statistics
    """
    if len(tsi_values) == 0:
        return {
            "mean": np.nan,
            "std": np.nan,
            "variance": np.nan,
            "ci_lower_95": np.nan,
            "ci_upper_95": np.nan,
            "n_samples": 0,
            "n_iterations": n_iterations
        }
    
    np.random.seed(random_seed)
    n_samples = len(tsi_values)
    
    # Bootstrap resampling
    bootstrap_means = []
    bootstrap_vars = []
    
    for i in range(n_iterations):
        # Resample with replacement
        resample_indices = np.random.choice(n_samples, size=n_samples, replace=True)
        resample = tsi_values[resample_indices]
        
        bootstrap_means.append(np.mean(resample))
        bootstrap_vars.append(np.var(resample))
    
    bootstrap_means = np.array(bootstrap_means)
    bootstrap_vars = np.array(bootstrap_vars)
    
    # Calculate statistics
    mean_estimate = np.mean(tsi_values)
    std_estimate = np.std(tsi_values, ddof=1)
    variance_estimate = np.var(tsi_values, ddof=1)
    
    # 95% Confidence Intervals
    ci_lower_95 = np.percentile(bootstrap_means, 2.5)
    ci_upper_95 = np.percentile(bootstrap_means, 97.5)
    
    return {
        "mean": float(mean_estimate),
        "std": float(std_estimate),
        "variance": float(variance_estimate),
        "ci_lower_95": float(ci_lower_95),
        "ci_upper_95": float(ci_upper_95),
        "n_samples": n_samples,
        "n_iterations": n_iterations,
        "bootstrap_std_mean": float(np.std(bootstrap_means)),
        "bootstrap_mean_variance": float(np.mean(bootstrap_vars))
    }

def compare_variance_across_periods(
    df: pd.DataFrame,
    periods: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Compare variance across multiple historical periods using bootstrap.
    
    Args:
        df: Full reconstruction DataFrame
        periods: List of period names to compare (default: all defined periods)
        
    Returns:
        Dictionary with variance comparison results
    """
    if periods is None:
        periods = list(MINIMA_PERIODS.keys())
    
    results = {}
    period_data = {}
    
    for period_name in periods:
        filtered_df = filter_by_period(df, period_name)
        if len(filtered_df) == 0:
            logger.warning(f"No data found for {period_name} period")
            results[period_name] = {
                "error": "No data available for this period",
                "n_samples": 0
            }
            continue
        
        tsi_values = filtered_df['tsi'].values
        period_data[period_name] = tsi_values
        
        bootstrap_stats = bootstrap_variance_estimation(
            tsi_values,
            n_iterations=BOOTSTRAP_ITERATIONS,
            random_seed=RANDOM_SEED
        )
        results[period_name] = bootstrap_stats
    
    # Pairwise comparisons
    pairwise_comparisons = []
    period_names = list(results.keys())
    
    for i in range(len(period_names)):
        for j in range(i + 1, len(period_names)):
            period_a = period_names[i]
            period_b = period_names[j]
            
            if "error" in results[period_a] or "error" in results[period_b]:
                continue
            
            var_a = results[period_a]["variance"]
            var_b = results[period_b]["variance"]
            mean_a = results[period_a]["mean"]
            mean_b = results[period_b]["mean"]
            
            # Levene's test for equality of variances
            if period_a in period_data and period_b in period_data:
                stat, p_value = stats.levene(
                    period_data[period_a],
                    period_data[period_b]
                )
            else:
                stat, p_value = np.nan, np.nan
            
            pairwise_comparisons.append({
                "period_a": period_a,
                "period_b": period_b,
                "variance_a": var_a,
                "variance_b": var_b,
                "mean_a": mean_a,
                "mean_b": mean_b,
                "variance_ratio": var_a / var_b if var_b > 0 else np.nan,
                "levene_statistic": float(stat) if not np.isnan(stat) else None,
                "levene_p_value": float(p_value) if not np.isnan(p_value) else None,
                "significant_diff": bool(p_value < 0.05) if not np.isnan(p_value) else None
            })
    
    return {
        "period_results": results,
        "pairwise_comparisons": pairwise_comparisons,
        "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
        "random_seed": RANDOM_SEED,
        "minima_definitions": MINIMA_PERIODS
    }

def run_bootstrap_analysis(
    input_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Run the complete bootstrap analysis pipeline.
    
    Args:
        input_path: Path to the reconstruction parquet file
        output_path: Path for the output JSON report
        
    Returns:
        Dictionary with analysis results
    """
    logger.info("Starting bootstrap variance analysis")
    
    # Load data
    df = load_reconstruction_data(input_path)
    
    # Run comparison across periods
    results = compare_variance_across_periods(df)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Analysis complete. Results saved to {output_path}")
    return results

def main():
    """Main entry point for the bootstrap analysis script."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    input_path = project_root / "data" / "processed" / "reconstruction_1610_2002.parquet"
    output_path = project_root / "data" / "processed" / "variance_analysis.json"
    
    try:
        results = run_bootstrap_analysis(input_path, output_path)
        print(f"Analysis complete. Output saved to: {output_path}")
        print(f"Periods analyzed: {list(results['period_results'].keys())}")
        print(f"Pairwise comparisons: {len(results['pairwise_comparisons'])}")
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
"""
Distribution Fitting Analysis Module

Implements ECDF generation, parametric distribution fitting (log-normal, Weibull),
and statistical goodness-of-fit testing using scipy.stats.
"""

import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.special import boxcox

# Add parent to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import get_config, get_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_cleaned_data() -> pd.DataFrame:
    """Load the cleaned dataset from the processed data directory."""
    config = get_config()
    data_path = get_path("cleaned_issues", config)
    
    if not Path(data_path).exists():
        raise FileNotFoundError(f"Cleaned dataset not found at {data_path}")
    
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} issues from {data_path}")
    return df

def fit_distribution(data: np.ndarray, dist_name: str) -> Dict[str, Any]:
    """
    Fit a parametric distribution to the data and return fit statistics.
    
    Args:
        data: 1D array of resolution times (must be positive)
        dist_name: Name of the distribution ('lognorm' or 'weibull_min')
        
    Returns:
        Dictionary containing parameters, KS statistic, p-value, and AIC
    """
    if dist_name not in ['lognorm', 'weibull_min']:
        raise ValueError(f"Unsupported distribution: {dist_name}")
    
    # Filter out non-positive values for fitting
    positive_data = data[data > 0]
    if len(positive_data) < 10:
        logger.warning(f"Insufficient positive data points for {dist_name} fitting")
        return {
            'distribution': dist_name,
            'status': 'failed',
            'reason': 'Insufficient positive data points'
        }
    
    try:
        # Fit the distribution
        if dist_name == 'lognorm':
            # lognorm in scipy: s is the shape parameter (sigma of underlying normal)
            # We fix loc=0 and scale to estimate shape, loc, scale
            params = stats.lognorm.fit(positive_data, floc=0)
            dist = stats.lognorm(*params)
        elif dist_name == 'weibull_min':
            # weibull_min: c is the shape parameter
            params = stats.weibull_min.fit(positive_data, floc=0)
            dist = stats.weibull_min(*params)
        
        # Kolmogorov-Smirnov test
        ks_stat, p_value = stats.kstest(positive_data, dist.cdf)
        
        # Calculate AIC
        # AIC = 2k - 2ln(L)
        # For scipy distributions, we can use logpdf to compute log-likelihood
        log_likelihood = np.sum(dist.logpdf(positive_data))
        k = len(params)  # Number of parameters
        aic = 2 * k - 2 * log_likelihood
        
        return {
            'distribution': dist_name,
            'status': 'success',
            'parameters': {
                'shape': params[0],
                'loc': params[1] if len(params) > 1 else 0.0,
                'scale': params[2] if len(params) > 2 else 1.0
            },
            'ks_statistic': float(ks_stat),
            'p_value': float(p_value),
            'aic': float(aic),
            'n_samples': len(positive_data)
        }
        
    except Exception as e:
        logger.error(f"Failed to fit {dist_name}: {str(e)}")
        return {
            'distribution': dist_name,
            'status': 'failed',
            'reason': str(e)
        }

def analyze_distributions(df: pd.DataFrame, time_column: str = 'resolution_time_hours') -> Dict[str, Any]:
    """
    Analyze the distribution of resolution times by fitting multiple parametric models.
    
    Args:
        df: DataFrame containing the cleaned issue data
        time_column: Name of the column containing resolution times
        
    Returns:
        Dictionary with fitting results for each distribution
    """
    if time_column not in df.columns:
        raise ValueError(f"Column '{time_column}' not found in dataframe")
    
    data = df[time_column].values
    logger.info(f"Fitting distributions to {len(data)} resolution time values")
    
    results = {
        'metadata': {
            'total_samples': len(data),
            'positive_samples': int(np.sum(data > 0)),
            'mean_resolution_time': float(np.mean(data[data > 0])) if np.sum(data > 0) > 0 else 0.0,
            'median_resolution_time': float(np.median(data[data > 0])) if np.sum(data > 0) > 0 else 0.0
        },
        'distributions': {}
    }
    
    # Fit log-normal
    lognorm_result = fit_distribution(data, 'lognorm')
    results['distributions']['lognorm'] = lognorm_result
    
    # Fit Weibull
    weibull_result = fit_distribution(data, 'weibull_min')
    results['distributions']['weibull_min'] = weibull_result
    
    # Determine best fit based on AIC (lower is better)
    valid_fits = [k for k, v in results['distributions'].items() if v.get('status') == 'success']
    if valid_fits:
        best_fit = min(valid_fits, key=lambda k: results['distributions'][k]['aic'])
        results['best_fit'] = {
            'distribution': best_fit,
            'aic': results['distributions'][best_fit]['aic']
        }
        logger.info(f"Best fit distribution: {best_fit} (AIC: {results['distributions'][best_fit]['aic']:.2f})")
    else:
        results['best_fit'] = None
        logger.warning("No valid distribution fits found")
    
    return results

def generate_ecdf_plot(data: np.ndarray, title: str = "Empirical CDF of Issue Resolution Times") -> plt.Figure:
    """
    Generate an ECDF plot with logarithmic x-axis.
    
    Args:
        data: 1D array of resolution times
        title: Plot title
        
    Returns:
        Matplotlib Figure object
    """
    # Filter positive data
    positive_data = data[data > 0]
    if len(positive_data) == 0:
        raise ValueError("No positive data points available for ECDF plot")
    
    # Sort data
    sorted_data = np.sort(positive_data)
    # Calculate ECDF
    ecdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
    
    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(sorted_data, ecdf, marker='.', linestyle='none', alpha=0.7, markersize=1)
    ax.set_xlabel('Resolution Time (hours)')
    ax.set_ylabel('Cumulative Probability')
    ax.set_title(title)
    ax.set_xscale('log')
    ax.grid(True, which="both", ls="-", alpha=0.2)
    
    # Add reference lines
    for p in [0.5, 0.9, 0.95]:
        idx = np.searchsorted(ecdf, p)
        if idx < len(sorted_data):
            ax.axhline(y=p, color='gray', linestyle='--', alpha=0.5)
            ax.axvline(x=sorted_data[idx], color='gray', linestyle='--', alpha=0.5)
            ax.text(sorted_data[idx] * 1.1, p, f'{int(p*100)}%', va='bottom', ha='left', fontsize=9)
    
    plt.tight_layout()
    return fig

def generate_fit_comparison_plot(data: np.ndarray, fit_results: Dict[str, Any]) -> plt.Figure:
    """
    Generate a comparison plot showing ECDF vs fitted distributions.
    
    Args:
        data: 1D array of resolution times
        fit_results: Dictionary containing distribution fit results
        
    Returns:
        Matplotlib Figure object
    """
    positive_data = data[data > 0]
    if len(positive_data) == 0:
        raise ValueError("No positive data points available for comparison plot")
    
    sorted_data = np.sort(positive_data)
    ecdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot ECDF
    ax.plot(sorted_data, ecdf, 'b.', label='Empirical CDF', alpha=0.5, markersize=1)
    
    # Plot fitted distributions
    colors = {'lognorm': 'red', 'weibull_min': 'green'}
    linestyles = {'lognorm': '-', 'weibull_min': '--'}
    
    for dist_name, result in fit_results.get('distributions', {}).items():
        if result.get('status') == 'success':
            params = result['parameters']
            if dist_name == 'lognorm':
                dist = stats.lognorm(params['shape'], loc=params['loc'], scale=params['scale'])
            elif dist_name == 'weibull_min':
                dist = stats.weibull_min(params['shape'], loc=params['loc'], scale=params['scale'])
            
            # Generate smooth curve
            x_vals = np.linspace(sorted_data.min(), sorted_data.max(), 500)
            y_vals = dist.cdf(x_vals)
            ax.plot(x_vals, y_vals, color=colors.get(dist_name, 'black'), 
                    linestyle=linestyles.get(dist_name, '-'), 
                    linewidth=2, label=f'{dist_name} fit')
    
    ax.set_xlabel('Resolution Time (hours)')
    ax.set_ylabel('Cumulative Probability')
    ax.set_title('ECDF vs Parametric Distribution Fits')
    ax.set_xscale('log')
    ax.legend(loc='lower right')
    ax.grid(True, which="both", ls="-", alpha=0.2)
    
    plt.tight_layout()
    return fig

def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save analysis results to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

def save_figures(figs: Dict[str, plt.Figure], output_dir: Path) -> None:
    """Save figures to the output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, fig in figs.items():
        path = output_dir / f"{name}.png"
        fig.savefig(path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        logger.info(f"Saved figure: {path}")

def main():
    """Main entry point for distribution fitting analysis."""
    logger.info("Starting distribution fitting analysis...")
    
    # Load data
    df = load_cleaned_data()
    
    # Analyze distributions
    results = analyze_distributions(df)
    
    # Generate figures
    data = df['resolution_time_hours'].values
    figs = {}
    
    # ECDF Plot
    try:
        figs['ecdf'] = generate_ecdf_plot(data, "Empirical CDF of Issue Resolution Times")
    except Exception as e:
        logger.error(f"Failed to generate ECDF plot: {e}")
    
    # Fit Comparison Plot
    try:
        figs['fit_comparison'] = generate_fit_comparison_plot(data, results)
    except Exception as e:
        logger.error(f"Failed to generate fit comparison plot: {e}")
    
    # Define output paths
    config = get_config()
    output_dir = get_path("figures", config)
    results_path = get_path("distribution_metrics", config)
    
    # Ensure directories exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(results_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Save figures
    if figs:
        save_figures(figs, Path(output_dir))
    
    # Save results
    save_results(results, Path(results_path))
    
    logger.info("Distribution fitting analysis completed successfully.")
    return results

if __name__ == "__main__":
    main()

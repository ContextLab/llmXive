"""
Distribution fitting and analysis module for GitHub issue resolution times.

This module handles:
1. Loading cleaned issue data
2. Fitting parametric distributions (log-normal, Weibull)
3. Analyzing distribution quality
4. Saving results and generating figures
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_DATA_PATH = "data/processed/cleaned_issues.csv"
DEFAULT_RESULTS_PATH = "data/processed/distribution_metrics.json"
DEFAULT_FIGURES_DIR = "data/figures"
LOG_MIN_VALUE = 1e-6  # Minimum value for log transformation to avoid log(0)

def load_cleaned_data(data_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the cleaned issues dataset from CSV.

    Args:
        data_path: Path to the cleaned CSV file. Defaults to DEFAULT_DATA_PATH.

    Returns:
        DataFrame containing cleaned issue data.

    Raises:
        FileNotFoundError: If the data file does not exist.
        ValueError: If required columns are missing.
    """
    if data_path is None:
        data_path = DEFAULT_DATA_PATH

    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Cleaned data file not found: {data_path}")

    logger.info(f"Loading cleaned data from {data_path}")
    df = pd.read_csv(path)

    # Verify required columns
    required_cols = ['resolution_time_hours', 'language']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    logger.info(f"Loaded {len(df)} records with columns: {list(df.columns)}")
    return df

def fit_distribution(data: np.ndarray, dist_name: str) -> Dict[str, Any]:
    """
    Fit a parametric distribution to the data.

    Args:
        data: 1D numpy array of resolution times.
        dist_name: Name of the distribution ('lognorm' or 'weibull_min').

    Returns:
        Dictionary containing fit parameters and goodness-of-fit metrics.
    """
    logger.info(f"Fitting {dist_name} distribution to data (n={len(data)})")

    # Filter non-positive values for distributions that require positive support
    valid_data = data[data > 0]
    if len(valid_data) < 10:
        logger.warning(f"Insufficient positive data points for {dist_name} fitting")
        return {
            "params": [],
            "ks_statistic": None,
            "p_value": None,
            "aic": None,
            "goodness_of_fit": "fail",
            "error": "Insufficient positive data"
        }

    try:
        if dist_name == 'lognorm':
            # Fit log-normal distribution
            # scipy.stats.lognorm uses shape (s), loc, scale
            # We fix loc=0 for standard log-normal
            shape, loc, scale = stats.lognorm.fit(valid_data, floc=0)
            dist_obj = stats.lognorm(shape, loc=loc, scale=scale)
        elif dist_name == 'weibull_min':
            # Fit Weibull minimum distribution
            # scipy.stats.weibull_min uses c, loc, scale
            c, loc, scale = stats.weibull_min.fit(valid_data, floc=0)
            dist_obj = stats.weibull_min(c, loc=loc, scale=scale)
        else:
            raise ValueError(f"Unsupported distribution: {dist_name}")

        # Kolmogorov-Smirnov test
        ks_stat, p_value = stats.kstest(valid_data, dist_obj.cdf)

        # Calculate AIC
        # AIC = 2k - 2ln(L), where k is number of parameters
        # For scipy distributions, we use the log-likelihood from the fit
        log_likelihood = np.sum(dist_obj.logpdf(valid_data))
        k = 2  # Typically 2-3 parameters depending on fit
        aic = 2 * k - 2 * log_likelihood

        # Determine goodness of fit (p > 0.05 suggests good fit)
        goodness = "pass" if p_value > 0.05 else "fail"

        logger.info(f"{dist_name} fit: KS={ks_stat:.4f}, p={p_value:.4f}, AIC={aic:.2f}")

        return {
            "params": [float(p) for p in [shape if dist_name == 'lognorm' else c, loc, scale]],
            "ks_statistic": float(ks_stat),
            "p_value": float(p_value),
            "aic": float(aic),
            "goodness_of_fit": goodness
        }

    except Exception as e:
        logger.error(f"Error fitting {dist_name}: {e}")
        return {
            "params": [],
            "ks_statistic": None,
            "p_value": None,
            "aic": None,
            "goodness_of_fit": "fail",
            "error": str(e)
        }

def analyze_distributions(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze the distribution of resolution times.

    Args:
        df: DataFrame with 'resolution_time_hours' column.

    Returns:
        Dictionary containing data statistics and distribution fit results.
    """
    data = df['resolution_time_hours'].values

    # Basic statistics
    data_stats = {
        "count": int(len(data)),
        "mean": float(np.mean(data)),
        "median": float(np.median(data)),
        "std": float(np.std(data)),
        "min": float(np.min(data)),
        "max": float(np.max(data))
    }

    # Fit distributions
    fits = {}
    distributions = ['lognorm', 'weibull_min']

    for dist_name in distributions:
        fits[dist_name] = fit_distribution(data, dist_name)

    # Determine best fit based on AIC (lower is better)
    valid_fits = {k: v for k, v in fits.items() if v.get('aic') is not None}
    if valid_fits:
        best_fit = min(valid_fits, key=lambda k: valid_fits[k]['aic'])
    else:
        best_fit = None

    result = {
        "data_stats": data_stats,
        "fits": fits,
        "best_fit": best_fit
    }

    logger.info(f"Analysis complete. Best fit: {best_fit}")
    return result

def save_results(results: Dict[str, Any], output_path: Optional[str] = None) -> None:
    """
    Save analysis results to a JSON file.

    Args:
        results: Dictionary containing analysis results.
        output_path: Path for the output JSON file. Defaults to DEFAULT_RESULTS_PATH.
    """
    if output_path is None:
        output_path = DEFAULT_RESULTS_PATH

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Results saved to {output_path}")

def generate_ecdf_plot(data: np.ndarray, output_path: Optional[str] = None) -> None:
    """
    Generate and save an ECDF plot with log-scaled x-axis.

    Args:
        data: 1D array of resolution times.
        output_path: Path to save the figure. Defaults to data/figures/ecdf.png.
    """
    if output_path is None:
        output_path = Path(DEFAULT_FIGURES_DIR) / "ecdf.png"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Filter positive values for log scale
    valid_data = data[data > 0]
    if len(valid_data) == 0:
        logger.warning("No positive data for ECDF plot")
        return

    # Calculate ECDF
    x = np.sort(valid_data)
    y = np.arange(1, len(x) + 1) / len(x)

    # Create plot
    plt.figure(figsize=(10, 6))
    plt.plot(x, y, marker='.', linestyle='none', markersize=3, alpha=0.6)
    plt.xscale('log')
    plt.xlabel('Resolution Time (hours, log scale)')
    plt.ylabel('Cumulative Probability')
    plt.title('Empirical Cumulative Distribution Function (ECDF)\nof GitHub Issue Resolution Times')
    plt.grid(True, which="both", ls="--", alpha=0.5)
    plt.tight_layout()

    plt.savefig(output_path, dpi=150)
    plt.close()

    logger.info(f"ECDF plot saved to {output_path}")

def generate_fit_comparison_plot(data: np.ndarray, fits: Dict[str, Any], output_path: Optional[str] = None) -> None:
    """
    Generate a plot comparing fitted distributions to the empirical data.

    Args:
        data: 1D array of resolution times.
        fits: Dictionary containing fit results.
        output_path: Path to save the figure. Defaults to data/figures/distribution_fits.png.
    """
    if output_path is None:
        output_path = Path(DEFAULT_FIGURES_DIR) / "distribution_fits.png"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    valid_data = data[data > 0]
    if len(valid_data) == 0:
        logger.warning("No positive data for fit comparison plot")
        return

    # Calculate ECDF
    x_ecdf = np.sort(valid_data)
    y_ecdf = np.arange(1, len(x_ecdf) + 1) / len(x_ecdf)

    # Create x values for smooth curves
    x_curve = np.linspace(np.min(valid_data), np.max(valid_data), 1000)

    plt.figure(figsize=(12, 7))

    # Plot ECDF
    plt.plot(x_ecdf, y_ecdf, 'b.', alpha=0.5, label='Empirical Data', markersize=2)

    # Plot fitted distributions
    colors = {'lognorm': 'r', 'weibull_min': 'g'}
    for dist_name, fit_result in fits.items():
        if fit_result.get('params') and fit_result['goodness_of_fit'] != 'fail':
            try:
                if dist_name == 'lognorm':
                    shape, loc, scale = fit_result['params']
                    dist_obj = stats.lognorm(shape, loc=loc, scale=scale)
                elif dist_name == 'weibull_min':
                    c, loc, scale = fit_result['params']
                    dist_obj = stats.weibull_min(c, loc=loc, scale=scale)
                else:
                    continue

                y_curve = dist_obj.cdf(x_curve)
                color = colors.get(dist_name, 'k')
                plt.plot(x_curve, y_curve, color=color, linewidth=2,
                         label=f'{dist_name} fit (p={fit_result["p_value"]:.3f})')
            except Exception as e:
                logger.warning(f"Could not plot {dist_name}: {e}")

    plt.xscale('log')
    plt.xlabel('Resolution Time (hours, log scale)')
    plt.ylabel('Cumulative Probability')
    plt.title('Distribution Fit Comparison')
    plt.legend()
    plt.grid(True, which="both", ls="--", alpha=0.5)
    plt.tight_layout()

    plt.savefig(output_path, dpi=150)
    plt.close()

    logger.info(f"Fit comparison plot saved to {output_path}")

def save_figures(df: pd.DataFrame, fits: Dict[str, Any]) -> Dict[str, str]:
    """
    Generate and save all required figures.

    Args:
        df: DataFrame with resolution time data.
        fits: Dictionary of distribution fit results.

    Returns:
        Dictionary mapping figure types to their file paths.
    """
    data = df['resolution_time_hours'].values
    figures_dir = Path(DEFAULT_FIGURES_DIR)
    figures_dir.mkdir(parents=True, exist_ok=True)

    saved_files = {}

    # ECDF Plot
    ecdf_path = figures_dir / "ecdf.png"
    generate_ecdf_plot(data, str(ecdf_path))
    saved_files['ecdf'] = str(ecdf_path)

    # Fit Comparison Plot
    fit_path = figures_dir / "distribution_fits.png"
    generate_fit_comparison_plot(data, fits, str(fit_path))
    saved_files['fit_comparison'] = str(fit_path)

    logger.info(f"Saved figures: {list(saved_files.keys())}")
    return saved_files

def main():
    """
    Main entry point for distribution analysis.
    Loads data, fits distributions, saves results and figures.
    """
    logger.info("Starting distribution analysis...")

    try:
        # Load data
        df = load_cleaned_data()

        # Analyze distributions
        results = analyze_distributions(df)

        # Save results to JSON
        save_results(results)

        # Generate and save figures
        save_figures(df, results['fits'])

        logger.info("Distribution analysis completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Data file error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
"""
Visualization module for flight delay distribution analysis.
Generates diagnostic plots including log-log survival plots and QQ-plots.
"""
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Callable
from scipy import stats
from scipy.special import ndtr

# Import from local modules
from models import get_fitted_distribution, ConvergenceError
from config import RANDOM_SEED

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate R-squared (coefficient of determination) for visualization.
    
    Args:
        y_true: Actual values
        y_pred: Predicted values
        
    Returns:
        R-squared value
    """
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    
    if ss_tot == 0:
        return 0.0
        
    return 1.0 - (ss_res / ss_tot)

def empirical_survival_function(data: np.ndarray, x_min: Optional[float] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate empirical survival function (1 - CDF) for log-log plot.
    
    Args:
        data: Array of delay values
        x_min: Minimum value to consider (tail threshold)
        
    Returns:
        Tuple of (sorted unique values, survival probabilities)
    """
    if x_min is not None:
        data = data[data >= x_min]
    
    if len(data) == 0:
        raise ValueError("No data points remain after filtering")
        
    data_sorted = np.sort(data)
    n = len(data_sorted)
    
    # Survival function: P(X > x)
    # For each unique value x, S(x) = (number of points > x) / n
    unique_vals = np.unique(data_sorted)
    survival_probs = np.array([np.sum(data_sorted > x) / n for x in unique_vals])
    
    return unique_vals, survival_probs

def plot_loglog_survival(
    data: np.ndarray,
    fitted_dists: Dict[str, Any],
    x_min: Optional[float] = None,
    output_path: Optional[Path] = None,
    title: str = "Log-Log Survival Plot: Empirical vs Fitted Distributions"
) -> Tuple[float, Dict[str, float]]:
    """
    Generate log-log survival plot comparing empirical data to fitted distributions.
    Calculates R² for visualization purposes only.
    
    Args:
        data: Array of delay values
        fitted_dists: Dictionary of fitted distributions from models.py
        x_min: Tail threshold (optional)
        output_path: Path to save the figure (optional)
        title: Plot title
        
    Returns:
        Tuple of (overall R², dict of R² per distribution)
    """
    if len(data) == 0:
        raise ValueError("Cannot plot empty data")
        
    # Set style
    sns.set_style("whitegrid")
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Calculate empirical survival function
    emp_x, emp_s = empirical_survival_function(data, x_min)
    
    # Plot empirical data
    ax.loglog(emp_x, emp_s, 'b-', linewidth=2, label='Empirical', alpha=0.7)
    
    # Calculate R² values
    r2_values = {}
    
    # Plot fitted distributions
    colors = ['r', 'g', 'm', 'c', 'orange', 'purple']
    
    for idx, (dist_name, dist_info) in enumerate(fitted_dists.items()):
        try:
            # Get distribution parameters
            dist_obj = dist_info.get('distribution')
            params = dist_info.get('params', ())
            
            if dist_obj is None:
                logger.warning(f"Skipping {dist_name}: no distribution object found")
                continue
                
            # Generate fitted survival curve
            # Use a grid of x values from min(data) to max(data)
            x_grid = np.linspace(emp_x[0], emp_x[-1], 1000)
            
            # Calculate CDF and then survival
            cdf_vals = dist_obj.cdf(x_grid, *params)
            surv_vals = 1 - cdf_vals
            
            # Filter out zero or negative survival probabilities for log plot
            valid_mask = surv_vals > 0
            if np.sum(valid_mask) < 10:
                logger.warning(f"Skipping {dist_name}: insufficient valid points for plotting")
                continue
                
            x_plot = x_grid[valid_mask]
            s_plot = surv_vals[valid_mask]
            
            # Plot
            color = colors[idx % len(colors)]
            ax.loglog(x_plot, s_plot, color=color, linewidth=1.5, 
                     label=f"{dist_name} (fit)", alpha=0.8)
            
            # Calculate R² for this distribution
            # Interpolate empirical data to match grid
            interp_emp_s = np.interp(x_plot, emp_x, emp_s, left=1.0, right=0.0)
            r2 = calculate_r2(interp_emp_s, s_plot)
            r2_values[dist_name] = r2
            
        except Exception as e:
            logger.warning(f"Error plotting {dist_name}: {e}")
            continue
    
    # Add legend and labels
    ax.set_xlabel('Delay (minutes)', fontsize=12)
    ax.set_ylabel('Survival Probability P(X > x)', fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.legend(loc='lower left', fontsize=10)
    
    # Add R² annotation
    if r2_values:
        r2_text = "\n".join([f"{name}: R² = {r2:.4f}" for name, r2 in r2_values.items()])
        ax.text(0.05, 0.95, f"R² (visualization only):\n{r2_text}",
               transform=ax.transAxes, fontsize=10, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    # Save if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Saved log-log survival plot to {output_path}")
    
    # Calculate overall R² (average of all valid distributions)
    overall_r2 = np.mean(list(r2_values.values())) if r2_values else 0.0
    
    return overall_r2, r2_values

def plot_qq_plot(
    data: np.ndarray,
    fitted_dist_name: str,
    fitted_params: Tuple,
    output_path: Optional[Path] = None,
    title: str = "Q-Q Plot: Empirical vs Fitted Distribution"
):
    """
    Generate Q-Q plot for a fitted distribution.
    
    Args:
        data: Array of delay values
        fitted_dist_name: Name of the fitted distribution
        fitted_params: Parameters of the fitted distribution
        output_path: Path to save the figure (optional)
        title: Plot title
    """
    if len(data) == 0:
        raise ValueError("Cannot plot empty data")
        
    sns.set_style("whitegrid")
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Get the distribution object
    dist_map = {
        'Exponential': stats.expon,
        'Gamma': stats.gamma,
        'Log-Normal': stats.lognorm,
        'Weibull': stats.weibull_min,
        'Pareto': stats.pareto
    }
    
    if fitted_dist_name not in dist_map:
        raise ValueError(f"Unknown distribution: {fitted_dist_name}")
        
    dist_obj = dist_map[fitted_dist_name]
    
    # Generate theoretical quantiles
    n = len(data)
    probs = (np.arange(1, n + 1) - 0.5) / n
    theoretical_quantiles = dist_obj.ppf(probs, *fitted_params)
    empirical_quantiles = np.sort(data)
    
    # Plot
    ax.scatter(theoretical_quantiles, empirical_quantiles, alpha=0.5, s=20)
    
    # Add reference line
    min_val = min(theoretical_quantiles.min(), empirical_quantiles.min())
    max_val = max(theoretical_quantiles.max(), empirical_quantiles.max())
    ax.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Reference Line')
    
    ax.set_xlabel('Theoretical Quantiles', fontsize=12)
    ax.set_ylabel('Empirical Quantiles', fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.legend()
    
    plt.tight_layout()
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Saved Q-Q plot to {output_path}")

def save_r2_results(r2_values: Dict[str, float], output_path: Path):
    """
    Save R² values to JSON file.
    
    Args:
        r2_values: Dictionary of distribution names to R² values
        output_path: Path to save the JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    result = {
        "description": "R² values for log-log survival plot (visualization only)",
        "note": "R² is calculated for visualization reporting only and is NOT used for model rejection",
        "r2_values": r2_values
    }
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Saved R² results to {output_path}")

def main():
    """
    Main function to generate visualization outputs.
    This function should be called by main.py Stage 3.
    """
    # Set random seed for reproducibility
    np.random.seed(RANDOM_SEED)
    
    # Paths
    data_path = Path("data/processed/cleaned_delays.csv")
    model_results_path = Path("data/results/model_comparison.json")
    x_min_path = Path("data/results/x_min_estimate.json")
    output_plot_path = Path("data/results/loglog_survival_plot.png")
    output_qq_path = Path("data/results/qq_plot_best_model.png")
    r2_output_path = Path("data/results/visualization_r2.json")
    
    # Check if required files exist
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        raise FileNotFoundError(f"Data file not found: {data_path}")
        
    if not model_results_path.exists():
        logger.error(f"Model results not found: {model_results_path}")
        raise FileNotFoundError(f"Model results not found: {model_results_path}")
    
    # Load data
    logger.info(f"Loading data from {data_path}")
    data = np.loadtxt(data_path, delimiter=',', skiprows=1)
    
    # Load model comparison results
    logger.info(f"Loading model results from {model_results_path}")
    with open(model_results_path, 'r') as f:
        model_results = json.load(f)
    
    # Load x_min if available
    x_min = None
    if x_min_path.exists():
        with open(x_min_path, 'r') as f:
            x_min_data = json.load(f)
            x_min = x_min_data.get('x_min')
        logger.info(f"Using x_min = {x_min}")
    
    # Reconstruct fitted distributions from model results
    # The model_comparison.json contains metrics but we need to re-fit to get distribution objects
    # We'll use the best model from the results
    
    # For now, we'll create a placeholder for fitted distributions
    # In a real implementation, this would load the actual fitted models
    fitted_dists = {}
    
    # Re-fit distributions for visualization
    from models import fit_distribution, ConvergenceError
    
    distributions_to_fit = [
        ('Exponential', stats.expon),
        ('Gamma', stats.gamma),
        ('Log-Normal', stats.lognorm),
        ('Weibull', stats.weibull_min),
        ('Pareto', stats.pareto)
    ]
    
    for name, dist_obj in distributions_to_fit:
        try:
            params, info = fit_distribution(data, dist_obj, x_min)
            fitted_dists[name] = {
                'distribution': dist_obj,
                'params': params,
                'info': info
            }
        except ConvergenceError as e:
            logger.warning(f"Failed to fit {name}: {e}")
        except Exception as e:
            logger.warning(f"Error fitting {name}: {e}")
    
    if not fitted_dists:
        logger.error("No distributions could be fitted for visualization")
        raise RuntimeError("No distributions fitted for visualization")
    
    # Generate log-log survival plot
    logger.info("Generating log-log survival plot...")
    overall_r2, r2_values = plot_loglog_survival(
        data=data,
        fitted_dists=fitted_dists,
        x_min=x_min,
        output_path=output_plot_path,
        title="Log-Log Survival Plot: Flight Delays"
    )
    
    logger.info(f"Overall R² (visualization only): {overall_r2:.4f}")
    for name, r2 in r2_values.items():
        logger.info(f"{name} R²: {r2:.4f}")
    
    # Save R² results
    save_r2_results(r2_values, r2_output_path)
    
    # Generate Q-Q plot for best model
    # Find best model based on AIC from model results
    best_model_name = model_results.get('best_model', 'Gamma')
    best_model_params = model_results.get('best_model_params', ())
    
    logger.info(f"Generating Q-Q plot for best model: {best_model_name}")
    try:
        plot_qq_plot(
            data=data,
            fitted_dist_name=best_model_name,
            fitted_params=best_model_params,
            output_path=output_qq_path,
            title=f"Q-Q Plot: {best_model_name} Fit"
        )
    except Exception as e:
        logger.warning(f"Failed to generate Q-Q plot: {e}")
    
    logger.info("Visualization complete")

if __name__ == "__main__":
    main()

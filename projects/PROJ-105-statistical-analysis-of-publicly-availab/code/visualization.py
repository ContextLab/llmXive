import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from scipy import stats
from scipy.stats import probplot
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_r2(observed: np.ndarray, predicted: np.ndarray) -> float:
    """
    Calculate R-squared value for observed vs predicted data.
    
    Args:
        observed: Array of observed values
        predicted: Array of predicted values
        
    Returns:
        R-squared value
    """
    if len(observed) != len(predicted):
        raise ValueError("Observed and predicted arrays must have the same length")
    
    ss_res = np.sum((observed - predicted) ** 2)
    ss_tot = np.sum((observed - np.mean(observed)) ** 2)
    
    if ss_tot == 0:
        return 0.0
        
    return 1 - (ss_res / ss_tot)

def empirical_survival_function(data: np.ndarray, x_values: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate the empirical survival function (1 - CDF) for given data.
    
    Args:
        data: Array of data values
        x_values: Optional array of x values to evaluate at. If None, uses unique sorted values from data.
        
    Returns:
        Tuple of (x_values, survival_probabilities)
    """
    data = np.sort(data)
    n = len(data)
    
    if x_values is None:
        x_values = np.unique(data)
    
    # Calculate survival probabilities
    survival_probs = np.array([1 - (np.searchsorted(data, x, side='right') / n) for x in x_values])
    
    return x_values, survival_probs

def plot_loglog_survival(
    data: np.ndarray,
    fitted_data: Optional[np.ndarray] = None,
    model_name: str = "Unknown",
    output_path: Optional[Path] = None,
    x_min: Optional[float] = None
) -> Dict[str, Any]:
    """
    Generate a log-log survival plot comparing empirical data to fitted model.
    
    Args:
        data: Array of empirical data
        fitted_data: Optional array of fitted model values
        model_name: Name of the model for the plot title
        output_path: Path to save the plot
        x_min: Optional x_min threshold for tail analysis
        
    Returns:
        Dictionary with R-squared value and plot statistics
    """
    logger.info(f"Generating log-log survival plot for {model_name}")
    
    # Calculate empirical survival function
    x_emp, surv_emp = empirical_survival_function(data)
    
    # Filter to positive values for log-log plot
    mask = x_emp > 0
    x_emp = x_emp[mask]
    surv_emp = surv_emp[mask]
    
    # Calculate R-squared if fitted data is provided
    r2 = None
    if fitted_data is not None:
        x_fit, surv_fit = empirical_survival_function(fitted_data)
        mask_fit = x_fit > 0
        x_fit = x_fit[mask_fit]
        surv_fit = surv_fit[mask_fit]
        
        # Interpolate fitted values to match empirical x values for comparison
        surv_fit_interp = np.interp(x_emp, x_fit, surv_fit, left=1.0, right=0.0)
        r2 = calculate_r2(surv_emp, surv_fit_interp)
    
    # Create plot
    plt.figure(figsize=(10, 8))
    plt.loglog(x_emp, surv_emp, 'b.', label='Empirical Data', alpha=0.5)
    
    if fitted_data is not None:
        plt.loglog(x_fit, surv_fit, 'r-', label=f'Fitted {model_name}', linewidth=2)
    
    if x_min is not None:
        plt.axvline(x=x_min, color='g', linestyle='--', label=f'x_min = {x_min:.2f}')
    
    plt.xlabel('Delay (minutes)')
    plt.ylabel('Survival Probability P(X > x)')
    plt.title(f'Log-Log Survival Plot: {model_name}')
    plt.legend()
    plt.grid(True, which="both", ls="-", alpha=0.2)
    
    # Save plot if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Saved log-log survival plot to {output_path}")
    
    plt.close()
    
    result = {
        'model_name': model_name,
        'num_points': len(x_emp),
        'r_squared': r2,
        'x_min': x_min
    }
    
    return result

def plot_qq_plot(
    data: np.ndarray,
    fitted_distribution: Any,
    model_name: str = "Unknown",
    output_path: Optional[Path] = None,
    x_min: Optional[float] = None
) -> Dict[str, Any]:
    """
    Generate a QQ-plot comparing empirical data to a fitted distribution.
    
    Args:
        data: Array of empirical data
        fitted_distribution: Fitted distribution object from scipy.stats
        model_name: Name of the model for the plot title
        output_path: Path to save the plot
        x_min: Optional x_min threshold for tail analysis
        
    Returns:
        Dictionary with QQ-plot statistics
    """
    logger.info(f"Generating QQ-plot for {model_name}")
    
    # Filter to positive values if needed
    data = data[data > 0]
    
    # Calculate theoretical quantiles
    theoretical_quantiles, sample_quantiles = probplot(data, dist=fitted_distribution, plot=None)
    
    # Calculate R-squared for the QQ-plot
    r2 = calculate_r2(sample_quantiles, theoretical_quantiles)
    
    # Create plot
    plt.figure(figsize=(10, 8))
    plt.scatter(theoretical_quantiles, sample_quantiles, alpha=0.5, s=10)
    
    # Add reference line
    min_val = min(theoretical_quantiles.min(), sample_quantiles.min())
    max_val = max(theoretical_quantiles.max(), sample_quantiles.max())
    plt.plot([min_val, max_val], [min_val, max_val], 'r--', label='Reference Line')
    
    plt.xlabel('Theoretical Quantiles')
    plt.ylabel('Sample Quantiles')
    plt.title(f'QQ-Plot: {model_name}')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Add x_min line if provided
    if x_min is not None:
        plt.axvline(x=x_min, color='g', linestyle=':', alpha=0.7, label=f'x_min = {x_min:.2f}')
    
    # Save plot if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Saved QQ-plot to {output_path}")
    
    plt.close()
    
    result = {
        'model_name': model_name,
        'num_points': len(data),
        'r_squared': r2,
        'x_min': x_min
    }
    
    return result

def save_r2_results(results: Dict[str, Any], output_path: Path) -> None:
    """
    Save R-squared results to a JSON file.
    
    Args:
        results: Dictionary of R-squared results
        output_path: Path to save the JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved R-squared results to {output_path}")

def main():
    """
    Main function to generate visualization artifacts for User Story 3.
    This function assumes that cleaned data and model fits are available from previous stages.
    """
    logger.info("Starting visualization stage (T037)")
    
    # Define paths
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    results_dir = data_dir / "results"
    figures_dir = data_dir / "figures"
    
    # Ensure directories exist
    results_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    # Load cleaned data
    cleaned_data_path = data_dir / "cleaned_delays.csv"
    if not cleaned_data_path.exists():
        logger.error(f"Cleaned data file not found: {cleaned_data_path}")
        return
    
    try:
        import pandas as pd
        df = pd.read_csv(cleaned_data_path)
        
        # Extract delay values (assuming 'total_delay' column exists)
        if 'total_delay' in df.columns:
            delay_data = df['total_delay'].values
        elif 'ArrDelay' in df.columns:
            delay_data = df['ArrDelay'].values
        else:
            logger.error("No delay column found in cleaned data")
            return
        
        delay_data = delay_data[delay_data > 0]  # Filter positive values
        
        if len(delay_data) == 0:
            logger.error("No positive delay values found")
            return
        
        logger.info(f"Loaded {len(delay_data)} delay values")
        
        # Load model comparison results to identify best model
        model_comparison_path = results_dir / "model_comparison.json"
        if model_comparison_path.exists():
            with open(model_comparison_path, 'r') as f:
                model_results = json.load(f)
            
            # Find best model based on AIC
            best_model = min(model_results['models'], key=lambda x: x['aic'])
            best_model_name = best_model['name']
            best_model_params = best_model['params']
            
            logger.info(f"Best model identified: {best_model_name}")
            
            # Fit the best distribution to data
            dist_name = best_model_name.lower()
            if dist_name == 'exponential':
                fitted_dist = stats.expon
            elif dist_name == 'gamma':
                fitted_dist = stats.gamma
            elif dist_name == 'lognormal':
                fitted_dist = stats.lognorm
            elif dist_name == 'weibull':
                fitted_dist = stats.weibull_min
            elif dist_name == 'pareto':
                fitted_dist = stats.pareto
            else:
                logger.warning(f"Unknown distribution: {dist_name}, skipping QQ-plot")
                return
            
            # Generate QQ-plot
            qq_output_path = figures_dir / f"qq_plot_{best_model_name}.png"
            qq_results = plot_qq_plot(
                delay_data,
                fitted_dist,
                model_name=best_model_name,
                output_path=qq_output_path
            )
            
            # Save QQ-plot results
            qq_results_path = results_dir / "qq_plot_results.json"
            with open(qq_results_path, 'w') as f:
                json.dump(qq_results, f, indent=2)
            
            logger.info(f"Generated QQ-plot: {qq_output_path}")
            logger.info(f"Saved QQ-plot results: {qq_results_path}")
            
        else:
            logger.warning("Model comparison results not found, skipping QQ-plot generation")
            
    except Exception as e:
        logger.error(f"Error during visualization: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
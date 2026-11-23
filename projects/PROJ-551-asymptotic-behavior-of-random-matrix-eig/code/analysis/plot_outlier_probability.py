"""
Visualization script for User Story 2 (T025).
Plots the probability of outlier emergence vs. theta for different sparsity patterns.
Reads aggregated sweep results from data/processed/validated_sweep_results.csv
and outputs the plot to data/figures/outlier_probability_vs_theta.png.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(project_root))

from utils.config import get_project_paths, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def sigmoid_function(x, a, b, c):
    """
    Logistic sigmoid function for fitting the phase transition.
    P(outlier) = 1 / (1 + exp(-a * (x - c)))
    where c is the critical threshold theta_c.
    """
    return 1.0 / (1.0 + np.exp(-a * (x - b)))

def load_aggregated_results(csv_path: str) -> pd.DataFrame:
    """
    Load the validated sweep results CSV.
    Expected columns: N, theta, seed, outlier_flag, support_density, perturbation_type
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Input file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    
    # Ensure required columns exist
    required_cols = ['theta', 'outlier_flag', 'perturbation_type']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {csv_path}: {missing}")
    
    logger.info(f"Loaded {len(df)} records from {csv_path}")
    return df

def aggregate_by_theta_and_type(df: pd.DataFrame) -> Dict[str, Dict[float, Tuple[int, int]]]:
    """
    Aggregate results by theta and perturbation_type.
    Returns: {type: {theta: (count_outliers, total_count)}}
    """
    aggregated = {}
    
    for ptype in df['perturbation_type'].unique():
        type_df = df[df['perturbation_type'] == ptype]
        aggregated[ptype] = {}
        
        for theta in type_df['theta'].unique():
            theta_df = type_df[type_df['theta'] == theta]
            total = len(theta_df)
            outliers = theta_df['outlier_flag'].sum()
            aggregated[ptype][theta] = (outliers, total)
    
    return aggregated

def plot_probability_vs_theta(
    aggregated_data: Dict[str, Dict[float, Tuple[int, int]]],
    output_path: str,
    title: str = "Probability of Outlier Emergence vs. Perturbation Strength (θ)"
):
    """
    Plot the probability of outlier emergence for each sparsity pattern.
    Fits a logistic curve to the data points.
    """
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(12, 8))

    colors = {'diagonal': 'blue', 'block-sparse': 'green', 'random sparse': 'red'}
    markers = {'diagonal': 'o', 'block-sparse': 's', 'random sparse': '^'}

    for ptype, data in aggregated_data.items():
        thetas = sorted(data.keys())
        probs = []
        errors = []

        for theta in thetas:
            outliers, total = data[theta]
            prob = outliers / total if total > 0 else 0.0
            probs.append(prob)
            # Binomial error estimate
            if total > 0:
                err = np.sqrt(prob * (1 - prob) / total)
            else:
                err = 0.0
            errors.append(err)

        # Plot data points with error bars
        color = colors.get(ptype, 'black')
        marker = markers.get(ptype, 'o')
        ax.errorbar(
            thetas, probs, yerr=errors,
            fmt=f'{marker}',
            capsize=5,
            label=f'{ptype} (data)',
            color=color,
            alpha=0.7
        )

        # Fit logistic curve if we have enough points
        if len(thetas) >= 3:
            try:
                popt, _ = curve_fit(
                    sigmoid_function,
                    np.array(thetas),
                    np.array(probs),
                    p0=[1.0, 2.0, 2.0], # a, b (theta_c), c
                    maxfev=2000
                )
                # Generate smooth curve for plotting
                x_fit = np.linspace(min(thetas), max(thetas), 100)
                y_fit = sigmoid_function(x_fit, *popt)
                ax.plot(x_fit, y_fit, '--', color=color, alpha=0.8, label=f'{ptype} (fit)')
                logger.info(f"Fitted theta_c for {ptype}: {popt[1]:.4f}")
            except Exception as e:
                logger.warning(f"Could not fit logistic curve for {ptype}: {e}")

    ax.set_xlabel(r'Perturbation Strength $\theta$', fontsize=14)
    ax.set_ylabel('Probability of Outlier Emergence', fontsize=14)
    ax.set_title(title, fontsize=16)
    ax.legend(fontsize=12)
    ax.set_xlim(left=0.5)
    ax.set_ylim(bottom=-0.05, top=1.05)
    ax.grid(True, linestyle='--', alpha=0.7)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Plot saved to {output_path}")

def main():
    """Main entry point for the visualization script."""
    project_root = Path(__file__).resolve().parent.parent.parent
    paths = get_project_paths(project_root)
    ensure_directories(project_root)

    input_csv = paths['processed'] / 'validated_sweep_results.csv'
    output_png = paths['figures'] / 'outlier_probability_vs_theta.png'

    logger.info(f"Starting outlier probability visualization.")
    logger.info(f"Input: {input_csv}")
    logger.info(f"Output: {output_png}")

    try:
        # Load data
        df = load_aggregated_results(str(input_csv))
        
        # Aggregate
        aggregated = aggregate_by_theta_and_type(df)
        
        if not aggregated:
            logger.error("No data found to aggregate.")
            sys.exit(1)

        # Plot
        plot_probability_vs_theta(aggregated, str(output_png))
        
        logger.info("Visualization completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        logger.error("Ensure T020b (validated_sweep_results.csv) has been completed.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during visualization: {e}")
        raise

if __name__ == "__main__":
    main()
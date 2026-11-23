"""
Visualization module for generating CPU-only plots.
Ensures matplotlib uses non-GPU backends for all rendering.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# FORCE CPU-ONLY RENDERING
# Set the backend to 'Agg' (non-interactive, CPU-only) BEFORE importing pyplot
import matplotlib
matplotlib.use('Agg')  # Agg is a CPU-only raster backend, no GPU acceleration
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from logging_config import get_logger

# Configure logger
logger = get_logger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DOCS_OUTPUT_DIR = PROJECT_ROOT / "docs" / "output"

# Ensure output directory exists
DOCS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_regression_results(filepath: Optional[Path] = None) -> Dict[str, Any]:
    """Load regression results from JSON file."""
    if filepath is None:
        filepath = DATA_PROCESSED_DIR / "regression_results_primary.json"
    
    if not filepath.exists():
        logger.error(f"Regression results file not found: {filepath}")
        raise FileNotFoundError(f"Regression results file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        return json.load(f)


def load_processed_data(filepath: Optional[Path] = None) -> pd.DataFrame:
    """Load processed dataset from CSV file."""
    if filepath is None:
        filepath = DATA_PROCESSED_DIR / "merged_data_cleaned.csv"
    
    if not filepath.exists():
        logger.error(f"Processed data file not found: {filepath}")
        raise FileNotFoundError(f"Processed data file not found: {filepath}")
    
    return pd.read_csv(filepath)


def generate_residual_scatter_plot(
    results: Optional[Dict[str, Any]] = None,
    data: Optional[pd.DataFrame] = None,
    output_path: Optional[Path] = None
) -> Path:
    """
    Generate a residual scatter plot (Predicted vs. Residuals).
    Uses CPU-only 'Agg' backend exclusively.
    """
    logger.info("Generating residual scatter plot...")

    if results is None:
        results = load_regression_results()
    
    if data is None:
        data = load_processed_data()

    # Extract predicted and residual values from regression results
    # Assuming results structure contains 'predicted' and 'residuals' arrays
    if 'predicted' not in results or 'residuals' not in results:
        logger.error("Regression results missing 'predicted' or 'residuals' keys.")
        raise KeyError("Regression results missing required keys: 'predicted', 'residuals'")

    predicted = np.array(results['predicted'])
    residuals = np.array(results['residuals'])

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Scatter plot
    ax.scatter(predicted, residuals, alpha=0.6, edgecolors='w', linewidth=0.5, color='steelblue')
    
    # Add reference line (y=0)
    ax.axhline(y=0, color='red', linestyle='--', linewidth=1.5, label='Zero Residual')
    
    # Labels and title
    ax.set_xlabel('Predicted Values', fontsize=12)
    ax.set_ylabel('Residuals', fontsize=12)
    ax.set_title('Residual Scatter Plot (Predicted vs. Residuals)', fontsize=14, fontweight='bold')
    
    # Grid
    ax.grid(True, linestyle=':', alpha=0.6)
    
    # Legend
    ax.legend(loc='best')
    
    # Tight layout
    plt.tight_layout()

    # Determine output path
    if output_path is None:
        output_path = DOCS_OUTPUT_DIR / "residual_scatter_plot.png"
    
    # Save plot (CPU-only backend ensures no GPU usage)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    logger.info(f"Residual scatter plot saved to: {output_path}")
    return output_path


def generate_coefficient_plot(
    results: Optional[Dict[str, Any]] = None,
    output_path: Optional[Path] = None
) -> Path:
    """
    Generate a coefficient plot with confidence interval error bars.
    Uses CPU-only 'Agg' backend exclusively.
    """
    logger.info("Generating coefficient plot...")

    if results is None:
        results = load_regression_results()

    # Extract coefficient data
    # Expected keys: 'coefficients', 'std_errors', 'p_values', 'variable_names'
    if not all(k in results for k in ['coefficients', 'std_errors', 'variable_names']):
        logger.error("Regression results missing required keys for coefficient plot.")
        raise KeyError("Regression results missing required keys: 'coefficients', 'std_errors', 'variable_names'")

    coefs = np.array(results['coefficients'])
    std_errs = np.array(results['std_errors'])
    var_names = results['variable_names']
    
    # Calculate 95% CI (approx 1.96 * std_err)
    ci_lower = coefs - 1.96 * std_errs
    ci_upper = coefs + 1.96 * std_errs

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Y positions for bars
    y_pos = np.arange(len(var_names))
    
    # Plot bars with error bars
    ax.barh(y_pos, coefs, xerr=[coefs - ci_lower, ci_upper - coefs], 
            align='center', color='steelblue', ecolor='red', capsize=5, alpha=0.8)
    
    # Reference line at 0
    ax.axvline(x=0, color='black', linestyle='-', linewidth=1.5)
    
    # Labels
    ax.set_yticks(y_pos)
    ax.set_yticklabels(var_names)
    ax.set_xlabel('Coefficient Estimate (95% CI)', fontsize=12)
    ax.set_title('Regression Coefficients with Confidence Intervals', fontsize=14, fontweight='bold')
    
    # Grid
    ax.grid(True, axis='x', linestyle=':', alpha=0.6)
    
    # Tight layout
    plt.tight_layout()

    # Determine output path
    if output_path is None:
        output_path = DOCS_OUTPUT_DIR / "coefficient_plot.png"
    
    # Save plot (CPU-only backend)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    logger.info(f"Coefficient plot saved to: {output_path}")
    return output_path


def main():
    """
    Main entry point for generating all visualization outputs.
    Ensures all plots are generated using CPU-only rendering.
    """
    logger.info("Starting visualization generation (CPU-only mode)...")
    
    try:
        # Load data
        results = load_regression_results()
        data = load_processed_data()
        
        # Generate plots
        residual_plot_path = generate_residual_scatter_plot(results, data)
        coef_plot_path = generate_coefficient_plot(results)
        
        logger.info("All plots generated successfully.")
        logger.info(f"  - Residual Plot: {residual_plot_path}")
        logger.info(f"  - Coefficient Plot: {coef_plot_path}")
        
    except Exception as e:
        logger.error(f"Visualization generation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
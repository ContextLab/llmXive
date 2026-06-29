"""
Visualization module for generating publication-ready plots.

Implements T041: Generate scatter plots with regression lines using matplotlib.
Output formats: PNG and PDF per T042 specification.

This module depends on correlation_results.csv produced by correlation_analysis.py.
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless operation
import matplotlib.pyplot as plt
import numpy as np
import csv

# Import config for reproducibility parameters
from config import (
    get_clone_thresholds,
    get_random_seed,
    get_figure_format,
    get_figure_dpi
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Output paths
PROJECT_ROOT = Path(__file__).parent.parent
FIGURES_DIR = PROJECT_ROOT / "data" / "analysis" / "figures"
CORRELATION_RESULTS_PATH = PROJECT_ROOT / "data" / "analysis" / "correlation_results.csv"

# Ensure output directory exists
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

def setup_logging():
    """Configure logging for visualization module."""
    logger.info("Visualization module initialized")
    logger.info(f"Output directory: {FIGURES_DIR}")
    logger.info(f"Random seed: {get_random_seed()}")
    logger.info(f"Figure formats: {get_figure_format()}")
    logger.info(f"Figure DPI: {get_figure_dpi()}")

def load_correlation_data() -> Optional[List[Dict[str, Any]]]:
    """
    Load correlation results from CSV file.
    
    Returns:
        List of dictionaries containing correlation data, or None if file not found
    """
    if not CORRELATION_RESULTS_PATH.exists():
        logger.error(f"Correlation results not found: {CORRELATION_RESULTS_PATH}")
        return None
    
    try:
        with open(CORRELATION_RESULTS_PATH, 'r') as f:
            reader = csv.DictReader(f)
            data = list(reader)
        
        logger.info(f"Loaded {len(data)} correlation result rows")
        return data
    except Exception as e:
        logger.error(f"Failed to load correlation data: {e}")
        return None

def compute_regression(x: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute linear regression for scatter plot.
    
    Args:
        x: Independent variable values
        y: Dependent variable values
    
    Returns:
        Tuple of (slope, intercept, correlation_coefficient)
    """
    # Filter out NaN values
    mask = ~(np.isnan(x) | np.isnan(y))
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 2:
        logger.warning("Insufficient data points for regression")
        return np.array([]), np.array([]), 0.0
    
    # Compute regression using numpy
    slope, intercept = np.polyfit(x_clean, y_clean, 1)
    correlation = np.corrcoef(x_clean, y_clean)[0, 1]
    
    # Generate regression line points
    x_line = np.linspace(x_clean.min(), x_clean.max(), 100)
    y_line = slope * x_line + intercept
    
    logger.info(f"Regression: slope={slope:.4f}, intercept={intercept:.4f}, r={correlation:.4f}")
    
    return x_line, y_line, correlation if not np.isnan(correlation) else 0.0

def create_scatter_plot_with_regression(
    x: np.ndarray,
    y: np.ndarray,
    x_label: str,
    y_label: str,
    title: str,
    output_path: Path,
    correlation: float = None
):
    """
    Create a scatter plot with regression line.
    
    Args:
        x: X-axis values
        y: Y-axis values
        x_label: X-axis label
        y_label: Y-axis label
        title: Plot title
        output_path: Output file path
        correlation: Pre-computed correlation coefficient (optional)
    """
    # Set random seed for reproducibility
    np.random.seed(get_random_seed())
    
    fig, ax = plt.subplots(figsize=(10, 8), dpi=get_figure_dpi())
    
    # Scatter plot
    ax.scatter(x, y, alpha=0.6, c='steelblue', edgecolors='black', s=50, label='Data Points')
    
    # Regression line
    x_line, y_line, corr = compute_regression(x, y)
    if len(x_line) > 0:
        ax.plot(x_line, y_line, 'r-', linewidth=2, label=f'Regression (r={corr:.3f})')
    
    # Labels and title
    ax.set_xlabel(x_label, fontsize=12)
    ax.set_ylabel(y_label, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    # Grid and legend
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best')
    
    # Save in both PNG and PDF formats
    formats = get_figure_format()
    for fmt in formats:
        output_file = output_path.parent / f"{output_path.stem}.{fmt}"
        plt.savefig(output_file, dpi=get_figure_dpi(), bbox_inches='tight')
        logger.info(f"Saved {output_file}")
    
    plt.close(fig)

def create_clone_density_vs_perplexity_plot(data: List[Dict[str, Any]]):
    """
    Create scatter plot of clone density vs perplexity.
    
    Args:
        data: List of correlation result dictionaries
    """
    # Extract data points
    x_values = []
    y_values = []
    
    for row in data:
        try:
            clone_density = float(row.get('clone_density', 0))
            perplexity = float(row.get('perplexity', 0))
            if not np.isnan(clone_density) and not np.isnan(perplexity):
                x_values.append(clone_density)
                y_values.append(perplexity)
        except (ValueError, TypeError):
            continue
    
    if len(x_values) < 2:
        logger.warning("Insufficient data for clone density vs perplexity plot")
        return
    
    output_path = FIGURES_DIR / "clone_density_vs_perplexity"
    create_scatter_plot_with_regression(
        np.array(x_values),
        np.array(y_values),
        "Clone Density",
        "Perplexity",
        "Clone Density vs Model Perplexity",
        output_path
    )

def create_clone_density_vs_accuracy_plot(data: List[Dict[str, Any]]):
    """
    Create scatter plot of clone density vs bug detection accuracy.
    
    Args:
        data: List of correlation result dictionaries
    """
    # Extract data points
    x_values = []
    y_values = []
    
    for row in data:
        try:
            clone_density = float(row.get('clone_density', 0))
            accuracy = float(row.get('bug_detection_accuracy', 0))
            if not np.isnan(clone_density) and not np.isnan(accuracy):
                x_values.append(clone_density)
                y_values.append(accuracy)
        except (ValueError, TypeError):
            continue
    
    if len(x_values) < 2:
        logger.warning("Insufficient data for clone density vs accuracy plot")
        return
    
    output_path = FIGURES_DIR / "clone_density_vs_accuracy"
    create_scatter_plot_with_regression(
        np.array(x_values),
        np.array(y_values),
        "Clone Density",
        "Bug Detection Accuracy (pass@1)",
        "Clone Density vs Bug Detection Accuracy",
        output_path
    )

def create_sensitivity_analysis_plot(data: List[Dict[str, Any]]):
    """
    Create sensitivity analysis plot across thresholds.
    
    Args:
        data: List of correlation result dictionaries
    """
    thresholds = get_clone_thresholds()
    correlations_by_threshold = {}
    
    for threshold in thresholds:
      threshold_str = str(threshold)
      correlations = []
      for row in data:
          if row.get('threshold') == threshold_str or str(threshold) in str(row.get('threshold', '')):
              try:
                  corr = float(row.get('correlation_perplexity', row.get('correlation', 0)))
                  if not np.isnan(corr):
                      correlations.append(corr)
              except (ValueError, TypeError):
                  continue
      
      if correlations:
          correlations_by_threshold[threshold] = np.mean(correlations)
    
    if not correlations_by_threshold:
        logger.warning("No sensitivity analysis data found")
        return
    
    # Create bar plot
    fig, ax = plt.subplots(figsize=(10, 6), dpi=get_figure_dpi())
    
    threshold_values = list(correlations_by_threshold.keys())
    correlation_values = list(correlations_by_threshold.values())
    
    bars = ax.bar(
        [str(t) for t in threshold_values],
        correlation_values,
        color='steelblue',
        alpha=0.8,
        edgecolor='black'
    )
    
    # Add value labels on bars
    for bar, val in zip(bars, correlation_values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.01,
            f'{val:.3f}',
            ha='center',
            va='bottom',
            fontsize=10
        )
    
    ax.set_xlabel('Clone Detection Threshold', fontsize=12)
    ax.set_ylabel('Mean Correlation Coefficient', fontsize=12)
    ax.set_title('Sensitivity Analysis: Correlation vs Threshold', fontsize=14, fontweight='bold')
    ax.set_ylim(0, max(correlation_values) * 1.2 if correlation_values else 1)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Save in both formats
    output_path = FIGURES_DIR / "sensitivity_analysis"
    formats = get_figure_format()
    for fmt in formats:
        output_file = output_path.parent / f"{output_path.stem}.{fmt}"
        plt.savefig(output_file, dpi=get_figure_dpi(), bbox_inches='tight')
        logger.info(f"Saved {output_file}")
    
    plt.close(fig)

def generate_all_visualizations():
    """
    Generate all required visualizations.
    
    This is the main entry point for the visualization pipeline.
    """
    setup_logging()
    
    # Load correlation data
    data = load_correlation_data()
    if data is None:
        logger.error("Cannot generate visualizations without correlation data")
        return False
    
    # Generate plots
    logger.info("Generating clone density vs perplexity plot...")
    create_clone_density_vs_perplexity_plot(data)
    
    logger.info("Generating clone density vs accuracy plot...")
    create_clone_density_vs_accuracy_plot(data)
    
    logger.info("Generating sensitivity analysis plot...")
    create_sensitivity_analysis_plot(data)
    
    logger.info("All visualizations generated successfully")
    return True

def main():
    """Main entry point."""
    success = generate_all_visualizations()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
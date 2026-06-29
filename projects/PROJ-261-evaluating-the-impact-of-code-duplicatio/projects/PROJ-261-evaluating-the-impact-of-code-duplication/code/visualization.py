"""
Visualization module for generating scatter plots with regression lines.

This module creates publication-ready visualizations showing the relationship
between code duplication metrics and LLM performance metrics.
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless environments
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from config import (
    get_figure_format,
    get_figure_dpi,
    get_random_seed,
    get_clone_thresholds
)
from checksum_manifest import record_artifact_checksums

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def setup_logging() -> logging.Logger:
    """Setup and return the logger for this module."""
    return logger


def load_correlation_data(filepath: Path) -> Optional[pd.DataFrame]:
    """
    Load correlation results from CSV file.
    
    Args:
        filepath: Path to correlation_results.csv
        
    Returns:
        DataFrame with correlation data, or None if file not found
    """
    if not filepath.exists():
        logger.error(f"Correlation results not found: {filepath}")
        return None
    
    try:
        df = pd.read_csv(filepath)
        logger.info(f"Loaded {len(df)} correlation records from {filepath}")
        return df
    except Exception as e:
        logger.error(f"Failed to load correlation data: {e}")
        return None


def compute_regression(
    x: np.ndarray,
    y: np.ndarray
) -> Optional[Tuple[float, float, float, float, float]]:
    """
    Compute linear regression parameters for scatter plot.
    
    Args:
        x: Independent variable array
        y: Dependent variable array
        
    Returns:
        Tuple of (slope, intercept, r_value, p_value, std_err) or None if computation fails
    """
    if len(x) < 2 or len(y) < 2:
        logger.warning("Not enough data points for regression (need at least 2)")
        return None
    
    try:
        # Filter out NaN/inf values
        mask = np.isfinite(x) & np.isfinite(y)
        x_clean = x[mask]
        y_clean = y[mask]
        
        if len(x_clean) < 2:
            logger.warning("After filtering NaN/inf, not enough data points for regression")
            return None
        
        slope, intercept, r_value, p_value, std_err = np.polyfit(
            x_clean, y_clean, 1
        )
        return slope, intercept, r_value, p_value, std_err
    except Exception as e:
        logger.error(f"Regression computation failed: {e}")
        return None


def create_scatter_plot_with_regression(
    ax: plt.Axes,
    x: np.ndarray,
    y: np.ndarray,
    xlabel: str,
    ylabel: str,
    title: str,
    regression: Optional[Tuple[float, float, float, float, float]] = None,
    color: str = '#1f77b4'
) -> None:
    """
    Create a scatter plot with optional regression line.
    
    Args:
        ax: Matplotlib axes object
        x: Independent variable data
        y: Dependent variable data
        xlabel: X-axis label
        ylabel: Y-axis label
        title: Plot title
        regression: Optional regression tuple (slope, intercept, r_value, p_value, std_err)
        color: Plot color
    """
    # Plot scatter points
    ax.scatter(x, y, alpha=0.6, s=20, color=color, edgecolors='black', linewidth=0.5)
    
    # Add regression line if available
    if regression is not None:
        slope, intercept, r_value, p_value, std_err = regression
        x_line = np.linspace(min(x), max(x), 100)
        y_line = slope * x_line + intercept
        ax.plot(x_line, y_line, 'r-', linewidth=2, label=f'Regression (r={r_value:.3f}, p={p_value:.3f})')
        ax.legend(loc='best')
    
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)


def create_clone_density_vs_perplexity_plot(
    df: pd.DataFrame,
    output_path: Path,
    format: str = 'png',
    dpi: int = 300
) -> bool:
    """
    Create scatter plot of clone density vs perplexity.
    
    Args:
        df: DataFrame with clone_density and perplexity columns
        output_path: Path to save the figure
        format: Output format ('png' or 'pdf')
        dpi: Figure DPI
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("Creating clone density vs perplexity plot...")
        
        # Extract data
        x = df['clone_density'].values
        y = df['perplexity'].values
        
        # Compute regression
        regression = compute_regression(x, y)
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8))
        create_scatter_plot_with_regression(
            ax, x, y,
            'Clone Density',
            'Perplexity',
            'Clone Density vs. Model Perplexity',
            regression,
            color='#1f77b4'
        )
        
        # Save figure
        plt.tight_layout()
        save_path = output_path / f'clone_density_vs_perplexity.{format}'
        fig.savefig(save_path, dpi=dpi, format=format, bbox_inches='tight')
        plt.close(fig)
        
        logger.info(f"Saved plot to {save_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create clone density vs perplexity plot: {e}")
        return False


def create_clone_density_vs_accuracy_plot(
    df: pd.DataFrame,
    output_path: Path,
    format: str = 'png',
    dpi: int = 300
) -> bool:
    """
    Create scatter plot of clone density vs bug detection accuracy.
    
    Args:
        df: DataFrame with clone_density and accuracy columns
        output_path: Path to save the figure
        format: Output format ('png' or 'pdf')
        dpi: Figure DPI
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("Creating clone density vs accuracy plot...")
        
        # Extract data
        x = df['clone_density'].values
        y = df['accuracy'].values
        
        # Compute regression
        regression = compute_regression(x, y)
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8))
        create_scatter_plot_with_regression(
            ax, x, y,
            'Clone Density',
            'Bug Detection Accuracy (pass@1)',
            'Clone Density vs. Bug Detection Accuracy',
            regression,
            color='#2ca02c'
        )
        
        # Save figure
        plt.tight_layout()
        save_path = output_path / f'clone_density_vs_accuracy.{format}'
        fig.savefig(save_path, dpi=dpi, format=format, bbox_inches='tight')
        plt.close(fig)
        
        logger.info(f"Saved plot to {save_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create clone density vs accuracy plot: {e}")
        return False


def create_sensitivity_analysis_plot(
    df: pd.DataFrame,
    output_path: Path,
    format: str = 'png',
    dpi: int = 300
) -> bool:
    """
    Create sensitivity analysis plot showing correlation across thresholds.
    
    Args:
        df: DataFrame with threshold, correlation, and p_value columns
        output_path: Path to save the figure
        format: Output format ('png' or 'pdf')
        dpi: Figure DPI
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("Creating sensitivity analysis plot...")
        
        # Group by threshold and metric
        thresholds = sorted(df['threshold'].unique())
        metrics = df['metric'].unique()
        
        # Create figure with subplots for each metric
        fig, axes = plt.subplots(1, len(metrics), figsize=(4 * len(metrics), 4))
        if len(metrics) == 1:
            axes = [axes]
        
        for idx, metric in enumerate(metrics):
            ax = axes[idx]
            metric_df = df[df['metric'] == metric]
            
            x = metric_df['threshold'].values
            y = metric_df['correlation'].values
            yerr = metric_df['p_value'].values  # Use p-value as error indicator
            
            ax.errorbar(x, y, yerr=yerr, fmt='o-', capsize=5, linewidth=2, markersize=8)
            ax.set_xlabel('Clone Detection Threshold')
            ax.set_ylabel(f'{metric.capitalize()} Correlation')
            ax.set_title(f'Sensitivity: {metric.capitalize()}')
            ax.grid(True, alpha=0.3)
            ax.set_xticks(thresholds)
        
        plt.tight_layout()
        save_path = output_path / f'sensitivity_analysis.{format}'
        fig.savefig(save_path, dpi=dpi, format=format, bbox_inches='tight')
        plt.close(fig)
        
        logger.info(f"Saved plot to {save_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create sensitivity analysis plot: {e}")
        return False


def generate_all_visualizations(
    correlation_path: Path,
    output_dir: Path,
    formats: Optional[List[str]] = None,
    dpi: Optional[int] = None
) -> Dict[str, bool]:
    """
    Generate all visualizations from correlation results.
    
    Args:
        correlation_path: Path to correlation_results.csv
        output_dir: Directory to save figures
        formats: List of output formats (default: from config)
        dpi: Figure DPI (default: from config)
        
    Returns:
        Dictionary mapping figure type to success status
    """
    if formats is None:
        formats = [get_figure_format()]
    if dpi is None:
        dpi = get_figure_dpi()
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load correlation data
    df = load_correlation_data(correlation_path)
    if df is None:
        logger.error("Cannot generate visualizations without correlation data")
        return {
            'clone_density_vs_perplexity': False,
            'clone_density_vs_accuracy': False,
            'sensitivity_analysis': False
        }
    
    results = {}
    
    # Generate plots for each format
    for fmt in formats:
        logger.info(f"Generating visualizations in {fmt} format...")
        
        # Clone density vs perplexity
        results['clone_density_vs_perplexity'] = create_clone_density_vs_perplexity_plot(
            df, output_dir, format=fmt, dpi=dpi
        )
        
        # Clone density vs accuracy
        results['clone_density_vs_accuracy'] = create_clone_density_vs_accuracy_plot(
            df, output_dir, format=fmt, dpi=dpi
        )
        
        # Sensitivity analysis
        results['sensitivity_analysis'] = create_sensitivity_analysis_plot(
            df, output_dir, format=fmt, dpi=dpi
        )
    
    return results


def main() -> int:
    """
    Main entry point for visualization generation.
    
    Returns:
        0 on success, 1 on failure
    """
    logger.info("=" * 60)
    logger.info("Starting visualization generation...")
    logger.info(f"Random seed: {get_random_seed()}")
    logger.info(f"Figure formats: {get_figure_format()}")
    logger.info(f"Figure DPI: {get_figure_dpi()}")
    logger.info("=" * 60)
    
    # Set paths
    project_root = Path(__file__).parent.parent
    correlation_path = project_root / 'data' / 'analysis' / 'correlation_results.csv'
    output_dir = project_root / 'data' / 'analysis' / 'figures'
    
    # Generate visualizations
    formats = [get_figure_format()]
    results = generate_all_visualizations(
        correlation_path, output_dir, formats=formats
    )
    
    # Report results
    logger.info("=" * 60)
    logger.info("Visualization generation complete:")
    for plot_type, success in results.items():
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"  {plot_type}: {status}")
    
    # Record checksums for generated figures
    try:
        record_artifact_checksums(output_dir)
        logger.info("Checksums recorded for visualization outputs")
    except Exception as e:
        logger.warning(f"Failed to record checksums: {e}")
    
    # Return success/failure
    if all(results.values()):
        logger.info("All visualizations generated successfully")
        return 0
    else:
        logger.error("Some visualizations failed to generate")
        return 1


if __name__ == '__main__':
    sys.exit(main())

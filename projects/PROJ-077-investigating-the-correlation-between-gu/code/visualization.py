"""
Visualization module for generating publication-quality plots.
Implements User Story 3: Statistical Correction and Visualization.
"""
import os
import sys
from pathlib import Path
from typing import Optional, Union

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from config import ensure_directories, RANDOM_SEED
from logging_config import get_logger, log_provenance, log_warning

# Set random seed for reproducibility
np.random.seed(RANDOM_SEED)

# Set matplotlib backend to non-interactive for server environments
plt.switch_backend('Agg')

# Configure seaborn style for publication-quality plots
sns.set_style("whitegrid")
sns.set_context("paper", font_scale=1.2)

logger = get_logger(__name__)


def generate_scatter_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    output_path: str,
    xlabel: str = 'Shannon Index',
    ylabel: str = 'Fluid Intelligence',
    title: str = 'Gut Microbiome Diversity vs. Cognitive Performance',
    figsize: tuple = (10, 8),
    dpi: int = 300,
    alpha: float = 0.6,
    color: str = '#2E86AB',
    show_regression_line: bool = True
) -> None:
    """
    Generate a scatter plot showing the relationship between two variables
    with an optional regression line.
    
    Args:
        df: DataFrame containing the data
        x_col: Column name for x-axis
        y_col: Column name for y-axis
        output_path: Path to save the plot
        xlabel: Label for x-axis
        ylabel: Label for y-axis
        title: Plot title
        figsize: Figure size (width, height) in inches
        dpi: Resolution in dots per inch
        alpha: Transparency of scatter points
        color: Color of scatter points
        show_regression_line: Whether to show regression line
    
    Raises:
        ValueError: If required columns are missing or data is invalid
        IOError: If the plot cannot be saved
    """
    logger.info(f"Generating scatter plot: {x_col} vs {y_col}")
    
    # Validate input data
    if x_col not in df.columns or y_col not in df.columns:
        raise ValueError(f"Required columns not found. Available: {df.columns.tolist()}")
    
    # Remove rows with NaN values in the columns of interest
    plot_data = df[[x_col, y_col]].dropna()
    
    if len(plot_data) < 2:
        raise ValueError(f"Insufficient data points for scatter plot. Found: {len(plot_data)}")
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    
    # Create scatter plot
    sns.scatterplot(
        x=x_col,
        y=y_col,
        data=plot_data,
        ax=ax,
        alpha=alpha,
        color=color,
        edgecolor='black',
        linewidth=0.5,
        s=50
    )
    
    # Add regression line if requested
    if show_regression_line and len(plot_data) >= 2:
        # Calculate regression line
        x_vals = plot_data[x_col].values
        y_vals = plot_data[y_col].values
        
        # Fit linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x_vals, y_vals)
        
        # Generate regression line points
        x_line = np.linspace(x_vals.min(), x_vals.max(), 100)
        y_line = slope * x_line + intercept
        
        # Plot regression line
        ax.plot(x_line, y_line, 'r--', linewidth=2, label=f'Regression (r={r_value:.3f}, p={p_value:.3f})')
        
        # Add correlation statistics to legend
        ax.legend(loc='best', framealpha=0.9)
        
        # Log correlation results
        logger.info(f"Correlation: r={r_value:.4f}, p={p_value:.6f}, n={len(plot_data)}")
    
    # Set labels and title
    ax.set_xlabel(xlabel, fontsize=14, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=14, fontweight='bold')
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save figure
    try:
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight', facecolor='white', edgecolor='none')
        logger.info(f"Scatter plot saved to: {output_path}")
        log_provenance(f"Generated scatter plot: {output_path}")
    except Exception as e:
        logger.error(f"Failed to save scatter plot: {e}")
        raise IOError(f"Could not save scatter plot to {output_path}: {e}")
    finally:
        plt.close(fig)


def generate_histogram_plot(
    df: pd.DataFrame,
    col: str,
    output_path: str,
    xlabel: str = 'Shannon Index',
    title: str = 'Distribution of Alpha Diversity',
    figsize: tuple = (10, 6),
    dpi: int = 300,
    bins: int = 30,
    color: str = '#A23B72',
    edgecolor: str = 'black',
    alpha: float = 0.7,
    kde: bool = True
) -> None:
    """
    Generate a histogram showing the distribution of a single variable
    with an optional KDE (Kernel Density Estimate) overlay.
    
    Args:
        df: DataFrame containing the data
        col: Column name to plot
        output_path: Path to save the plot
        xlabel: Label for x-axis
        title: Plot title
        figsize: Figure size (width, height) in inches
        dpi: Resolution in dots per inch
        bins: Number of histogram bins
        color: Color of histogram bars
        edgecolor: Color of bar edges
        alpha: Transparency of bars
        kde: Whether to show KDE overlay
    
    Raises:
        ValueError: If required column is missing or data is invalid
        IOError: If the plot cannot be saved
    """
    logger.info(f"Generating histogram plot for: {col}")
    
    # Validate input data
    if col not in df.columns:
        raise ValueError(f"Required column not found: {col}. Available: {df.columns.tolist()}")
    
    # Remove NaN values
    plot_data = df[col].dropna()
    
    if len(plot_data) == 0:
        raise ValueError(f"No valid data points for histogram: {col}")
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    
    # Create histogram with KDE overlay
    sns.histplot(
        data=plot_data,
        x=col if col in plot_data.index else None,
        kde=kde,
        bins=bins,
        color=color,
        edgecolor=edgecolor,
        alpha=alpha,
        ax=ax
    )
    
    # If passing a Series directly, we need to handle it differently
    if col not in plot_data.index:
        # Re-create histogram properly
        ax.clear()
        sns.histplot(
            x=plot_data.values,
            bins=bins,
            kde=kde,
            color=color,
            edgecolor=edgecolor,
            alpha=alpha,
            ax=ax
        )
    
    # Set labels and title
    ax.set_xlabel(xlabel, fontsize=14, fontweight='bold')
    ax.set_ylabel('Frequency', fontsize=14, fontweight='bold')
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    
    # Add statistics to the plot
    mean_val = plot_data.mean()
    median_val = plot_data.median()
    std_val = plot_data.std()
    
    stats_text = f'Mean: {mean_val:.3f}\nMedian: {median_val:.3f}\nStd: {std_val:.3f}'
    ax.text(
        0.98, 0.98, stats_text,
        transform=ax.transAxes,
        fontsize=11,
        verticalalignment='top',
        horizontalalignment='right',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )
    
    # Add grid
    ax.grid(True, alpha=0.3, axis='y')
    
    # Adjust layout
    plt.tight_layout()
    
    # Save figure
    try:
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight', facecolor='white', edgecolor='none')
        logger.info(f"Histogram plot saved to: {output_path}")
        log_provenance(f"Generated histogram plot: {output_path}")
    except Exception as e:
        logger.error(f"Failed to save histogram plot: {e}")
        raise IOError(f"Could not save histogram plot to {output_path}: {e}")
    finally:
        plt.close(fig)


def generate_correlation_heatmap(
    df: pd.DataFrame,
    columns: Optional[list] = None,
    output_path: Optional[str] = None,
    figsize: tuple = (12, 10),
    dpi: int = 300,
    cmap: str = 'coolwarm',
    annot: bool = True,
    fmt: str = '.2f',
    title: str = 'Correlation Matrix'
) -> Optional[plt.Figure]:
    """
    Generate a correlation heatmap for multiple variables.
    
    Args:
        df: DataFrame containing the data
        columns: List of columns to include (default: all numeric)
        output_path: Path to save the plot (optional)
        figsize: Figure size (width, height) in inches
        dpi: Resolution in dots per inch
        cmap: Color map for the heatmap
        annot: Whether to show correlation values on the heatmap
        fmt: Format string for annotation values
        title: Plot title
    
    Returns:
        Figure object if output_path is not provided
    """
    logger.info("Generating correlation heatmap")
    
    # Select numeric columns if not specified
    if columns is None:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    else:
        numeric_cols = [col for col in columns if col in df.columns and pd.api.types.is_numeric_dtype(df[col])]
    
    if len(numeric_cols) < 2:
        raise ValueError(f"Insufficient numeric columns for correlation matrix. Found: {len(numeric_cols)}")
    
    # Calculate correlation matrix
    corr_matrix = df[numeric_cols].corr()
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    
    # Create heatmap
    sns.heatmap(
        corr_matrix,
        annot=annot,
        fmt=fmt,
        cmap=cmap,
        linewidths=0.5,
        ax=ax,
        cbar_kws={'shrink': 0.8},
        annot_kws={'size': 10}
    )
    
    # Set title
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save or return
    if output_path:
        try:
            plt.savefig(output_path, dpi=dpi, bbox_inches='tight', facecolor='white', edgecolor='none')
            logger.info(f"Correlation heatmap saved to: {output_path}")
            log_provenance(f"Generated correlation heatmap: {output_path}")
        except Exception as e:
            logger.error(f"Failed to save correlation heatmap: {e}")
            raise IOError(f"Could not save correlation heatmap to {output_path}: {e}")
        finally:
            plt.close(fig)
        return None
    else:
        return fig


def run_visualization_pipeline(
    input_path: str,
    output_dir: str,
    scatter_x: str = 'shannon_index',
    scatter_y: str = 'fluid_intelligence',
    histogram_col: str = 'shannon_index',
    dpi: int = 300
) -> dict:
    """
    Run the full visualization pipeline: generate scatter plot and histogram.
    
    Args:
        input_path: Path to the processed data CSV
        output_dir: Directory to save generated plots
        scatter_x: Column for scatter plot x-axis
        scatter_y: Column for scatter plot y-axis
        histogram_col: Column for histogram
        dpi: Resolution for output images
    
    Returns:
        Dictionary with paths to generated files
    """
    logger.info("Running visualization pipeline")
    
    # Ensure output directory exists
    ensure_directories()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load data
    logger.info(f"Loading data from: {input_path}")
    df = pd.read_csv(input_path)
    
    # Generate scatter plot
    scatter_output = str(output_path / "scatter_shannon_fi.png")
    generate_scatter_plot(
        df=df,
        x_col=scatter_x,
        y_col=scatter_y,
        output_path=scatter_output,
        xlabel='Shannon Index',
        ylabel='Fluid Intelligence',
        title='Gut Microbiome Diversity vs. Cognitive Performance',
        dpi=dpi
    )
    
    # Generate histogram
    histogram_output = str(output_path / "diversity_histogram.png")
    generate_histogram_plot(
        df=df,
        col=histogram_col,
        output_path=histogram_output,
        xlabel='Shannon Index',
        title='Distribution of Alpha Diversity',
        dpi=dpi
    )
    
    result = {
        'scatter_plot': scatter_output,
        'histogram_plot': histogram_output,
        'status': 'success'
    }
    
    logger.info(f"Visualization pipeline completed. Results: {result}")
    return result


def main():
    """Main entry point for visualization pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate visualization plots')
    parser.add_argument('--input', type=str, required=True, help='Path to input CSV file')
    parser.add_argument('--output-dir', type=str, required=True, help='Output directory for plots')
    parser.add_argument('--dpi', type=int, default=300, help='Resolution for output images')
    
    args = parser.parse_args()
    
    try:
        results = run_visualization_pipeline(
            input_path=args.input,
            output_dir=args.output_dir,
            dpi=args.dpi
        )
        print(f"Visualization pipeline completed successfully!")
        print(f"Scatter plot: {results['scatter_plot']}")
        print(f"Histogram plot: {results['histogram_plot']}")
    except Exception as e:
        logger.error(f"Visualization pipeline failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

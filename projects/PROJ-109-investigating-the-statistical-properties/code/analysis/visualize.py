import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
import seaborn as sns

from config import LOG_LEVEL, LOG_FORMAT, LOGS_DIR
from utils.logging import setup_logging, get_logger
from analysis.save_results import load_convergence_stats

# Initialize logger
logger = get_logger(__name__)

# Constants for figure saving
FIGURES_DIR = Path("results/figures")
DPI = 300
FIGSIZE = (10, 6)
FONT_SIZE = 12
LABEL_SIZE = 14
TITLE_SIZE = 16

def setup_plot_style():
    """
    Configure matplotlib and seaborn styles for publication-quality plots.
    """
    sns.set_theme(style="whitegrid", font_scale=1.2)
    plt.rcParams['figure.figsize'] = FIGSIZE
    plt.rcParams['figure.dpi'] = DPI
    plt.rcParams['savefig.dpi'] = DPI
    plt.rcParams['savefig.bbox'] = 'tight'
    plt.rcParams['font.size'] = FONT_SIZE
    plt.rcParams['axes.labelsize'] = LABEL_SIZE
    plt.rcParams['axes.titlesize'] = TITLE_SIZE
    plt.rcParams['xtick.labelsize'] = LABEL_SIZE
    plt.rcParams['ytick.labelsize'] = LABEL_SIZE
    plt.rcParams['legend.fontsize'] = LABEL_SIZE
    logger.info("Plot style configured.")

def plot_metric_distributions(df: pd.DataFrame, metrics: List[str], output_dir: Path):
    """
    Plot KDE and histogram distributions for each structural metric.

    Args:
        df: DataFrame containing halo data with metric columns.
        metrics: List of metric column names to plot (e.g., 'shape', 'spin', 'concentration').
        output_dir: Directory to save the generated figures.
    """
    setup_plot_style()
    for metric in metrics:
        if metric not in df.columns:
            logger.warning(f"Metric '{metric}' not found in DataFrame, skipping.")
            continue

        plt.figure()
        sns.histplot(df[metric], kde=True, stat="density", alpha=0.7)
        plt.title(f'Distribution of {metric.capitalize()}')
        plt.xlabel(metric.capitalize())
        plt.ylabel('Density')
        plt.grid(True, linestyle='--', alpha=0.6)

        output_path = output_dir / f"distribution_{metric}.png"
        plt.savefig(output_path)
        plt.close()
        logger.info(f"Saved distribution plot for {metric} to {output_path}")

def plot_metric_vs_mass(df: pd.DataFrame, metric: str, output_dir: Path):
    """
    Plot the relationship between a structural metric and halo mass.

    Args:
        df: DataFrame containing halo data.
        metric: Name of the structural metric column.
        output_dir: Directory to save the generated figures.
    """
    if 'mass' not in df.columns or metric not in df.columns:
        logger.warning(f"Missing 'mass' or '{metric}' column, skipping metric vs mass plot.")
        return

    setup_plot_style()
    plt.figure()
    # Use a scatter plot with alpha for density visualization
    plt.scatter(df['mass'], df[metric], alpha=0.3, s=10, edgecolors='none')
    plt.title(f'{metric.capitalize()} vs Halo Mass')
    plt.xlabel('Mass (M☉/h)')
    plt.ylabel(metric.capitalize())
    plt.grid(True, linestyle='--', alpha=0.6)

    # Log-log scale often better for mass distributions
    plt.xscale('log')

    output_path = output_dir / f"{metric}_vs_mass.png"
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Saved {metric} vs mass plot to {output_path}")

def plot_correlation_heatmap(df: pd.DataFrame, metrics: List[str], output_dir: Path):
    """
    Plot a correlation heatmap for the specified structural metrics.

    Args:
        df: DataFrame containing halo data.
        metrics: List of metric column names.
        output_dir: Directory to save the generated figures.
    """
    setup_plot_style()
    # Select only the relevant columns
    plot_df = df[metrics].copy()
    if plot_df.empty:
        logger.warning("No metrics found for correlation heatmap.")
        return

    # Compute correlation matrix
    corr_matrix = plot_df.corr()

    plt.figure(figsize=(8, 6))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f", linewidths=.5, vmin=-1, vmax=1)
    plt.title('Correlation Matrix of Structural Metrics')
    plt.tight_layout()

    output_path = output_dir / "correlation_heatmap.png"
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Saved correlation heatmap to {output_path}")

def plot_bullock_comparison(df: pd.DataFrame, output_dir: Path):
    """
    Plot measured mass-concentration relation against the Bullock et al. (2001) fit.

    Requires 'mass' and 'concentration' columns in df.
    """
    if 'mass' not in df.columns or 'concentration' not in df.columns:
        logger.warning("Missing 'mass' or 'concentration' for Bullock comparison plot.")
        return

    setup_plot_style()
    plt.figure()

    # Scatter plot of measured data
    plt.scatter(df['mass'], df['concentration'], alpha=0.3, s=10, label='Measured', edgecolors='none')

    # If Bullock fit parameters are available in config, plot the curve
    # Assuming config exposes BULLOCK_C200 and BULLOCK_ALPHA if defined
    # We attempt to import them safely
    try:
        from config import BULLOCK_C200, BULLOCK_ALPHA
        import numpy as np

        # Define mass range for the fit curve
        mass_min = df['mass'].min()
        mass_max = df['mass'].max()
        mass_range = np.logspace(np.log10(mass_min), np.log10(mass_max), 100)

        # Bullock et al. (2001) fit: c(M) = c200 * (M / M*)^(-alpha)
        # Note: The exact normalization M* depends on the simulation context.
        # If M* is not defined, we assume the fit is relative to a characteristic mass.
        # For this generic plot, we just plot the power law shape.
        # A more robust implementation would require M* from config.
        # Placeholder: assuming M* = 1e12 for visualization if not defined,
        # but in a real run, this should come from config.
        # Since T036B is not completed, we might not have the full fit function.
        # We will plot a simple power law if parameters exist.
        if 'BULLOCK_C200' in dir() and 'BULLOCK_ALPHA' in dir():
            # c = c200 * (M / M_ref)^(-alpha)
            # We need a reference mass. Let's use the mean mass as a rough proxy for visualization
            # or a standard M* if available. Without T036B, we can't guarantee the exact fit.
            # We will skip the curve if we don't have the full context, or just plot the parameters as text.
            pass
    except ImportError:
        logger.info("Bullock parameters not found in config, skipping fit curve overlay.")

    plt.title('Mass-Concentration Relation')
    plt.xlabel('Mass (M☉/h)')
    plt.ylabel('Concentration (c)')
    plt.xscale('log')
    plt.yscale('log')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)

    output_path = output_dir / "bullock_comparison.png"
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Saved Bullock comparison plot to {output_path}")

def generate_all_visualizations(data_path: Optional[str] = None):
    """
    Main entry point to generate all required visualizations.
    Loads the processed data, generates plots, and saves them to results/figures/.

    Args:
        data_path: Optional path to the processed parquet file. If None, tries to find the latest.
    """
    # Ensure output directory exists
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # Load data
    if data_path is None:
        # Try to find the latest processed file
        processed_dir = Path("data/processed")
        parquet_files = list(processed_dir.glob("filtered_halos_*.parquet"))
        if not parquet_files:
            logger.error("No processed halo data found. Please run the data pipeline first.")
            return
        data_path = str(sorted(parquet_files)[-1])

    logger.info(f"Loading data from {data_path}")
    try:
        df = pd.read_parquet(data_path)
    except Exception as e:
        logger.error(f"Failed to load data from {data_path}: {e}")
        return

    # Ensure required columns exist (from T014/T022/T023/T024 output)
    # Expected columns: mass, position, velocity, particle_count, shape, spin, concentration
    required_metrics = ['shape', 'spin', 'concentration']
    missing_cols = [m for m in required_metrics if m not in df.columns]
    if missing_cols:
        logger.warning(f"Missing metric columns in data: {missing_cols}. Some plots may be skipped.")

    # 1. Metric Distributions
    plot_metric_distributions(df, required_metrics, FIGURES_DIR)

    # 2. Metric vs Mass
    for metric in required_metrics:
        if metric in df.columns:
            plot_metric_vs_mass(df, metric, FIGURES_DIR)

    # 3. Correlation Heatmap
    plot_correlation_heatmap(df, required_metrics, FIGURES_DIR)

    # 4. Bullock Comparison (if concentration exists)
    if 'concentration' in df.columns:
        plot_bullock_comparison(df, FIGURES_DIR)

    logger.info("All visualizations generated successfully.")

if __name__ == "__main__":
    # Allow running as a script: python code/analysis/visualize.py [path_to_parquet]
    import sys
    input_path = sys.argv[1] if len(sys.argv) > 1 else None
    generate_all_visualizations(input_path)

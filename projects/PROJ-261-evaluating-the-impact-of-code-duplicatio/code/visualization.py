"""
Visualization module for code duplication impact analysis.
Generates scatter plots with regression lines using matplotlib.
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from config import (
    get_figure_format, get_figure_dpi, get_clone_thresholds,
    get_random_seed, get_correlation_method
)
from checksum_manifest import record_artifact_checksums

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_logging() -> logging.Logger:
    """Setup and return the logger for this module."""
    return logger

def load_correlation_data(
    data_path: Path,
    required_columns: List[str] = None
) -> Optional[pd.DataFrame]:
    """
    Load correlation results from CSV file.

    Args:
        data_path: Path to correlation_results.csv
        required_columns: List of columns that must exist

    Returns:
        DataFrame with correlation data, or None if loading fails
    """
    if required_columns is None:
        required_columns = ['clone_density', 'perplexity']

    try:
        if not data_path.exists():
            logger.warning(f"Correlation data file not found: {data_path}")
            return None

        df = pd.read_csv(data_path)
        logger.info(f"Loaded {len(df)} rows from {data_path}")

        # Check for required columns
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            logger.warning(f"Missing columns in correlation data: {missing_cols}")
            return None

        # Filter out rows with NaN or infinite values
        valid_rows = df.dropna(subset=required_columns)
        valid_rows = valid_rows[np.isfinite(valid_rows[required_columns]).all(axis=1)]

        if len(valid_rows) != len(df):
            logger.warning(
                f"Filtered {len(df) - len(valid_rows)} invalid rows "
                f"(NaN/infinite values)"
            )

        logger.info(f"Valid data points: {len(valid_rows)}")
        return valid_rows

    except Exception as e:
        logger.error(f"Failed to load correlation data: {e}")
        return None

def compute_regression(
    x: np.ndarray,
    y: np.ndarray
) -> Tuple[float, float, float, float]:
    """
    Compute linear regression for scatter plot.

    Args:
        x: X-axis values
        y: Y-axis values

    Returns:
        Tuple of (slope, intercept, r_value, p_value)
    """
    if len(x) < 2:
        return 0.0, 0.0, 0.0, 1.0

    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    return slope, intercept, r_value, p_value

def create_scatter_plot_with_regression(
    x: np.ndarray,
    y: np.ndarray,
    x_label: str,
    y_label: str,
    title: str,
    slope: float,
    intercept: float,
    r_value: float,
    p_value: float,
    output_path: Path,
    dpi: int = 300
) -> bool:
    """
    Create a scatter plot with regression line.

    Args:
        x: X-axis values
        y: Y-axis values
        x_label: X-axis label
        y_label: Y-axis label
        title: Plot title
        slope: Regression slope
        intercept: Regression intercept
        r_value: Correlation coefficient
        p_value: P-value
        output_path: Path to save the figure
        dpi: Figure DPI

    Returns:
        True if plot was successfully created and saved
    """
    try:
        fig, ax = plt.subplots(figsize=(10, 8), dpi=dpi)

        # Scatter plot
        ax.scatter(x, y, alpha=0.6, edgecolors='k', s=50)

        # Regression line
        x_line = np.linspace(x.min(), x.max(), 100)
        y_line = slope * x_line + intercept
        ax.plot(x_line, y_line, 'r-', linewidth=2, label='Regression line')

        # Labels and title
        ax.set_xlabel(x_label, fontsize=12)
        ax.set_ylabel(y_label, fontsize=12)
        ax.set_title(title, fontsize=14)

        # Add statistics annotation
        stats_text = f'r = {r_value:.3f}, p = {p_value:.3e}'
        ax.annotate(
            stats_text,
            xy=(0.05, 0.95),
            xycoords='axes fraction',
            fontsize=10,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        )

        # Grid and legend
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')

        # Save figure
        plt.tight_layout()
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
        plt.close(fig)

        logger.info(f"Saved scatter plot: {output_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to create scatter plot: {e}")
        return False

def create_clone_density_vs_perplexity_plot(
    df: pd.DataFrame,
    output_dir: Path,
    dpi: int = 300
) -> List[Path]:
    """
    Create scatter plot of clone density vs perplexity.

    Args:
        df: DataFrame with clone_density and perplexity columns
        output_dir: Directory to save figures
        dpi: Figure DPI

    Returns:
        List of saved figure paths
    """
    saved_paths = []

    if 'clone_density' not in df.columns or 'perplexity' not in df.columns:
        logger.warning("Missing clone_density or perplexity columns")
        return saved_paths

    x = df['clone_density'].values
    y = df['perplexity'].values

    # Filter valid data points
    valid_mask = np.isfinite(x) & np.isfinite(y)
    x_valid = x[valid_mask]
    y_valid = y[valid_mask]

    if len(x_valid) < 2:
        logger.warning("Insufficient valid data points for scatter plot")
        return saved_paths

    # Compute regression
    slope, intercept, r_value, p_value = compute_regression(x_valid, y_valid)

    # Create plot
    output_path = output_dir / "clone_density_vs_perplexity.png"
    success = create_scatter_plot_with_regression(
        x_valid, y_valid,
        "Clone Density", "Perplexity",
        "Clone Density vs Perplexity",
        slope, intercept, r_value, p_value,
        output_path, dpi
    )

    if success:
        saved_paths.append(output_path)

        # Also save PDF
        pdf_path = output_dir / "clone_density_vs_perplexity.pdf"
        try:
            fig, ax = plt.subplots(figsize=(10, 8), dpi=dpi)
            ax.scatter(x_valid, y_valid, alpha=0.6, edgecolors='k', s=50)
            x_line = np.linspace(x_valid.min(), x_valid.max(), 100)
            y_line = slope * x_line + intercept
            ax.plot(x_line, y_line, 'r-', linewidth=2, label='Regression line')
            ax.set_xlabel("Clone Density", fontsize=12)
            ax.set_ylabel("Perplexity", fontsize=12)
            ax.set_title("Clone Density vs Perplexity", fontsize=14)
            stats_text = f'r = {r_value:.3f}, p = {p_value:.3e}'
            ax.annotate(
                stats_text,
                xy=(0.05, 0.95),
                xycoords='axes fraction',
                fontsize=10,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            )
            ax.grid(True, alpha=0.3)
            ax.legend(loc='best')
            plt.tight_layout()
            plt.savefig(pdf_path, dpi=dpi, bbox_inches='tight')
            plt.close(fig)
            logger.info(f"Saved PDF plot: {pdf_path}")
            saved_paths.append(pdf_path)
        except Exception as e:
            logger.error(f"Failed to save PDF: {e}")

    return saved_paths

def create_clone_density_vs_accuracy_plot(
    df: pd.DataFrame,
    output_dir: Path,
    dpi: int = 300
) -> List[Path]:
    """
    Create scatter plot of clone density vs bug detection accuracy.

    Args:
        df: DataFrame with clone_density and accuracy columns
        output_dir: Directory to save figures
        dpi: Figure DPI

    Returns:
        List of saved figure paths
    """
    saved_paths = []

    if 'clone_density' not in df.columns:
        logger.warning("Missing clone_density column")
        return saved_paths

    if 'accuracy' not in df.columns:
        logger.warning("No accuracy column in DataFrame")
        return saved_paths

    x = df['clone_density'].values
    y = df['accuracy'].values

    # Filter valid data points
    valid_mask = np.isfinite(x) & np.isfinite(y)
    x_valid = x[valid_mask]
    y_valid = y[valid_mask]

    if len(x_valid) < 2:
        logger.warning("Insufficient valid data points for scatter plot")
        return saved_paths

    # Compute regression
    slope, intercept, r_value, p_value = compute_regression(x_valid, y_valid)

    # Create plot
    output_path = output_dir / "clone_density_vs_accuracy.png"
    success = create_scatter_plot_with_regression(
        x_valid, y_valid,
        "Clone Density", "Bug Detection Accuracy (pass@1)",
        "Clone Density vs Bug Detection Accuracy",
        slope, intercept, r_value, p_value,
        output_path, dpi
    )

    if success:
        saved_paths.append(output_path)

        # Also save PDF
        pdf_path = output_dir / "clone_density_vs_accuracy.pdf"
        try:
            fig, ax = plt.subplots(figsize=(10, 8), dpi=dpi)
            ax.scatter(x_valid, y_valid, alpha=0.6, edgecolors='k', s=50)
            x_line = np.linspace(x_valid.min(), x_valid.max(), 100)
            y_line = slope * x_line + intercept
            ax.plot(x_line, y_line, 'r-', linewidth=2, label='Regression line')
            ax.set_xlabel("Clone Density", fontsize=12)
            ax.set_ylabel("Bug Detection Accuracy (pass@1)", fontsize=12)
            ax.set_title("Clone Density vs Bug Detection Accuracy", fontsize=14)
            stats_text = f'r = {r_value:.3f}, p = {p_value:.3e}'
            ax.annotate(
                stats_text,
                xy=(0.05, 0.95),
                xycoords='axes fraction',
                fontsize=10,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            )
            ax.grid(True, alpha=0.3)
            ax.legend(loc='best')
            plt.tight_layout()
            plt.savefig(pdf_path, dpi=dpi, bbox_inches='tight')
            plt.close(fig)
            logger.info(f"Saved PDF plot: {pdf_path}")
            saved_paths.append(pdf_path)
        except Exception as e:
            logger.error(f"Failed to save PDF: {e}")

    return saved_paths

def create_sensitivity_analysis_plot(
    df: pd.DataFrame,
    output_dir: Path,
    dpi: int = 300
) -> List[Path]:
    """
    Create sensitivity analysis plot across thresholds.

    Args:
        df: DataFrame with threshold, correlation, and p_value columns
        output_dir: Directory to save figures
        dpi: Figure DPI

    Returns:
        List of saved figure paths
    """
    saved_paths = []

    required_cols = ['threshold', 'correlation', 'p_value']
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        logger.warning(f"Missing columns for sensitivity analysis: {missing_cols}")
        return saved_paths

    thresholds = df['threshold'].values
    correlations = df['correlation'].values
    p_values = df['p_value'].values

    valid_mask = np.isfinite(correlations) & np.isfinite(p_values)
    thresholds_valid = thresholds[valid_mask]
    correlations_valid = correlations[valid_mask]
    p_values_valid = p_values[valid_mask]

    if len(thresholds_valid) < 2:
        logger.warning("Insufficient data points for sensitivity analysis plot")
        return saved_paths

    # Create line plot
    try:
        fig, ax1 = plt.subplots(figsize=(10, 6), dpi=dpi)

        # Correlation line
        ax1.plot(thresholds_valid, correlations_valid, 'bo-',
                linewidth=2, markersize=8, label='Correlation (r)')
        ax1.set_xlabel('Clone Detection Threshold', fontsize=12)
        ax1.set_ylabel('Spearman Correlation (r)', fontsize=12, color='b')
        ax1.tick_params(axis='y', labelcolor='b')
        ax1.grid(True, alpha=0.3)

        # P-value secondary axis
        ax2 = ax1.twinx()
        ax2.plot(thresholds_valid, p_values_valid, 'rs--',
                linewidth=2, markersize=8, label='P-value')
        ax2.set_ylabel('P-value', fontsize=12, color='r')
        ax2.tick_params(axis='y', labelcolor='r')

        # Combined legend
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='best')

        plt.title('Sensitivity Analysis: Correlation vs Threshold', fontsize=14)
        plt.tight_layout()

        output_path = output_dir / "sensitivity_analysis.png"
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
        logger.info(f"Saved sensitivity analysis plot: {output_path}")
        saved_paths.append(output_path)

        # Save PDF
        pdf_path = output_dir / "sensitivity_analysis.pdf"
        plt.savefig(pdf_path, dpi=dpi, bbox_inches='tight')
        logger.info(f"Saved sensitivity analysis PDF: {pdf_path}")
        saved_paths.append(pdf_path)

    except Exception as e:
        logger.error(f"Failed to create sensitivity analysis plot: {e}")

    return saved_paths

def generate_all_visualizations(
    correlation_data_path: Path,
    output_dir: Path
) -> Dict[str, List[Path]]:
    """
    Generate all visualizations from correlation results.

    Args:
        correlation_data_path: Path to correlation_results.csv
        output_dir: Directory to save all figures

    Returns:
        Dictionary mapping plot type to list of saved paths
    """
    results = {
        'perplexity_plot': [],
        'accuracy_plot': [],
        'sensitivity_plot': []
    }

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load correlation data
    df = load_correlation_data(correlation_data_path)
    if df is None or len(df) == 0:
        logger.warning("No valid correlation data to visualize")
        return results

    dpi = get_figure_dpi()

    # Clone density vs perplexity
    results['perplexity_plot'] = create_clone_density_vs_perplexity_plot(
        df, output_dir, dpi
    )

    # Clone density vs accuracy (if accuracy column exists)
    results['accuracy_plot'] = create_clone_density_vs_accuracy_plot(
        df, output_dir, dpi
    )

    # Sensitivity analysis (if threshold data exists)
    results['sensitivity_plot'] = create_sensitivity_analysis_plot(
        df, output_dir, dpi
    )

    # Count total plots
    total_plots = sum(len(v) for v in results.values())
    logger.info(f"Generated {total_plots} visualization files")

    return results

def main():
    """Main entry point for visualization generation."""
    logger.info("Starting visualization generation")

    # Get paths from config
    correlation_data_path = Path("data/analysis/correlation_results.csv")
    output_dir = Path("data/analysis/figures")

    # Generate visualizations
    results = generate_all_visualizations(correlation_data_path, output_dir)

    # Record checksums for generated figures
    all_paths = []
    for paths in results.values():
        all_paths.extend(paths)

    if all_paths:
        record_artifact_checksums(all_paths, "visualization_outputs")
        logger.info(f"Recorded checksums for {len(all_paths)} visualization files")

    # Summary
    total_files = sum(len(v) for v in results.values())
    if total_files == 0:
        logger.warning("No visualization files were generated")
    else:
        logger.info(f"Successfully generated {total_files} visualization files")

    logger.info("Visualization generation complete")
    return results

if __name__ == "__main__":
    main()
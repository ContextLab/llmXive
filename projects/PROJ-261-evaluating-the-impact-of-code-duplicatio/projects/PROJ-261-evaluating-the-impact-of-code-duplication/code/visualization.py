"""
Visualization module for code duplication impact analysis.
Generates scatter plots with regression lines for clone density vs perplexity/accuracy.
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

# Import from config module
sys.path.insert(0, str(Path(__file__).parent))
from config import (
    get_clone_thresholds,
    get_figure_dpi,
    get_figure_format,
    get_random_seed,
)

# Setup logging
logger = logging.getLogger(__name__)

def setup_logging() -> logging.Logger:
    """Configure logging for visualization module."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                Path(__file__).parent.parent / 'data' / 'visualization.log'
            )
        ]
    )
    return logger

def load_correlation_data(
    correlation_path: Optional[Path] = None,
    clone_metrics_path: Optional[Path] = None,
    perplexity_path: Optional[Path] = None,
    accuracy_path: Optional[Path] = None
) -> Dict[str, pd.DataFrame]:
    """
    Load correlation results and supporting metrics data.

    Args:
        correlation_path: Path to correlation_results.csv
        clone_metrics_path: Path to clone_metrics.csv
        perplexity_path: Path to perplexity_scores.csv
        accuracy_path: Path to bug_detection_results.csv

    Returns:
        Dictionary with loaded DataFrames
    """
    data = {}

    # Set default paths relative to project root
    project_root = Path(__file__).parent.parent
    if correlation_path is None:
        correlation_path = project_root / 'data' / 'analysis' / 'correlation_results.csv'
    if clone_metrics_path is None:
        clone_metrics_path = project_root / 'data' / 'processed' / 'clone_metrics.csv'
    if perplexity_path is None:
        perplexity_path = project_root / 'data' / 'processed' / 'perplexity_scores.csv'
    if accuracy_path is None:
        accuracy_path = project_root / 'data' / 'processed' / 'bug_detection_results.csv'

    # Load correlation results if available
    if correlation_path.exists():
        try:
            data['correlation'] = pd.read_csv(correlation_path)
            logger.info(f"Loaded correlation results from {correlation_path}")
        except Exception as e:
            logger.warning(f"Could not load correlation results: {e}")
    else:
        logger.warning(f"Correlation results not found at {correlation_path}")

    # Load clone metrics
    if clone_metrics_path.exists():
        try:
            data['clone_metrics'] = pd.read_csv(clone_metrics_path)
            logger.info(f"Loaded clone metrics from {clone_metrics_path}")
        except Exception as e:
            logger.warning(f"Could not load clone metrics: {e}")
    else:
        logger.warning(f"Clone metrics not found at {clone_metrics_path}")

    # Load perplexity scores
    if perplexity_path.exists():
        try:
            data['perplexity'] = pd.read_csv(perplexity_path)
            logger.info(f"Loaded perplexity scores from {perplexity_path}")
        except Exception as e:
            logger.warning(f"Could not load perplexity scores: {e}")
    else:
        logger.warning(f"Perplexity scores not found at {perplexity_path}")

    # Load accuracy results
    if accuracy_path.exists():
        try:
            data['accuracy'] = pd.read_csv(accuracy_path)
            logger.info(f"Loaded accuracy results from {accuracy_path}")
        except Exception as e:
            logger.warning(f"Could not load accuracy results: {e}")
    else:
        logger.warning(f"Accuracy results not found at {accuracy_path}")

    return data

def compute_regression(
    x: np.ndarray,
    y: np.ndarray
) -> Tuple[float, float, float, float]:
    """
    Compute linear regression line and statistics.

    Args:
        x: Independent variable array
        y: Dependent variable array

    Returns:
        Tuple of (slope, intercept, r_value, p_value)
    """
    if len(x) < 2 or len(y) < 2:
        logger.warning("Insufficient data points for regression")
        return 0.0, 0.0, 0.0, 1.0

    try:
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        return slope, intercept, r_value, p_value
    except Exception as e:
        logger.error(f"Regression computation failed: {e}")
        return 0.0, 0.0, 0.0, 1.0

def create_scatter_plot_with_regression(
    x: np.ndarray,
    y: np.ndarray,
    x_label: str,
    y_label: str,
    title: str,
    output_path: Path,
    r_value: Optional[float] = None,
    p_value: Optional[float] = None,
    threshold_lines: Optional[List[float]] = None,
    threshold_label: Optional[str] = None
) -> Path:
    """
    Create a scatter plot with regression line and optional threshold lines.

    Args:
        x: X-axis data
        y: Y-axis data
        x_label: X-axis label
        y_label: Y-axis label
        title: Plot title
        output_path: Path to save the figure
        r_value: Correlation coefficient (shown in title if provided)
        p_value: P-value (shown in title if provided)
        threshold_lines: List of threshold values for vertical lines
        threshold_label: Label for threshold lines

    Returns:
        Path where the figure was saved
    """
    # Set random seed for reproducibility
    seed = get_random_seed()
    np.random.seed(seed)

    # Create figure with publication-ready settings
    dpi = get_figure_dpi()
    fig, ax = plt.subplots(figsize=(10, 8), dpi=dpi)

    # Create scatter plot
    scatter = ax.scatter(
        x, y,
        alpha=0.6,
        edgecolors='black',
        linewidth=0.5,
        s=50,
        c='steelblue'
    )

    # Add regression line if data exists
    if len(x) >= 2 and len(y) >= 2:
        slope, intercept, _, _ = compute_regression(x, y)
        x_range = np.linspace(min(x), max(x), 100)
        y_range = slope * x_range + intercept
        ax.plot(
            x_range, y_range,
            'r-',
            linewidth=2,
            label=f'Regression (slope={slope:.4f})'
        )

    # Add threshold lines if provided
    if threshold_lines:
        for threshold in threshold_lines:
            ax.axvline(
                x=threshold,
                color='green',
                linestyle='--',
                linewidth=1.5,
                alpha=0.7,
                label=f'{threshold_label}={threshold:.1f}' if threshold_label else None
            )

    # Set labels and title
    ax.set_xlabel(x_label, fontsize=12)
    ax.set_ylabel(y_label, fontsize=12)

    # Add correlation info to title
    if r_value is not None and p_value is not None:
        significance = "***" if p_value < 0.001 else "**" if p_value < 0.01 else "*" if p_value < 0.05 else "ns"
        title = f"{title}\n(r={r_value:.3f}, p={p_value:.4f}{significance})"
    ax.set_title(title, fontsize=14)

    # Add legend
    ax.legend(loc='best', fontsize=10)

    # Add grid
    ax.grid(True, alpha=0.3, linestyle=':')

    # Set axis limits with padding
    x_margin = (max(x) - min(x)) * 0.05 if max(x) != min(x) else 0.5
    y_margin = (max(y) - min(y)) * 0.05 if max(y) != min(y) else 0.5
    ax.set_xlim(min(x) - x_margin, max(x) + x_margin)
    ax.set_ylim(min(y) - y_margin, max(y) + y_margin)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save figure in multiple formats
    formats = get_figure_format()
    if not isinstance(formats, list):
        formats = [formats]

    saved_paths = []
    for fmt in formats:
        save_path = output_path.with_suffix(f'.{fmt}')
        fig.savefig(
            save_path,
            dpi=dpi,
            bbox_inches='tight',
            facecolor='white',
            edgecolor='none'
        )
        saved_paths.append(save_path)
        logger.info(f"Saved figure: {save_path}")

    plt.close(fig)

    # Return the first saved path
    return saved_paths[0] if saved_paths else output_path

def create_clone_density_vs_perplexity_plot(
    clone_metrics: pd.DataFrame,
    perplexity_scores: pd.DataFrame,
    output_dir: Path
) -> List[Path]:
    """
    Create scatter plot of clone density vs perplexity.

    Args:
        clone_metrics: DataFrame with clone density data
        perplexity_scores: DataFrame with perplexity scores
        output_dir: Directory to save figures

    Returns:
        List of paths where figures were saved
    """
    saved_paths = []

    # Merge data on file identifier
    try:
        # Try common column names for joining
        join_key = None
        for key in ['file_id', 'file_path', 'file', 'id', 'segment_id']:
            if key in clone_metrics.columns and key in perplexity_scores.columns:
                join_key = key
                break

        if join_key is None:
            # Fall back to index if no common key
            merged = pd.concat([
                clone_metrics[['clone_density']] if 'clone_density' in clone_metrics.columns else clone_metrics,
                perplexity_scores[['perplexity']] if 'perplexity' in perplexity_scores.columns else perplexity_scores
            ], axis=1)
        else:
            merged = pd.merge(clone_metrics, perplexity_scores, on=join_key, how='inner')

        # Extract data
        if 'clone_density' in merged.columns and 'perplexity' in merged.columns:
            x = merged['clone_density'].dropna().values
            y = merged['perplexity'].dropna().values

            # Compute correlation
            r_value, p_value = None, None
            if len(x) >= 2 and len(y) >= 2:
                _, _, r_value, p_value, _ = stats.pearsonr(x, y)

            # Create plot
            output_path = output_dir / 'clone_density_vs_perplexity'
            saved_path = create_scatter_plot_with_regression(
                x=x,
                y=y,
                x_label='Clone Density',
                y_label='Perplexity',
                title='Clone Density vs Model Perplexity',
                output_path=output_path,
                r_value=r_value,
                p_value=p_value,
                threshold_lines=get_clone_thresholds(),
                threshold_label='Clone Threshold'
            )
            saved_paths.append(saved_path)
        else:
            logger.warning("Required columns not found in merged data")

    except Exception as e:
        logger.error(f"Failed to create clone density vs perplexity plot: {e}")

    return saved_paths

def create_clone_density_vs_accuracy_plot(
    clone_metrics: pd.DataFrame,
    accuracy_results: pd.DataFrame,
    output_dir: Path
) -> List[Path]:
    """
    Create scatter plot of clone density vs bug detection accuracy.

    Args:
        clone_metrics: DataFrame with clone density data
        accuracy_results: DataFrame with accuracy results
        output_dir: Directory to save figures

    Returns:
        List of paths where figures were saved
    """
    saved_paths = []

    try:
        # Merge data on file identifier
        join_key = None
        for key in ['file_id', 'file_path', 'file', 'id', 'segment_id']:
            if key in clone_metrics.columns and key in accuracy_results.columns:
                join_key = key
                break

        if join_key is None:
            merged = pd.concat([
                clone_metrics[['clone_density']] if 'clone_density' in clone_metrics.columns else clone_metrics,
                accuracy_results[['accuracy']] if 'accuracy' in accuracy_results.columns else accuracy_results
            ], axis=1)
        else:
            merged = pd.merge(clone_metrics, accuracy_results, on=join_key, how='inner')

        # Extract data
        if 'clone_density' in merged.columns and 'accuracy' in merged.columns:
            x = merged['clone_density'].dropna().values
            y = merged['accuracy'].dropna().values

            # Compute correlation
            r_value, p_value = None, None
            if len(x) >= 2 and len(y) >= 2:
                _, _, r_value, p_value, _ = stats.pearsonr(x, y)

            # Create plot
            output_path = output_dir / 'clone_density_vs_accuracy'
            saved_path = create_scatter_plot_with_regression(
                x=x,
                y=y,
                x_label='Clone Density',
                y_label='Bug Detection Accuracy (pass@1)',
                title='Clone Density vs Bug Detection Accuracy',
                output_path=output_path,
                r_value=r_value,
                p_value=p_value,
                threshold_lines=get_clone_thresholds(),
                threshold_label='Clone Threshold'
            )
            saved_paths.append(saved_path)
        else:
            logger.warning("Required columns not found in merged data")

    except Exception as e:
        logger.error(f"Failed to create clone density vs accuracy plot: {e}")

    return saved_paths

def create_sensitivity_analysis_plot(
    correlation_data: pd.DataFrame,
    output_dir: Path
) -> List[Path]:
    """
    Create sensitivity analysis plot across different clone detection thresholds.

    Args:
        correlation_data: DataFrame with sensitivity analysis results
        output_dir: Directory to save figures

    Returns:
        List of paths where figures were saved
    """
    saved_paths = []

    try:
        # Expected columns for sensitivity analysis
        expected_cols = ['threshold', 'correlation_perplexity', 'correlation_accuracy',
                       'p_value_perplexity', 'p_value_accuracy']

        # Check if we have the required columns
        available_cols = [col for col in expected_cols if col in correlation_data.columns]

        if len(available_cols) >= 2:
            thresholds = correlation_data['threshold'].values

            # Create figure with subplots
            dpi = get_figure_dpi()
            fig, axes = plt.subplots(1, 2, figsize=(14, 6), dpi=dpi)

            # Plot correlation vs threshold for perplexity
            if 'correlation_perplexity' in correlation_data.columns:
                axes[0].plot(
                    thresholds,
                    correlation_data['correlation_perplexity'].values,
                    'bo-',
                    linewidth=2,
                    markersize=8,
                    label='Perplexity Correlation'
                )
                axes[0].set_xlabel('Clone Detection Threshold')
                axes[0].set_ylabel('Correlation Coefficient (Spearman)')
                axes[0].set_title('Sensitivity: Clone Threshold vs Perplexity Correlation')
                axes[0].grid(True, alpha=0.3)
                axes[0].legend()

            # Plot correlation vs threshold for accuracy
            if 'correlation_accuracy' in correlation_data.columns:
                axes[1].plot(
                    thresholds,
                    correlation_data['correlation_accuracy'].values,
                    'ro-',
                    linewidth=2,
                    markersize=8,
                    label='Accuracy Correlation'
                )
                axes[1].set_xlabel('Clone Detection Threshold')
                axes[1].set_ylabel('Correlation Coefficient (Spearman)')
                axes[1].set_title('Sensitivity: Clone Threshold vs Accuracy Correlation')
                axes[1].grid(True, alpha=0.3)
                axes[1].legend()

            # Adjust layout
            plt.tight_layout()

            # Save figure
            output_path = output_dir / 'sensitivity_analysis'
            formats = get_figure_format()
            if not isinstance(formats, list):
                formats = [formats]

            for fmt in formats:
                save_path = output_path.with_suffix(f'.{fmt}')
                fig.savefig(
                    save_path,
                    dpi=dpi,
                    bbox_inches='tight',
                    facecolor='white',
                    edgecolor='none'
                )
                saved_paths.append(save_path)
                logger.info(f"Saved sensitivity analysis: {save_path}")

            plt.close(fig)
        else:
            logger.warning("Missing required columns for sensitivity analysis plot")

    except Exception as e:
        logger.error(f"Failed to create sensitivity analysis plot: {e}")

    return saved_paths

def generate_all_visualizations(
    output_dir: Optional[Path] = None
) -> Dict[str, List[Path]]:
    """
    Generate all visualizations for the analysis.

    Args:
        output_dir: Directory to save all figures (default: data/analysis/figures)

    Returns:
        Dictionary mapping plot type to list of saved paths
    """
    # Set default output directory
    if output_dir is None:
        project_root = Path(__file__).parent.parent
        output_dir = project_root / 'data' / 'analysis' / 'figures'

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Generating visualizations to {output_dir}")

    # Load all data
    data = load_correlation_data()

    results = {
        'clone_density_vs_perplexity': [],
        'clone_density_vs_accuracy': [],
        'sensitivity_analysis': []
    }

    # Create clone density vs perplexity plot
    if 'clone_metrics' in data and 'perplexity' in data:
        results['clone_density_vs_perplexity'] = create_clone_density_vs_perplexity_plot(
            data['clone_metrics'],
            data['perplexity'],
            output_dir
        )

    # Create clone density vs accuracy plot
    if 'clone_metrics' in data and 'accuracy' in data:
        results['clone_density_vs_accuracy'] = create_clone_density_vs_accuracy_plot(
            data['clone_metrics'],
            data['accuracy'],
            output_dir
        )

    # Create sensitivity analysis plot
    if 'correlation' in data and not data['correlation'].empty:
        results['sensitivity_analysis'] = create_sensitivity_analysis_plot(
            data['correlation'],
            output_dir
        )

    # Log summary
    total_plots = sum(len(paths) for paths in results.values())
    logger.info(f"Generated {total_plots} visualization files")

    return results

def main() -> int:
    """
    Main entry point for visualization generation.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger = setup_logging()
    logger.info("Starting visualization generation")

    try:
        # Generate all visualizations
        results = generate_all_visualizations()

        # Check if any plots were generated
        total_plots = sum(len(paths) for paths in results.values())
        if total_plots == 0:
            logger.warning("No visualizations were generated")
            # Still return success as this may be expected if data is missing
            return 0

        logger.info(f"Successfully generated {total_plots} visualization files")
        return 0

    except Exception as e:
        logger.error(f"Visualization generation failed: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())
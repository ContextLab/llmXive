"""
Visualization module for generating scatter plots with regression lines.

This module creates publication-ready visualizations for the code duplication
impact analysis pipeline, specifically for User Story 3 (Sensitivity Analysis
and Visualizations).

Outputs scatter plots of:
- Clone density vs. perplexity scores
- Clone density vs. bug detection accuracy

All plots include regression lines, confidence intervals, and proper formatting
for publication.
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

# Import project configuration
from config import (
    PROJECT_ROOT,
    RANDOM_SEED,
    OUTPUT_DIR,
    FIGURES_DIR,
    CORRELATION_RESULTS_PATH,
    CLONE_DENSITY_THRESHOLD_07,
    CLONE_DENSITY_THRESHOLD_08,
    CLONE_DENSITY_THRESHOLD_09,
)

# Import checksum tracking for artifact verification
from checksum_manifest import compute_file_checksum, record_artifact_checksums

# Set up logging
logger = logging.getLogger(__name__)

# Constants
DPI = 300
FIGURE_WIDTH = 10
FIGURE_HEIGHT = 8
FONT_SIZE = 12
TICK_SIZE = 10
LINE_WIDTH = 2
MARKER_SIZE = 50
ALPHA = 0.6
GRID_ALPHA = 0.3


def setup_logging() -> logging.Logger:
    """Configure logging for visualization module."""
    log_dir = PROJECT_ROOT / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f'visualization_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logger


def load_correlation_data(
    data_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Load correlation results data from CSV file.
    
    Args:
        data_path: Path to correlation results CSV. Defaults to config path.
    
    Returns:
        DataFrame containing correlation data with clone density, perplexity,
        and accuracy metrics.
    
    Raises:
        FileNotFoundError: If the data file does not exist.
        ValueError: If required columns are missing.
    """
    if data_path is None:
        data_path = CORRELATION_RESULTS_PATH
    
    data_path = PROJECT_ROOT / data_path if not data_path.is_absolute() else data_path
    
    if not data_path.exists():
        raise FileNotFoundError(f"Correlation data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    
    # Validate required columns
    required_columns = ['clone_density', 'perplexity', 'accuracy']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    logger.info(f"Loaded {len(df)} records from {data_path}")
    return df


def compute_regression(
    x: np.ndarray,
    y: np.ndarray
) -> Tuple[float, float, float, float]:
    """
    Compute linear regression line and statistics.
    
    Args:
        x: Independent variable values.
        y: Dependent variable values.
    
    Returns:
        Tuple of (slope, intercept, r_value, p_value).
    """
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    return slope, intercept, r_value, p_value


def create_scatter_plot_with_regression(
    x: np.ndarray,
    y: np.ndarray,
    x_label: str,
    y_label: str,
    title: str,
    output_path: Path,
    color: str = '#2E86AB',
    show_confidence: bool = True,
    confidence_level: float = 0.95
) -> None:
    """
    Create a scatter plot with regression line and save to file.
    
    Args:
        x: Independent variable values.
        y: Dependent variable values.
        x_label: Label for x-axis.
        y_label: Label for y-axis.
        title: Plot title.
        output_path: Path to save the figure.
        color: Color for scatter points and regression line.
        show_confidence: Whether to show confidence interval shading.
        confidence_level: Confidence level for interval (default 0.95).
    """
    fig, ax = plt.subplots(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT), dpi=DPI)
    
    # Scatter plot
    ax.scatter(x, y, alpha=ALPHA, s=MARKER_SIZE, color=color,
              edgecolors='black', linewidth=0.5, label='Data points')
    
    # Regression line
    slope, intercept, r_value, p_value = compute_regression(x, y)
    x_min, x_max = x.min(), x.max()
    x_line = np.linspace(x_min, x_max, 100)
    y_line = slope * x_line + intercept
    
    ax.plot(x_line, y_line, color=color, linewidth=LINE_WIDTH,
           label=f'Regression (r={r_value:.3f}, p={p_value:.3e})')
    
    # Confidence interval shading
    if show_confidence:
        residuals = y - (slope * x + intercept)
        std_residual = np.std(residuals)
        z_score = stats.norm.ppf((1 + confidence_level) / 2)
        margin = z_score * std_residual
        
        y_lower = slope * x_line + intercept - margin
        y_upper = slope * x_line + intercept + margin
        
        ax.fill_between(x_line, y_lower, y_upper, alpha=0.2, color=color,
                      label=f'{confidence_level*100:.0f}% CI')
    
    # Formatting
    ax.set_xlabel(x_label, fontsize=FONT_SIZE)
    ax.set_ylabel(y_label, fontsize=FONT_SIZE)
    ax.set_title(title, fontsize=FONT_SIZE + 2, fontweight='bold')
    ax.legend(loc='best', fontsize=TICK_SIZE)
    ax.grid(True, alpha=GRID_ALPHA, linestyle='--')
    
    ax.tick_params(axis='both', which='major', labelsize=TICK_SIZE)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save in both PNG and PDF formats
    output_path_png = output_path.with_suffix('.png')
    output_path_pdf = output_path.with_suffix('.pdf')
    
    plt.savefig(output_path_png, dpi=DPI, bbox_inches='tight',
               facecolor='white', edgecolor='none')
    plt.savefig(output_path_pdf, bbox_inches='tight',
               facecolor='white', edgecolor='none')
    
    logger.info(f"Saved plot to {output_path_png} and {output_path_pdf}")
    
    plt.close(fig)


def create_clone_density_vs_perplexity_plot(
    df: pd.DataFrame,
    output_dir: Optional[Path] = None
) -> List[Path]:
    """
    Create scatter plot of clone density vs. perplexity scores.
    
    Args:
        df: DataFrame with clone_density and perplexity columns.
        output_dir: Directory to save plots. Defaults to FIGURES_DIR.
    
    Returns:
        List of paths to saved plot files.
    """
    if output_dir is None:
        output_dir = FIGURES_DIR
    
    output_dir = PROJECT_ROOT / output_dir if not output_dir.is_absolute() else output_dir
    
    x = df['clone_density'].values
    y = df['perplexity'].values
    
    output_path = output_dir / 'clone_density_vs_perplexity'
    
    create_scatter_plot_with_regression(
        x=x,
        y=y,
        x_label='Clone Density',
        y_label='Perplexity (log loss)',
        title='Clone Density vs. Model Perplexity',
        output_path=output_path,
        color='#2E86AB'
    )
    
    return [
        output_path.with_suffix('.png'),
        output_path.with_suffix('.pdf')
    ]


def create_clone_density_vs_accuracy_plot(
    df: pd.DataFrame,
    output_dir: Optional[Path] = None
) -> List[Path]:
    """
    Create scatter plot of clone density vs. bug detection accuracy.
    
    Args:
        df: DataFrame with clone_density and accuracy columns.
        output_dir: Directory to save plots. Defaults to FIGURES_DIR.
    
    Returns:
        List of paths to saved plot files.
    """
    if output_dir is None:
        output_dir = FIGURES_DIR
    
    output_dir = PROJECT_ROOT / output_dir if not output_dir.is_absolute() else output_dir
    
    x = df['clone_density'].values
    y = df['accuracy'].values
    
    output_path = output_dir / 'clone_density_vs_accuracy'
    
    create_scatter_plot_with_regression(
        x=x,
        y=y,
        x_label='Clone Density',
        y_label='Bug Detection Accuracy (pass@1)',
        title='Clone Density vs. Bug Detection Accuracy',
        output_path=output_path,
        color='#A23B72'
    )
    
    return [
        output_path.with_suffix('.png'),
        output_path.with_suffix('.pdf')
    ]


def create_sensitivity_analysis_plot(
    df: pd.DataFrame,
    output_dir: Optional[Path] = None
) -> List[Path]:
    """
    Create sensitivity analysis plot across different clone detection thresholds.
    
    Args:
        df: DataFrame with clone_density, perplexity, accuracy columns.
        output_dir: Directory to save plots. Defaults to FIGURES_DIR.
    
    Returns:
        List of paths to saved plot files.
    """
    if output_dir is None:
        output_dir = FIGURES_DIR
    
    output_dir = PROJECT_ROOT / output_dir if not output_dir.is_absolute() else output_dir
    
    thresholds = [
        (CLONE_DENSITY_THRESHOLD_07, '#2E86AB'),
        (CLONE_DENSITY_THRESHOLD_08, '#A23B72'),
        (CLONE_DENSITY_THRESHOLD_09, '#F18F01')
    ]
    
    fig, ax = plt.subplots(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT), dpi=DPI)
    
    for threshold, color in thresholds:
        mask = df['clone_density'] >= threshold
        if mask.sum() > 0:
            x = df.loc[mask, 'clone_density'].values
            y = df.loc[mask, 'perplexity'].values
            
            slope, intercept, r_value, p_value = compute_regression(x, y)
            
            x_min, x_max = x.min(), x.max()
            x_line = np.linspace(x_min, x_max, 100)
            y_line = slope * x_line + intercept
            
            ax.plot(x_line, y_line, color=color, linewidth=LINE_WIDTH,
                   label=f'Threshold ≥ {threshold:.1f} (r={r_value:.3f})')
            ax.scatter(x, y, alpha=ALPHA, s=MARKER_SIZE, color=color,
                     edgecolors='black', linewidth=0.5)
    
    ax.set_xlabel('Clone Density', fontsize=FONT_SIZE)
    ax.set_ylabel('Perplexity (log loss)', fontsize=FONT_SIZE)
    ax.set_title('Sensitivity Analysis: Clone Detection Thresholds',
                fontsize=FONT_SIZE + 2, fontweight='bold')
    ax.legend(loc='best', fontsize=TICK_SIZE)
    ax.grid(True, alpha=GRID_ALPHA, linestyle='--')
    ax.tick_params(axis='both', which='major', labelsize=TICK_SIZE)
    
    output_path = output_dir / 'sensitivity_analysis'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    plt.savefig(output_path.with_suffix('.png'), dpi=DPI, bbox_inches='tight',
               facecolor='white', edgecolor='none')
    plt.savefig(output_path.with_suffix('.pdf'), bbox_inches='tight',
               facecolor='white', edgecolor='none')
    
    logger.info(f"Saved sensitivity analysis plot to {output_dir}")
    
    plt.close(fig)
    
    return [
        output_path.with_suffix('.png'),
        output_path.with_suffix('.pdf')
    ]


def generate_all_visualizations(
    data_path: Optional[Path] = None,
    output_dir: Optional[Path] = None
) -> Dict[str, List[Path]]:
    """
    Generate all visualization outputs for the analysis.
    
    Args:
        data_path: Path to correlation results CSV.
        output_dir: Directory to save plots.
    
    Returns:
        Dictionary mapping plot names to lists of saved file paths.
    """
    logger.info("Starting visualization generation...")
    
    # Load data
    df = load_correlation_data(data_path)
    
    # Set output directory
    if output_dir is None:
        output_dir = FIGURES_DIR
    output_dir = PROJECT_ROOT / output_dir if not output_dir.is_absolute() else output_dir
    
    # Ensure directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    # Generate individual plots
    results['clone_density_vs_perplexity'] = create_clone_density_vs_perplexity_plot(
        df=df, output_dir=output_dir
    )
    logger.info("Generated clone density vs. perplexity plot")
    
    results['clone_density_vs_accuracy'] = create_clone_density_vs_accuracy_plot(
        df=df, output_dir=output_dir
    )
    logger.info("Generated clone density vs. accuracy plot")
    
    results['sensitivity_analysis'] = create_sensitivity_analysis_plot(
        df=df, output_dir=output_dir
    )
    logger.info("Generated sensitivity analysis plot")
    
    # Record checksums for all generated files
    all_files = []
    for paths in results.values():
        all_files.extend(paths)
    
    for file_path in all_files:
        checksum = compute_file_checksum(file_path)
        logger.info(f"Computed checksum for {file_path}: {checksum[:16]}...")
    
    logger.info(f"Successfully generated {len(all_files)} visualization files")
    
    return results


def main() -> None:
    """Main entry point for visualization generation."""
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("Starting visualization generation for code duplication analysis")
    logger.info("=" * 60)
    
    try:
        results = generate_all_visualizations()
        
        # Print summary
        logger.info("\nVisualization Summary:")
        for name, paths in results.items():
            logger.info(f"  {name}:")
            for path in paths:
                logger.info(f"    - {path}")
        
        logger.info("\nVisualization generation completed successfully!")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during visualization generation: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    main()

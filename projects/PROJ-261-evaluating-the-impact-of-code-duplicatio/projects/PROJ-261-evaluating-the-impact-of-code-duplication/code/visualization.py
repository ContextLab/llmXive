"""
Visualization module for code duplication impact analysis.

Generates publication-ready scatter plots with regression lines,
clone density vs perplexity plots, clone density vs accuracy plots,
and sensitivity analysis plots.

All plots are saved to data/analysis/figures/ in both PNG and PDF formats.
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

# Import from config for reproducibility
try:
    from config import DEFAULT_SEED, CLONE_THRESHOLD_DEFAULT
except ImportError:
    DEFAULT_SEED = 42
    CLONE_THRESHOLD_DEFAULT = 0.7

# Configure logging
logger = logging.getLogger(__name__)

def setup_logging() -> logging.Logger:
    """Setup logging for visualization module."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/visualization.log')
        ]
    )
    return logger

def load_correlation_data(data_path: str) -> pd.DataFrame:
    """
    Load correlation data from CSV file.
    
    Args:
        data_path: Path to the correlation results CSV file.
    
    Returns:
        DataFrame with correlation data.
    """
    logger.info(f"Loading correlation data from {data_path}")
    try:
        df = pd.read_csv(data_path)
        logger.info(f"Loaded {len(df)} records from {data_path}")
        return df
    except FileNotFoundError:
        logger.error(f"Correlation data file not found: {data_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading correlation data: {e}")
        raise

def compute_regression(
    x: np.ndarray,
    y: np.ndarray
) -> Tuple[float, float, float, float]:
    """
    Compute linear regression for scatter plot.
    
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
    slope: float,
    intercept: float,
    r_value: float,
    p_value: float,
    output_path: Path,
    dpi: int = 300
) -> None:
    """
    Create a scatter plot with regression line.
    
    Args:
        x: X-axis data.
        y: Y-axis data.
        x_label: Label for X-axis.
        y_label: Label for Y-axis.
        title: Plot title.
        slope: Regression slope.
        intercept: Regression intercept.
        r_value: Correlation coefficient.
        p_value: P-value for correlation.
        output_path: Path to save the plot.
        dpi: Resolution for saved figure.
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Scatter plot
    ax.scatter(x, y, alpha=0.6, s=50, edgecolors='black', linewidth=0.5)
    
    # Regression line
    x_min, x_max = x.min(), x.max()
    y_pred = slope * np.array([x_min, x_max]) + intercept
    ax.plot([x_min, x_max], y_pred, 'r-', linewidth=2, 
            label=f'Regression (r={r_value:.3f}, p={p_value:.3e})')
    
    ax.set_xlabel(x_label, fontsize=12)
    ax.set_ylabel(y_label, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # Save in both PNG and PDF formats
    output_path_png = output_path.with_suffix('.png')
    output_path_pdf = output_path.with_suffix('.pdf')
    
    plt.savefig(output_path_png, dpi=dpi, bbox_inches='tight')
    plt.savefig(output_path_pdf, bbox_inches='tight')
    
    plt.close(fig)
    
    logger.info(f"Saved scatter plot to {output_path_png} and {output_path_pdf}")

def create_clone_density_vs_perplexity_plot(
    data: pd.DataFrame,
    output_dir: Path,
    dpi: int = 300
) -> None:
    """
    Create scatter plot of clone density vs model perplexity.
    
    Args:
        data: DataFrame with clone_density and perplexity columns.
        output_dir: Directory to save the plot.
        dpi: Resolution for saved figure.
    """
    x = data['clone_density'].values
    y = data['perplexity'].values
    
    slope, intercept, r_value, p_value = compute_regression(x, y)
    
    output_path = output_dir / 'clone_density_vs_perplexity'
    
    title = 'Clone Density vs Model Perplexity'
    create_scatter_plot_with_regression(
        x, y, 'Clone Density', 'Perplexity',
        title, slope, intercept, r_value, p_value,
        output_path, dpi
    )

def create_clone_density_vs_accuracy_plot(
    data: pd.DataFrame,
    output_dir: Path,
    dpi: int = 300
) -> None:
    """
    Create scatter plot of clone density vs bug detection accuracy.
    
    Args:
        data: DataFrame with clone_density and accuracy columns.
        output_dir: Directory to save the plot.
        dpi: Resolution for saved figure.
    """
    x = data['clone_density'].values
    y = data['pass1_accuracy'].values
    
    slope, intercept, r_value, p_value = compute_regression(x, y)
    
    output_path = output_dir / 'clone_density_vs_accuracy'
    
    title = 'Clone Density vs Bug Detection Accuracy (pass@1)'
    create_scatter_plot_with_regression(
        x, y, 'Clone Density', 'Pass@1 Accuracy',
        title, slope, intercept, r_value, p_value,
        output_path, dpi
    )

def create_sensitivity_analysis_plot(
    sensitivity_data: Dict[str, Dict[str, float]],
    output_dir: Path,
    dpi: int = 300
) -> None:
    """
    Create sensitivity analysis plot across thresholds.
    
    Args:
        sensitivity_data: Dictionary with threshold keys and correlation metrics.
        output_dir: Directory to save the plot.
        dpi: Resolution for saved figure.
    """
    thresholds = list(sensitivity_data.keys())
    perplexity_corrs = [sensitivity_data[t].get('perplexity_correlation', 0) 
                       for t in thresholds]
    accuracy_corrs = [sensitivity_data[t].get('accuracy_correlation', 0) 
                     for t in thresholds]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x_positions = np.arange(len(thresholds))
    width = 0.35
    
    ax.bar(x_positions - width/2, perplexity_corrs, width, 
           label='Perplexity Correlation', alpha=0.8)
    ax.bar(x_positions + width/2, accuracy_corrs, width, 
           label='Accuracy Correlation', alpha=0.8)
    
    ax.set_xlabel('Clone Detection Threshold', fontsize=12)
    ax.set_ylabel('Spearman Correlation Coefficient', fontsize=12)
    ax.set_title('Sensitivity Analysis: Correlation Across Thresholds', 
                fontsize=14, fontweight='bold')
    ax.set_xticks(x_positions)
    ax.set_xticklabels([f'{t}' for t in thresholds])
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for i, (pc, ac) in enumerate(zip(perplexity_corrs, accuracy_corrs)):
        ax.text(i - width/2, pc + 0.01, f'{pc:.3f}', 
               ha='center', va='bottom', fontsize=9)
        ax.text(i + width/2, ac + 0.01, f'{ac:.3f}', 
               ha='center', va='bottom', fontsize=9)
    
    output_path = output_dir / 'sensitivity_analysis'
    
    plt.savefig(output_path.with_suffix('.png'), dpi=dpi, bbox_inches='tight')
    plt.savefig(output_path.with_suffix('.pdf'), bbox_inches='tight')
    
    plt.close(fig)
    
    logger.info(f"Saved sensitivity analysis plot to {output_dir}")

def generate_all_visualizations(
    correlation_results_path: str,
    output_dir: str,
    sensitivity_data: Optional[Dict[str, Dict[str, float]]] = None
) -> List[Path]:
    """
    Generate all visualizations and save to output directory.
    
    Args:
        correlation_results_path: Path to correlation results CSV.
        output_dir: Directory to save all visualization outputs.
        sensitivity_data: Optional sensitivity analysis data dictionary.
    
    Returns:
        List of paths to saved visualization files.
    """
    logger.info(f"Generating visualizations to {output_dir}")
    
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load data
    data = load_correlation_data(correlation_results_path)
    
    saved_files = []
    
    # Generate clone density vs perplexity plot
    create_clone_density_vs_perplexity_plot(data, output_path)
    saved_files.extend([
        output_path / 'clone_density_vs_perplexity.png',
        output_path / 'clone_density_vs_perplexity.pdf'
    ])
    
    # Generate clone density vs accuracy plot
    create_clone_density_vs_accuracy_plot(data, output_path)
    saved_files.extend([
        output_path / 'clone_density_vs_accuracy.png',
        output_path / 'clone_density_vs_accuracy.pdf'
    ])
    
    # Generate sensitivity analysis plot if data provided
    if sensitivity_data:
        create_sensitivity_analysis_plot(sensitivity_data, output_path)
        saved_files.extend([
            output_path / 'sensitivity_analysis.png',
            output_path / 'sensitivity_analysis.pdf'
        ])
    
    logger.info(f"Generated {len(saved_files)} visualization files")
    return saved_files

def main() -> None:
    """Main entry point for visualization generation."""
    logger = setup_logging()
    
    # Default paths
    correlation_results_path = 'data/analysis/correlation_results.csv'
    output_dir = 'data/analysis/figures'
    
    # Load sensitivity data if available
    sensitivity_data = None
    try:
        sensitivity_df = pd.read_csv('data/analysis/sensitivity_analysis.csv')
        sensitivity_data = {}
        for _, row in sensitivity_df.iterrows():
            threshold = str(row['threshold'])
            sensitivity_data[threshold] = {
                'perplexity_correlation': row.get('perplexity_correlation', 0),
                'accuracy_correlation': row.get('accuracy_correlation', 0)
            }
    except FileNotFoundError:
        logger.info("No sensitivity analysis data found, skipping sensitivity plot")
    
    # Generate all visualizations
    saved_files = generate_all_visualizations(
        correlation_results_path,
        output_dir,
        sensitivity_data
    )
    
    logger.info(f"All visualizations saved to {output_dir}")
    for f in saved_files:
        logger.info(f"  - {f}")

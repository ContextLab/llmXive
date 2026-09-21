"""
Visualization module for perovskite thermal conductivity analysis.

Generates scatter plots for the top-k correlated descriptors with confidence interval bands.
"""
import sys
import logging
import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

def setup_logger_module(name: str, level: int = logging.INFO) -> logging.Logger:
    """Setup a module-level logger."""
    log = logging.getLogger(name)
    log.setLevel(level)
    if not log.handlers:
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        log.addHandler(ch)
    return log

def load_correlation_results(correlation_file: Path) -> Dict[str, Any]:
    """
    Load correlation results from JSON file.
    
    Args:
        correlation_file: Path to correlation_matrix.json
        
    Returns:
        Dictionary containing correlation results
    """
    if not correlation_file.exists():
        raise FileNotFoundError(f"Correlation results file not found: {correlation_file}")
    
    with open(correlation_file, 'r') as f:
        return json.load(f)

def load_vif_filtered_data(data_file: Path) -> pd.DataFrame:
    """
    Load VIF-filtered dataset.
    
    Args:
        data_file: Path to descriptors_vif_filtered.csv
        
    Returns:
        DataFrame with VIF-filtered descriptors
    """
    if not data_file.exists():
        raise FileNotFoundError(f"Data file not found: {data_file}")
    
    df = pd.read_csv(data_file)
    logger.info(f"Loaded {len(df)} rows from {data_file}")
    return df

def get_top_k_correlated_descriptors(
    correlation_results: Dict[str, Any],
    target_variable: str = 'thermal_conductivity',
    k: int = 3
) -> List[Tuple[str, float, float]]:
    """
    Extract top-k correlated descriptors with the target variable.
    
    Args:
        correlation_results: Dictionary from correlation analysis
        target_variable: Name of the target variable (thermal conductivity)
        k: Number of top descriptors to return
        
    Returns:
        List of tuples (descriptor_name, correlation, p_value) sorted by absolute correlation
    """
    stratified_results = correlation_results.get('stratified_results', {})
    
    # Aggregate correlations across chemistry classes if stratified
    # For simplicity, we'll use the 'all' or first available class, or average
    if 'all' in stratified_results:
        class_results = stratified_results['all']
    else:
        # Use first available class
        class_results = list(stratified_results.values())[0]
    
    correlations = class_results.get('pearson', {})
    
    # Filter out the target variable itself and non-descriptor columns
    descriptor_correlations = []
    for descriptor, corr_info in correlations.items():
        if descriptor == target_variable or descriptor in ['chemistry_class', 'structure_id']:
            continue
        
        if isinstance(corr_info, dict):
            corr_val = corr_info.get('r', 0.0)
            p_val = corr_info.get('p', 1.0)
        else:
            corr_val = float(corr_info)
            p_val = 1.0
        
        descriptor_correlations.append((descriptor, corr_val, p_val))
    
    # Sort by absolute correlation value
    descriptor_correlations.sort(key=lambda x: abs(x[1]), reverse=True)
    
    return descriptor_correlations[:k]

def plot_scatter_with_ci(
    df: pd.DataFrame,
    x: str,
    y: str,
    ax: Optional[plt.Axes] = None,
    title: Optional[str] = None,
    color: str = '#2E86AB'
) -> plt.Axes:
    """
    Create a scatter plot with 95% confidence interval bands.
    
    Args:
        df: DataFrame containing the data
        x: X-axis column name
        y: Y-axis column name
        ax: Matplotlib Axes object (optional)
        title: Plot title
        color: Plot color
        
    Returns:
        Matplotlib Axes object
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 6))
    
    # Filter out NaN values
    mask = df[[x, y]].notna().all(axis=1)
    x_data = df.loc[mask, x]
    y_data = df.loc[mask, y]
    
    # Scatter plot
    ax.scatter(x_data, y_data, alpha=0.6, color=color, s=50, edgecolors='w', linewidth=0.5)
    
    # Linear regression for CI band
    if len(x_data) > 2:
        slope, intercept, r_value, p_value, std_err = stats.linregress(x_data, y_data)
        
        # Create line for regression
        x_line = np.linspace(x_data.min(), x_data.max(), 100)
        y_line = slope * x_line + intercept
        
        # Calculate confidence interval
        y_fit = slope * x_data + intercept
        residuals = y_data - y_fit
        mse = np.sum(residuals ** 2) / (len(y_data) - 2)
        x_mean = x_data.mean()
        
        # Standard error of prediction
        se = np.sqrt(mse * (1 + 1/len(x_data) + (x_line - x_mean)**2 / np.sum((x_data - x_mean)**2)))
        ci = 1.96 * se  # 95% CI
        
        # Plot regression line
        ax.plot(x_line, y_line, color='red', linewidth=2, label=f'Fit (r={r_value:.3f})')
        
        # Plot confidence interval band
        ax.fill_between(x_line, y_line - ci, y_line + ci, color='red', alpha=0.2, label='95% CI')
    
    # Labels and title
    ax.set_xlabel(x.replace('_', ' ').title(), fontsize=12)
    ax.set_ylabel(y.replace('_', ' ').title(), fontsize=12)
    if title:
        ax.set_title(title, fontsize=14)
    
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best')
    
    return ax

def create_top_k_scatter_plots(
    df: pd.DataFrame,
    correlation_results: Dict[str, Any],
    output_dir: Path,
    target_variable: str = 'thermal_conductivity',
    k: int = 3,
    dpi: int = 300
) -> List[Path]:
    """
    Generate scatter plots for top-k correlated descriptors with CI bands.
    
    Args:
        df: VIF-filtered dataset
        correlation_results: Correlation analysis results
        output_dir: Directory to save plots
        target_variable: Target variable name
        k: Number of top descriptors
        dpi: Output resolution
        
    Returns:
        List of paths to generated plot files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get top-k descriptors
    top_k = get_top_k_correlated_descriptors(correlation_results, target_variable, k)
    
    if len(top_k) == 0:
        logger.warning("No correlated descriptors found to plot.")
        return []
    
    plot_paths = []
    fig, axes = plt.subplots(1, len(top_k), figsize=(6 * len(top_k), 6))
    if len(top_k) == 1:
        axes = [axes]
    
    for idx, (descriptor, corr, p_val) in enumerate(top_k):
        if descriptor not in df.columns or target_variable not in df.columns:
            logger.warning(f"Descriptor '{descriptor}' or target '{target_variable}' not in dataframe.")
            continue
        
        title = f"{descriptor.replace('_', ' ').title()} vs Thermal Conductivity\n(r={corr:.3f}, p={p_val:.3f})"
        ax = axes[idx]
        plot_scatter_with_ci(df, descriptor, target_variable, ax=ax, title=title)
        
        # Save individual plot
        plot_filename = output_dir / f"scatter_{descriptor}_vs_{target_variable}.png"
        fig.savefig(plot_filename, dpi=dpi, bbox_inches='tight')
        plot_paths.append(plot_filename)
        logger.info(f"Saved plot: {plot_filename}")
    
    plt.close(fig)
    
    return plot_paths

def main():
    """Main entry point for visualization script."""
    parser = argparse.ArgumentParser(description="Generate scatter plots for top-k correlated descriptors.")
    parser.add_argument(
        '--data',
        type=str,
        default='data/cleaned/descriptors_vif_filtered.csv',
        help='Path to VIF-filtered dataset'
    )
    parser.add_argument(
        '--correlation',
        type=str,
        default='data/results/correlation_matrix.json',
        help='Path to correlation results JSON'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='figures',
        help='Output directory for plots'
    )
    parser.add_argument(
        '--k',
        type=int,
        default=3,
        help='Number of top correlated descriptors to plot'
    )
    parser.add_argument(
        '--target',
        type=str,
        default='thermal_conductivity',
        help='Target variable name'
    )
    parser.add_argument(
        '--dpi',
        type=int,
        default=300,
        help='Output resolution (DPI)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )
    
    args = parser.parse_args()
    
    # Setup logger
    log = setup_logger_module('visualize')
    
    # Load data
    try:
        df = load_vif_filtered_data(Path(args.data))
    except FileNotFoundError as e:
        log.error(str(e))
        sys.exit(1)
    
    # Load correlation results
    try:
        corr_results = load_correlation_results(Path(args.correlation))
    except FileNotFoundError as e:
        log.error(str(e))
        sys.exit(1)
    
    # Set seed
    np.random.seed(args.seed)
    
    # Generate plots
    output_dir = Path(args.output_dir)
    plot_paths = create_top_k_scatter_plots(
        df,
        corr_results,
        output_dir,
        target_variable=args.target,
        k=args.k,
        dpi=args.dpi
    )
    
    if plot_paths:
        log.info(f"Successfully generated {len(plot_paths)} plots.")
        for p in plot_paths:
            log.info(f"  - {p}")
    else:
        log.warning("No plots were generated.")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
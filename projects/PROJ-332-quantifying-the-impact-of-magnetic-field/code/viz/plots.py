"""
Visualization module for generating diagnostic plots and charts.

This module provides functions to create regression plots, scatter plots,
and other diagnostic visualizations for the plasma confinement analysis pipeline.
All plots are saved to the specified output directory with appropriate formatting
and metadata.

Functions:
    create_regression_plot: Generate a scatter plot with regression line and confidence intervals.
    main: Entry point for running the visualization module as a script.
"""

import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)


def create_regression_plot(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    x_label: str,
    y_label: str,
    output_path: Path,
    ci_level: float = 0.95,
    bootstrap_iterations: int = 1000,
    random_seed: int = 42,
    figsize: Tuple[int, int] = (10, 8),
    show_grid: bool = True,
    line_style: str = 'linear',
    mode_col: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a regression plot with scatter points, regression line, and confidence interval band.

    This function generates a visualization showing the relationship between two variables
    with optional stratification by a categorical mode variable. It includes bootstrap-based
    confidence intervals for the regression line.

    Args:
        data: DataFrame containing the data to plot.
        x_col: Name of the column to use for the x-axis.
        y_col: Name of the column to use for the y-axis.
        title: Title of the plot.
        x_label: Label for the x-axis.
        y_label: Label for the y-axis.
        output_path: Path where the plot will be saved (must have .png extension).
        ci_level: Confidence level for the interval (default 0.95 for 95%).
        bootstrap_iterations: Number of bootstrap iterations for CI calculation (default 1000).
        random_seed: Random seed for reproducibility (default 42).
        figsize: Figure size as (width, height) in inches (default (10, 8)).
        show_grid: Whether to show grid lines (default True).
        line_style: Style of regression line - 'linear' or 'quadratic' (default 'linear').
        mode_col: Optional column name for stratifying by mode (e.g., 'H-mode' vs 'L-mode').

    Returns:
        Dictionary containing plot statistics:
            - 'slope': Slope of the regression line
            - 'intercept': Intercept of the regression line
            - 'r_value': Pearson correlation coefficient
            - 'p_value': P-value for the correlation
            - 'std_err': Standard error of the estimate
            - 'ci_lower': Lower bound of confidence interval
            - 'ci_upper': Upper bound of confidence interval

    Raises:
        ValueError: If required columns are missing from the DataFrame.
        FileNotFoundError: If the output directory does not exist.
        IOError: If the plot cannot be saved.

    Example:
        >>> df = pd.DataFrame({'island_width': [0.1, 0.2, 0.3], 'tau_e': [0.5, 0.6, 0.7]})
        >>> output_path = Path('outputs/plot.png')
        >>> stats = create_regression_plot(df, 'island_width', 'tau_e', 'Island Width vs Tau_E',
        ...                                'Island Width (m)', 'Tau_E (s)', output_path)
        >>> print(f"Slope: {stats['slope']:.4f}")
    """
    # Validate input data
    if x_col not in data.columns or y_col not in data.columns:
        raise ValueError(f"Required columns '{x_col}' and/or '{y_col}' not found in DataFrame.")

    # Remove rows with NaN values in the columns of interest
    plot_data = data[[x_col, y_col]].dropna()

    if len(plot_data) < 2:
        logger.warning(f"Insufficient data points ({len(plot_data)}) for regression plot.")
        return {}

    x = plot_data[x_col].values
    y = plot_data[y_col].values

    # Perform linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    # Generate regression line points
    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = slope * x_line + intercept

    # Calculate confidence intervals using bootstrap
    np.random.seed(random_seed)
    bootstrap_slopes = []
    bootstrap_intercepts = []

    for _ in range(bootstrap_iterations):
        indices = np.random.choice(len(x), size=len(x), replace=True)
        x_boot = x[indices]
        y_boot = y[indices]
        boot_slope, boot_intercept, _, _, _ = stats.linregress(x_boot, y_boot)
        bootstrap_slopes.append(boot_slope)
        bootstrap_intercepts.append(boot_intercept)

    # Calculate confidence interval bounds
    alpha = 1 - ci_level
    ci_lower_slope = np.percentile(bootstrap_slopes, 100 * alpha / 2)
    ci_upper_slope = np.percentile(bootstrap_slopes, 100 * (1 - alpha / 2))
    ci_lower_intercept = np.percentile(bootstrap_intercepts, 100 * alpha / 2)
    ci_upper_intercept = np.percentile(bootstrap_intercepts, 100 * (1 - alpha / 2))

    # Calculate CI for the regression line
    y_ci_lower = ci_lower_slope * x_line + ci_lower_intercept
    y_ci_upper = ci_upper_slope * x_line + ci_upper_intercept

    # Create the plot
    fig, ax = plt.subplots(figsize=figsize)

    # Plot scatter points
    if mode_col and mode_col in plot_data.columns:
        # Color by mode
        modes = plot_data[mode_col].unique()
        colors = plt.cm.Set3(np.linspace(0, 1, len(modes)))
        for i, mode in enumerate(modes):
            mask = plot_data[mode_col] == mode
            ax.scatter(
                plot_data.loc[mask, x_col],
                plot_data.loc[mask, y_col],
                label=mode,
                alpha=0.6,
                edgecolors='black',
                s=60,
                color=colors[i]
            )
        ax.legend(title=mode_col.replace('_', ' ').title())
    else:
        ax.scatter(x, y, alpha=0.6, edgecolors='black', s=60)

    # Plot regression line
    ax.plot(x_line, y_line, 'r-', linewidth=2, label=f'Regression (r={r_value:.3f})')

    # Plot confidence interval band
    ax.fill_between(x_line, y_ci_lower, y_ci_upper, color='red', alpha=0.2, label=f'{ci_level*100:.0f}% CI')

    # Set labels and title
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel(x_label, fontsize=12)
    ax.set_ylabel(y_label, fontsize=12)

    if show_grid:
        ax.grid(True, linestyle='--', alpha=0.7)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save the plot
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    logger.info(f"Plot saved to {output_path}")

    return {
        'slope': slope,
        'intercept': intercept,
        'r_value': r_value,
        'p_value': p_value,
        'std_err': std_err,
        'ci_lower': ci_lower_slope,
        'ci_upper': ci_upper_slope,
        'n_points': len(x)
    }


def main():
    """
    Main entry point for the visualization module.

    This function demonstrates the usage of the create_regression_plot function
    with sample data. It is intended for testing and validation purposes.

    Note:
        In a production environment, this function would be called from the main
        pipeline script with actual data from the analysis results.
    """
    logger.info("Running viz/plots.py as a script (demo mode)")

    # Create sample data for demonstration
    np.random.seed(42)
    n_samples = 20
    x_data = np.random.uniform(0.05, 0.25, n_samples)
    # Simulate a negative correlation (as expected in the hypothesis)
    y_data = -2.5 * x_data + 1.2 + np.random.normal(0, 0.1, n_samples)

    sample_df = pd.DataFrame({
        'island_width': x_data,
        'tau_e': y_data,
        'mode': np.random.choice(['H-mode', 'L-mode'], n_samples)
    })

    output_dir = Path('outputs')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'topology_vs_confinement_demo.png'

    try:
        stats_result = create_regression_plot(
            data=sample_df,
            x_col='island_width',
            y_col='tau_e',
            title='Topology vs Confinement (Demo)',
            x_label='Island Width (m)',
            y_label='Tau_E (s)',
            output_path=output_path,
            mode_col='mode',
            line_style='linear',
            bootstrap_iterations=1000,
            random_seed=42
        )

        if stats_result:
            logger.info(f"Demo plot created successfully: {output_path}")
            logger.info(f"Regression stats: r={stats_result['r_value']:.3f}, p={stats_result['p_value']:.3f}")
        else:
            logger.warning("No stats returned from plot creation (insufficient data)")

    except Exception as e:
        logger.error(f"Failed to create demo plot: {e}", exc_info=True)
        raise

"""
Visualization module.
Defines plot generation logic for error rate curves and power comparisons.

This module provides functions to create matplotlib figures based on
simulation results. It does NOT execute the simulation or write files to disk;
it only defines the plotting logic as requested by the library definition task.

FR-006 Compliance:
- plot_error_rate_curve: Visualizes Type I error inflation vs dependency strength.
- plot_power_comparison: Visualizes statistical power vs dependency strength.
"""
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import List, Dict, Any, Optional

# Ensure consistent plotting style
sns.set_theme(style="whitegrid", context="talk")

def plot_error_rate_curve(
    results_df: pd.DataFrame,
    x_col: str = 'dependency_strength',
    y_col: str = 'error_rate',
    hue_col: str = 'test_type',
    nominal_alpha: float = 0.05
) -> plt.Figure:
    """
    Plot error rate curves showing Type I error inflation.
    
    This function generates a line plot where the x-axis represents the
    dependency strength (e.g., AR(1) correlation coefficient) and the
    y-axis represents the observed Type I error rate. It includes a
    horizontal reference line for the nominal alpha level.
    
    Args:
        results_df: DataFrame containing aggregated simulation results.
                    Must contain columns for x, y, and hue.
        x_col: Column name for the x-axis (dependency strength).
        y_col: Column name for the y-axis (error rate).
        hue_col: Column name for grouping lines (e.g., test_type).
        nominal_alpha: The nominal significance level to plot as a reference.
    
    Returns:
        Matplotlib figure object containing the plot.
    
    Raises:
        ValueError: If required columns are missing from the DataFrame.
    """
    required_cols = {x_col, y_col, hue_col}
    if not required_cols.issubset(results_df.columns):
        missing = required_cols - set(results_df.columns)
        raise ValueError(f"Missing required columns in results_df: {missing}")

    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot the main trend lines
    sns.lineplot(
        data=results_df,
        x=x_col,
        y=y_col,
        hue=hue_col,
        ax=ax,
        marker='o',
        linewidth=2,
        markersize=8
    )
    
    # Add nominal alpha reference line
    ax.axhline(
        y=nominal_alpha,
        color='red',
        linestyle='--',
        linewidth=2,
        label=f'Nominal Alpha ({nominal_alpha})'
    )
    
    ax.set_xlabel('Dependency Strength (r)', fontsize=12)
    ax.set_ylabel('Observed Type I Error Rate', fontsize=12)
    ax.set_title('Robustness of Statistical Tests to Non-Independence', fontsize=14)
    ax.legend(title='Test Type')
    
    # Set y-axis limits to include 0 and slightly above max observed or alpha
    current_ylim = ax.get_ylim()
    max_val = max(results_df[y_col].max(), nominal_alpha)
    ax.set_ylim(0, max(max_val * 1.2, 0.15))
    
    plt.tight_layout()
    return fig

def plot_power_comparison(
    results_df: pd.DataFrame,
    x_col: str = 'dependency_strength',
    y_col: str = 'power',
    hue_col: str = 'dependency_type',
    baseline_power: Optional[float] = None
) -> plt.Figure:
    """
    Plot power comparison across dependency structures.
    
    This function generates a line plot showing how statistical power
    changes as dependency strength increases. It is used to quantify
    the reduction in power due to non-independence (US3).
    
    Args:
        results_df: DataFrame containing aggregated power analysis results.
        x_col: Column name for the x-axis (dependency strength).
        y_col: Column name for the y-axis (statistical power).
        hue_col: Column name for grouping lines (e.g., dependency_type).
        baseline_power: Optional horizontal line to indicate baseline power
                        (e.g., power at r=0).
    
    Returns:
        Matplotlib figure object containing the plot.
    
    Raises:
        ValueError: If required columns are missing from the DataFrame.
    """
    required_cols = {x_col, y_col, hue_col}
    if not required_cols.issubset(results_df.columns):
        missing = required_cols - set(results_df.columns)
        raise ValueError(f"Missing required columns in results_df: {missing}")

    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot the main trend lines
    sns.lineplot(
        data=results_df,
        x=x_col,
        y=y_col,
        hue=hue_col,
        ax=ax,
        marker='s',
        linewidth=2,
        markersize=8
    )
    
    if baseline_power is not None:
        ax.axhline(
            y=baseline_power,
            color='green',
            linestyle=':',
            linewidth=2,
            label=f'Baseline Power ({baseline_power:.2f})'
        )
    
    ax.set_xlabel('Dependency Strength (r)', fontsize=12)
    ax.set_ylabel('Statistical Power (1 - Beta)', fontsize=12)
    ax.set_title('Impact of Non-Independence on Statistical Power', fontsize=14)
    ax.legend(title='Dependency Structure')
    
    # Set y-axis limits to ensure 0 to 1 range is visible
    ax.set_ylim(0, 1.05)
    
    plt.tight_layout()
    return fig

def plot_ci_bands(
    results_df: pd.DataFrame,
    x_col: str = 'dependency_strength',
    y_col: str = 'error_rate',
    ci_lower_col: str = 'ci_lower',
    ci_upper_col: str = 'ci_upper',
    hue_col: str = 'test_type'
) -> plt.Figure:
    """
    Plot error rate curves with Clopper-Pearson confidence intervals.
    
    This function extends the basic error rate plot by shading the area
    between the lower and upper confidence bounds, providing a visual
    representation of the uncertainty in the error rate estimates.
    
    Args:
        results_df: DataFrame containing results with CI columns.
        x_col: Column name for x-axis.
        y_col: Column name for y-axis (point estimate).
        ci_lower_col: Column name for lower CI bound.
        ci_upper_col: Column name for upper CI bound.
        hue_col: Column name for grouping.
    
    Returns:
        Matplotlib figure object.
    """
    required_cols = {x_col, y_col, ci_lower_col, ci_upper_col, hue_col}
    if not required_cols.issubset(results_df.columns):
        missing = required_cols - set(results_df.columns)
        raise ValueError(f"Missing required columns: {missing}")

    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Group by hue and plot manually to handle fill_between correctly
    for name, group in results_df.groupby(hue_col):
        group = group.sort_values(x_col)
        ax.plot(group[x_col], group[y_col], label=name, marker='o')
        ax.fill_between(
            group[x_col],
            group[ci_lower_col],
            group[ci_upper_col],
            alpha=0.2
        )
    
    ax.axhline(y=0.05, color='red', linestyle='--', label='Nominal Alpha')
    ax.set_xlabel('Dependency Strength')
    ax.set_ylabel('Error Rate with 95% CI')
    ax.set_title('Type I Error Rates with Clopper-Pearson Confidence Intervals')
    ax.legend()
    plt.tight_layout()
    return fig
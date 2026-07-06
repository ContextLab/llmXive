import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import List, Dict, Any, Optional
import numpy as np
import os

# Set style for scientific publication quality
sns.set_theme(style="whitegrid", context="talk")
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.figsize'] = (10, 6)

def plot_error_rate_curve(
    data: pd.DataFrame,
    x_col: str = 'dependency_strength',
    y_col: str = 'type1_error_rate',
    hue_col: str = 'test_type',
    nominal_alpha: float = 0.05,
    ci_col: Optional[str] = None,
    output_path: Optional[str] = None
) -> plt.Figure:
    """
    Generate comparative line plots of Type I error rates vs dependency strength.
    
    Parameters
    ----------
    data : pd.DataFrame
        Aggregated simulation results containing columns for dependency strength,
        error rate, test type, and optionally confidence intervals.
    x_col : str
        Column name for dependency strength (x-axis).
    y_col : str
        Column name for error rate (y-axis).
    hue_col : str
        Column name for test type (hue/legend).
    nominal_alpha : float
        Nominal significance level to plot as horizontal reference line.
    ci_col : str, optional
        Column name for confidence interval width (for error bars). If None, no error bars.
    output_path : str, optional
        Path to save the figure. If None, figure is not saved.
        
    Returns
    -------
    plt.Figure
        The matplotlib figure object.
        
    Raises
    ------
    ValueError
        If required columns are missing from the dataframe.
    """
    required_cols = {x_col, y_col, hue_col}
    if not required_cols.issubset(data.columns):
        missing = required_cols - set(data.columns)
        raise ValueError(f"Missing required columns in data: {missing}")
    
    fig, ax = plt.subplots()
    
    # Sort data by dependency strength for proper line plotting
    data_sorted = data.sort_values(by=[hue_col, x_col])
    
    # Plot lines for each test type
    for test_type, group in data_sorted.groupby(hue_col):
        group_sorted = group.sort_values(x_col)
        ax.plot(group_sorted[x_col], group_sorted[y_col], 
               label=test_type, marker='o', linewidth=2, markersize=6)
        
        # Add confidence interval bands if available
        if ci_col and f'{ci_col}_lower' in data.columns and f'{ci_col}_upper' in data.columns:
            ax.fill_between(group_sorted[x_col], 
                           group_sorted[f'{ci_col}_lower'], 
                           group_sorted[f'{ci_col}_upper'], 
                           alpha=0.2)
    
    # Add nominal alpha reference line
    ax.axhline(y=nominal_alpha, color='red', linestyle='--', 
              label=f'Nominal α = {nominal_alpha}', linewidth=1.5)
    
    # Add threshold reference line for α=0.10 if needed for US2 AC-2
    if nominal_alpha != 0.10:
        ax.axhline(y=0.10, color='orange', linestyle=':', 
                  label='Threshold α = 0.10', linewidth=1.5)
    
    ax.set_xlabel('Dependency Strength (r)')
    ax.set_ylabel('Observed Type I Error Rate')
    ax.set_title('Robustness of Statistical Tests to Non-Independence\n(Type I Error Inflation)')
    ax.legend(loc='best')
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0, top=max(0.2, data[y_col].max() * 1.1))
    
    # Ensure grid is visible
    ax.grid(True, alpha=0.3)
    
    if output_path:
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Figure saved to {output_path}")
    
    return fig

def plot_power_comparison(
    data: pd.DataFrame,
    x_col: str = 'dependency_strength',
    y_col: str = 'power',
    hue_col: str = 'test_type',
    effect_size_col: Optional[str] = None,
    output_path: Optional[str] = None
) -> plt.Figure:
    """
    Generate comparative line plots of statistical power vs dependency strength.
    
    Parameters
    ----------
    data : pd.DataFrame
        Aggregated simulation results for power analysis.
    x_col : str
        Column name for dependency strength (x-axis).
    y_col : str
        Column name for power (y-axis).
    hue_col : str
        Column name for test type (hue/legend).
    effect_size_col : str, optional
        Column name for effect size if multiple effect sizes are plotted.
    output_path : str, optional
        Path to save the figure.
        
    Returns
    -------
    plt.Figure
        The matplotlib figure object.
    """
    required_cols = {x_col, y_col, hue_col}
    if not required_cols.issubset(data.columns):
        missing = required_cols - set(data.columns)
        raise ValueError(f"Missing required columns in data: {missing}")
    
    fig, ax = plt.subplots()
    
    data_sorted = data.sort_values(by=[hue_col, x_col])
    
    if effect_size_col and effect_size_col in data.columns:
        # Create subplots or use different markers for effect sizes
        for (test_type, effect_size), group in data_sorted.groupby([hue_col, effect_size_col]):
            group_sorted = group.sort_values(x_col)
            ax.plot(group_sorted[x_col], group_sorted[y_col], 
                   label=f'{test_type} (δ={effect_size})', marker='o', linewidth=2)
    else:
        for test_type, group in data_sorted.groupby(hue_col):
            group_sorted = group.sort_values(x_col)
            ax.plot(group_sorted[x_col], group_sorted[y_col], 
                   label=test_type, marker='o', linewidth=2, markersize=6)
    
    ax.axhline(y=0.80, color='green', linestyle='--', 
              label='Target Power = 0.80', linewidth=1.5)
    
    ax.set_xlabel('Dependency Strength (r)')
    ax.set_ylabel('Statistical Power (1 - β)')
    ax.set_title('Statistical Power Under Non-Independence')
    ax.legend(loc='best')
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0, top=1.05)
    ax.grid(True, alpha=0.3)
    
    if output_path:
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Figure saved to {output_path}")
    
    return fig

def plot_ci_bands(
    data: pd.DataFrame,
    x_col: str = 'dependency_strength',
    y_col: str = 'type1_error_rate',
    hue_col: str = 'test_type',
    ci_lower_col: str = 'ci_lower',
    ci_upper_col: str = 'ci_upper',
    output_path: Optional[str] = None
) -> plt.Figure:
    """
    Generate plots showing error rates with confidence interval bands.
    
    Parameters
    ----------
    data : pd.DataFrame
        Aggregated results with confidence interval columns.
    x_col : str
        Column name for dependency strength.
    y_col : str
        Column name for error rate.
    hue_col : str
        Column name for test type.
    ci_lower_col : str
        Column name for lower CI bound.
    ci_upper_col : str
        Column name for upper CI bound.
    output_path : str, optional
        Path to save the figure.
        
    Returns
    -------
    plt.Figure
        The matplotlib figure object.
    """
    required_cols = {x_col, y_col, hue_col, ci_lower_col, ci_upper_col}
    if not required_cols.issubset(data.columns):
        missing = required_cols - required_cols.intersection(data.columns)
        raise ValueError(f"Missing required columns in data: {missing}")
    
    fig, ax = plt.subplots()
    
    for test_type, group in data.groupby(hue_col):
        group_sorted = group.sort_values(x_col)
        ax.plot(group_sorted[x_col], group_sorted[y_col], 
               label=test_type, marker='o', linewidth=2)
        ax.fill_between(group_sorted[x_col], 
                       group_sorted[ci_lower_col], 
                       group_sorted[ci_upper_col], 
                       alpha=0.2)
    
    ax.axhline(y=0.05, color='red', linestyle='--', label='Nominal α = 0.05')
    
    ax.set_xlabel('Dependency Strength (r)')
    ax.set_ylabel('Type I Error Rate (95% CI)')
    ax.set_title('Type I Error Rates with Clopper-Pearson Confidence Intervals')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    if output_path:
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Figure saved to {output_path}")
    
    return fig
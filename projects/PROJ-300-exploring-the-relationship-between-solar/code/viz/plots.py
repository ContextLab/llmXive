"""
Visualization module for plotting solar wind and geomagnetic data.
File: code/viz/plots.py

Functions:
  - plot_scatter: Generate scatter plot of lag-adjusted Vsw vs. Ey with regression line.
  - plot_timeseries: Generate dual-axis time-series overlay of Vsw and Ey.

Both functions include correct axis labels, units, and optimal lag annotation (SC-005).
"""
import os
from typing import Optional, Tuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

def plot_scatter(
    df_vsw: pd.DataFrame,
    df_ey: pd.DataFrame,
    output_path: str,
    optimal_lag: int,
    title: Optional[str] = None
) -> None:
    """
    Generate a scatter plot of Solar Wind Speed (Vsw) vs. Tail Reconnection Rate (Ey).
    
    Args:
        df_vsw: DataFrame with columns ['timestamp', 'Vsw']
        df_ey: DataFrame with columns ['timestamp', 'Ey']
        output_path: Path to save the PNG file.
        optimal_lag: The optimal lag in minutes to display in the annotation.
        title: Optional custom title.
    
    Requirements (SC-005):
        - X-axis label: "Solar Wind Speed (km/s)"
        - Y-axis label: "Tail Reconnection Rate Ey (mV/m)"
        - Annotation: "Optimal Lag: {L*} min"
        - Includes regression line.
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    # Prepare data: drop NaNs
    valid_mask = df_vsw['Vsw'].notna() & df_ey['Ey'].notna()
    vsw_data = df_vsw.loc[valid_mask, 'Vsw']
    ey_data = df_ey.loc[valid_mask, 'Ey']
    
    if len(vsw_data) < 2:
        raise ValueError("Insufficient valid data points to generate scatter plot.")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Scatter plot
    ax.scatter(vsw_data, ey_data, alpha=0.6, label='Data Points', color='tab:blue')
    
    # Regression line
    slope, intercept, r_value, p_value, std_err = stats.linregress(vsw_data, ey_data)
    line_data = np.array([vsw_data.min(), vsw_data.max()])
    ax.plot(line_data, slope * line_data + intercept, 'r-', label=f'Linear Fit (r={r_value:.2f})')
    
    # Labels and Title (SC-005)
    ax.set_xlabel('Solar Wind Speed (km/s)', fontsize=12)
    ax.set_ylabel('Tail Reconnection Rate Ey (mV/m)', fontsize=12)
    
    plot_title = title if title else f'Lag-Adjusted Scatter Plot (Optimal Lag: {optimal_lag} min)'
    ax.set_title(plot_title, fontsize=14)
    
    ax.legend(loc='best')
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Save
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)

def plot_timeseries(
    df_vsw: pd.DataFrame,
    df_ey: pd.DataFrame,
    output_path: str,
    optimal_lag: int,
    title: Optional[str] = None
) -> None:
    """
    Generate a dual-axis time-series overlay of Vsw and Ey.
    
    Args:
        df_vsw: DataFrame with columns ['timestamp', 'Vsw']
        df_ey: DataFrame with columns ['timestamp', 'Ey']
        output_path: Path to save the PNG file.
        optimal_lag: The optimal lag in minutes to display in the annotation.
        title: Optional custom title.
    
    Requirements (SC-005):
        - X-axis label: "Time (UTC)"
        - Left Y-axis: "Solar Wind Speed (km/s)"
        - Right Y-axis: "Tail Reconnection Rate Ey (mV/m)"
        - Annotation: "Optimal Lag: {L*} min"
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Plot Vsw
    color_vsw = 'tab:blue'
    ax1.set_xlabel('Time (UTC)', fontsize=12)
    ax1.set_ylabel('Solar Wind Speed (km/s)', color=color_vsw, fontsize=12)
    ax1.plot(df_vsw['timestamp'], df_vsw['Vsw'], color=color_vsw, label='Vsw', linewidth=1.5)
    ax1.tick_params(axis='y', labelcolor=color_vsw)
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    # Plot Ey on twin axis
    ax2 = ax1.twinx()
    color_ey = 'tab:orange'
    ax2.set_ylabel('Tail Reconnection Rate Ey (mV/m)', color=color_ey, fontsize=12)
    ax2.plot(df_ey['timestamp'], df_ey['Ey'], color=color_ey, label='Ey', linewidth=1.5, alpha=0.8)
    ax2.tick_params(axis='y', labelcolor=color_ey)
    
    # Combine legends
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')
    
    # Title with Optimal Lag Annotation (SC-005)
    plot_title = title if title else f'Time Series Overlay (Optimal Lag: {optimal_lag} min)'
    ax1.set_title(plot_title, fontsize=14)
    
    # Rotate x-axis labels for readability
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)

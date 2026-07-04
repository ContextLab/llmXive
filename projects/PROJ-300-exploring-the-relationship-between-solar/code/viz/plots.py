"""
Visualization module for generating scatter plots and time-series overlays.
Includes optimal lag annotation and correct axis labels/units.
"""
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from typing import Optional, Tuple

def plot_scatter(
    vsw: pd.Series,
    ey: pd.Series,
    optimal_lag: int,
    output_path: Optional[str] = None
) -> None:
    """
    Generate a scatter plot of lag-adjusted Vsw vs. Ey with regression line.

    Args:
        vsw: Solar wind speed series (km/s).
        ey: Tail reconnection proxy series (mV/m).
        optimal_lag: Optimal lag in minutes.
        output_path: Path to save the plot. If None, plot is shown.
    """
    # Drop NaN pairs
    valid_mask = vsw.notna() & ey.notna()
    vsw_valid = vsw[valid_mask]
    ey_valid = ey[valid_mask]

    if len(vsw_valid) < 2:
        raise ValueError("Insufficient valid data points for scatter plot.")

    fig, ax = plt.subplots(figsize=(10, 6))

    # Scatter points
    ax.scatter(vsw_valid, ey_valid, alpha=0.6, label='Data points', s=20)

    # Linear regression line
    slope, intercept, r_value, p_value, std_err = stats.linregress(vsw_valid, ey_valid)
    x_line = np.linspace(vsw_valid.min(), vsw_valid.max(), 100)
    y_line = slope * x_line + intercept
    ax.plot(x_line, y_line, 'r-', label=f'Fit: r={r_value:.3f}', linewidth=2)

    # Annotations
    ax.set_xlabel('Solar Wind Speed Vsw (km/s)', fontsize=12)
    ax.set_ylabel('Tail Reconnection Proxy Ey (mV/m)', fontsize=12)
    ax.set_title(f'Scatter Plot: Vsw vs Ey (Optimal Lag = {optimal_lag} min)', fontsize=14)
    ax.legend(loc='best')
    ax.grid(True, linestyle='--', alpha=0.7)

    # Save or show
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
    else:
        plt.show()

def plot_timeseries(
    df_sw: pd.DataFrame,
    df_ey: pd.DataFrame,
    optimal_lag: int,
    output_path: Optional[str] = None
) -> None:
    """
    Generate dual-axis time-series overlay of Vsw and Ey.

    Args:
        df_sw: DataFrame with 'timestamp' and 'Vsw'.
        df_ey: DataFrame with 'timestamp' and 'Ey'.
        optimal_lag: Optimal lag in minutes.
        output_path: Path to save the plot. If None, plot is shown.
    """
    # Ensure timestamp is datetime
    if 'timestamp' not in df_sw.columns or 'timestamp' not in df_ey.columns:
        raise ValueError("DataFrames must contain 'timestamp' column.")

    df_sw_plot = df_sw.set_index('timestamp').dropna()
    df_ey_plot = df_ey.set_index('timestamp').dropna()

    # Align indices for plotting (inner join)
    common_index = df_sw_plot.index.intersection(df_ey_plot.index)
    if len(common_index) == 0:
        raise ValueError("No common timestamps between Vsw and Ey data.")

    fig, ax1 = plt.subplots(figsize=(14, 6))

    # Plot Vsw on left axis
    color_vsw = 'tab:blue'
    ax1.set_xlabel('Time', fontsize=12)
    ax1.set_ylabel('Vsw (km/s)', color=color_vsw, fontsize=12)
    ax1.plot(common_index, df_sw_plot.loc[common_index, 'Vsw'], color=color_vsw, label='Vsw')
    ax1.tick_params(axis='y', labelcolor=color_vsw)
    ax1.grid(True, linestyle='--', alpha=0.3)

    # Plot Ey on right axis
    ax2 = ax1.twinx()
    color_ey = 'tab:red'
    ax2.set_ylabel('Ey (mV/m)', color=color_ey, fontsize=12)
    ax2.plot(common_index, df_ey_plot.loc[common_index, 'Ey'], color=color_ey, label='Ey', alpha=0.7)
    ax2.tick_params(axis='y', labelcolor=color_ey)

    # Title and annotation
    title = f'Time Series: Vsw and Ey (Optimal Lag = {optimal_lag} min)'
    fig.suptitle(title, fontsize=14, fontweight='bold')

    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    plt.tight_layout()

    # Save or show
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
    else:
        plt.show()

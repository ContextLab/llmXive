"""
Visualization module for solar wind and geomagnetic reconnection data.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/viz/plots.py
"""
import os
from typing import Optional, Tuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from ..config import EARTH_RADIUS_KM, TAIL_DISTANCE_RE

def plot_scatter(
    df_vsw: pd.DataFrame,
    df_ey: pd.DataFrame,
    optimal_lag: int,
    output_path: Optional[str] = None
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Generate a scatter plot of lag-adjusted Vsw vs. Ey with regression line.
    
    Parameters
    ----------
    df_vsw : pd.DataFrame
        DataFrame with columns ['timestamp', 'Vsw']
    df_ey : pd.DataFrame
        DataFrame with columns ['timestamp', 'Ey']
    optimal_lag : int
        Optimal time lag in minutes to apply to Vsw before plotting
    output_path : str, optional
        Path to save the plot. If None, plot is not saved.
    
    Returns
    -------
    Tuple[plt.Figure, plt.Axes]
        The matplotlib figure and axes objects.
    
    Raises
    ------
    ValueError
        If data columns are missing or lag is invalid.
    """
    # Validate inputs
    if 'Vsw' not in df_vsw.columns or 'timestamp' not in df_vsw.columns:
        raise ValueError("df_vsw must contain 'Vsw' and 'timestamp' columns")
    if 'Ey' not in df_ey.columns or 'timestamp' not in df_ey.columns:
        raise ValueError("df_ey must contain 'Ey' and 'timestamp' columns")
    
    # Apply lag shift to Vsw (shift forward in time by optimal_lag minutes)
    # This simulates the propagation delay
    df_vsw_lagged = df_vsw.copy()
    df_vsw_lagged['timestamp'] = df_vsw_lagged['timestamp'] + pd.Timedelta(minutes=optimal_lag)
    
    # Merge on timestamp
    merged = pd.merge(
        df_vsw_lagged[['timestamp', 'Vsw']],
        df_ey[['timestamp', 'Ey']],
        on='timestamp',
        how='inner'
    )
    
    if len(merged) == 0:
        raise ValueError("No overlapping data points after applying lag. Check timestamps and lag value.")
    
    x = merged['Vsw'].dropna()
    y = merged['Ey'].dropna()
    
    # Ensure alignment after dropna
    min_len = min(len(x), len(y))
    x = x.iloc[:min_len]
    y = y.iloc[:min_len]
    
    if len(x) < 2:
        raise ValueError("Insufficient data points for regression after cleaning.")
    
    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Scatter
    ax.scatter(x, y, alpha=0.6, color='steelblue', edgecolors='black', s=40)
    
    # Regression line
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    x_line = np.linspace(x.min(), x.max(), 100)
    ax.plot(x_line, p(x_line), "r--", label=f'Linear Fit (r={np.corrcoef(x, y)[0,1]:.2f})')
    
    # Labels and Title with Optimal Lag Annotation
    ax.set_xlabel(f'Solar Wind Speed (Vsw) [km/s]')
    ax.set_ylabel(f'Tail Reconnection Rate (Ey) [mV/m]')
    ax.set_title(f'Lag-Adjusted Vsw vs Ey (Optimal Lag: {optimal_lag} min)')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Save if path provided
    if output_path:
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches='tight')
    
    return fig, ax

def plot_timeseries(
    df_vsw: pd.DataFrame,
    df_ey: pd.DataFrame,
    optimal_lag: int,
    output_path: Optional[str] = None
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Generate a dual-axis time-series overlay of Vsw and Ey.
    
    Parameters
    ----------
    df_vsw : pd.DataFrame
        DataFrame with columns ['timestamp', 'Vsw']
    df_ey : pd.DataFrame
        DataFrame with columns ['timestamp', 'Ey']
    optimal_lag : int
        Optimal time lag in minutes to annotate.
    output_path : str, optional
        Path to save the plot. If None, plot is not saved.
    
    Returns
    -------
    Tuple[plt.Figure, plt.Axes]
        The matplotlib figure and axes object (primary axis).
    """
    # Validate inputs
    if 'Vsw' not in df_vsw.columns or 'timestamp' not in df_vsw.columns:
        raise ValueError("df_vsw must contain 'Vsw' and 'timestamp' columns")
    if 'Ey' not in df_ey.columns or 'timestamp' not in df_ey.columns:
        raise ValueError("df_ey must contain 'Ey' and 'timestamp' columns")
    
    # Sort by timestamp
    df_vsw = df_vsw.sort_values('timestamp')
    df_ey = df_ey.sort_values('timestamp')
    
    # Create plot with dual axis
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Plot Vsw on primary axis
    color_vsw = 'tab:blue'
    ax1.set_xlabel('Time (UTC)')
    ax1.set_ylabel('Solar Wind Speed (Vsw) [km/s]', color=color_vsw)
    ax1.plot(df_vsw['timestamp'], df_vsw['Vsw'], color=color_vsw, label='Vsw', linewidth=1.5)
    ax1.tick_params(axis='y', labelcolor=color_vsw)
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Plot Ey on secondary axis
    ax2 = ax1.twinx()
    color_ey = 'tab:orange'
    ax2.set_ylabel('Tail Reconnection Rate (Ey) [mV/m]', color=color_ey)
    ax2.plot(df_ey['timestamp'], df_ey['Ey'], color=color_ey, label='Ey', linewidth=1.5, linestyle='--')
    ax2.tick_params(axis='y', labelcolor=color_ey)
    
    # Title with Optimal Lag Annotation
    ax1.set_title(f'Solar Wind and Reconnection Rate Time Series (Optimal Lag: {optimal_lag} min)')
    
    # Combine legends
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')
    
    # Save if path provided
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches='tight')
    
    return fig, ax1
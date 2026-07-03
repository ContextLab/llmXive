"""
Visualization module for solar wind and geomagnetic tail reconnection analysis.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/viz/plots.py
"""
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from typing import Optional, Tuple

def plot_scatter(
    df_vsw: pd.DataFrame,
    df_ey: pd.DataFrame,
    lag_minutes: int = 0,
    output_path: Optional[str] = None,
    ax: Optional[plt.Axes] = None
) -> Optional[plt.Figure]:
    """
    Generate scatter plot of lag-adjusted Vsw vs. Ey with regression line.
    
    Parameters
    ----------
    df_vsw : pd.DataFrame
        DataFrame with columns 'timestamp' and 'Vsw' (solar wind speed in km/s)
    df_ey : pd.DataFrame
        DataFrame with columns 'timestamp' and 'Ey' (reconnection rate proxy in mV/m)
    lag_minutes : int
        Time lag in minutes to apply to Vsw before correlation
    output_path : str, optional
        Path to save the plot. If None, plot is displayed but not saved.
    ax : plt.Axes, optional
        Axes to plot on. If None, a new figure and axes are created.
        
    Returns
    -------
    plt.Figure or None
        The figure object if ax was not provided, None otherwise.
        
    Notes
    -----
    - Applies lag shift to Vsw data before plotting
    - Includes linear regression line and R² value
    - Annotates optimal lag on the plot (SC-005)
    """
    # Apply lag shift to Vsw timestamps
    vsw_lagged = df_vsw.copy()
    vsw_lagged['timestamp'] = vsw_lagged['timestamp'] + pd.Timedelta(minutes=lag_minutes)
    
    # Merge on timestamp (inner join to align data)
    merged = pd.merge(
        vsw_lagged[['timestamp', 'Vsw']],
        df_ey[['timestamp', 'Ey']],
        on='timestamp',
        how='inner'
    )
    
    # Remove NaN values
    merged = merged.dropna()
    
    if len(merged) < 2:
        raise ValueError("Insufficient data points after lag alignment and NaN removal")
    
    x = merged['Vsw'].values
    y = merged['Ey'].values
    
    # Create figure and axes if not provided
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
    else:
        fig = None
    
    # Scatter plot
    ax.scatter(x, y, alpha=0.6, edgecolors='k', linewidth=0.5, label='Data points')
    
    # Linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = slope * x_line + intercept
    ax.plot(x_line, y_line, 'r-', linewidth=2, label=f'Linear fit (R²={r_value**2:.3f})')
    
    # Labels and title (SC-005: correct labels and units)
    ax.set_xlabel('Solar Wind Speed (Vsw) [km/s]', fontsize=12)
    ax.set_ylabel('Tail Reconnection Rate Proxy (Ey) [mV/m]', fontsize=12)
    ax.set_title(f'Lag-Adjusted Correlation: Vsw vs Ey (Lag = {lag_minutes} min)', fontsize=14)
    
    # Optimal lag annotation (SC-005)
    ax.annotate(
        f'Optimal Lag: {lag_minutes} min',
        xy=(0.05, 0.95),
        xycoords='axes fraction',
        fontsize=11,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    )
    
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    # Save if output path provided
    if output_path:
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Scatter plot saved to: {output_path}")
    
    if fig is not None:
        return fig
    return None

def plot_timeseries(
    df_vsw: pd.DataFrame,
    df_ey: pd.DataFrame,
    lag_minutes: int = 0,
    output_path: Optional[str] = None,
    ax: Optional[plt.Axes] = None
) -> Optional[plt.Figure]:
    """
    Generate dual-axis time-series overlay of Vsw and Ey.
    
    Parameters
    ----------
    df_vsw : pd.DataFrame
        DataFrame with columns 'timestamp' and 'Vsw' (solar wind speed in km/s)
    df_ey : pd.DataFrame
        DataFrame with columns 'timestamp' and 'Ey' (reconnection rate proxy in mV/m)
    lag_minutes : int
        Time lag in minutes to apply to Vsw before plotting
    output_path : str, optional
        Path to save the plot. If None, plot is displayed but not saved.
    ax : plt.Axes, optional
        Axes to plot on. If None, a new figure and axes are created.
        
    Returns
    -------
    plt.Figure or None
        The figure object if ax was not provided, None otherwise.
        
    Notes
    -----
    - Left y-axis: Vsw (km/s)
    - Right y-axis: Ey (mV/m)
    - Annotates optimal lag on the plot (SC-005)
    """
    # Apply lag shift to Vsw timestamps
    vsw_lagged = df_vsw.copy()
    vsw_lagged['timestamp'] = vsw_lagged['timestamp'] + pd.Timedelta(minutes=lag_minutes)
    
    # Merge on timestamp (inner join to align data)
    merged = pd.merge(
        vsw_lagged[['timestamp', 'Vsw']],
        df_ey[['timestamp', 'Ey']],
        on='timestamp',
        how='inner'
    )
    
    # Remove NaN values
    merged = merged.dropna()
    
    if len(merged) < 2:
        raise ValueError("Insufficient data points after lag alignment and NaN removal")
    
    timestamps = merged['timestamp']
    vsw = merged['Vsw'].values
    ey = merged['Ey'].values
    
    # Create figure and axes if not provided
    if ax is None:
        fig, ax = plt.subplots(figsize=(14, 6))
    else:
        fig = None
    
    # Primary y-axis (Vsw)
    ax.plot(timestamps, vsw, 'b-', linewidth=1.5, label='Vsw (Solar Wind Speed)')
    ax.set_xlabel('Time', fontsize=12)
    ax.set_ylabel('Solar Wind Speed (Vsw) [km/s]', fontsize=12, color='b')
    ax.tick_params(axis='y', labelcolor='b')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Secondary y-axis (Ey)
    ax2 = ax.twinx()
    ax2.plot(timestamps, ey, 'r-', linewidth=1.5, label='Ey (Reconnection Rate)')
    ax2.set_ylabel('Tail Reconnection Rate Proxy (Ey) [mV/m]', fontsize=12, color='r')
    ax2.tick_params(axis='y', labelcolor='r')
    
    # Combine legends
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)
    
    # Title
    ax.set_title(f'Time Series Overlay with Propagation Lag (Lag = {lag_minutes} min)', fontsize=14)
    
    # Optimal lag annotation (SC-005)
    ax.annotate(
        f'Optimal Lag: {lag_minutes} min',
        xy=(0.05, 0.95),
        xycoords='axes fraction',
        fontsize=11,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8)
    )
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45, ha='right')
    
    # Save if output path provided
    if output_path:
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Time series plot saved to: {output_path}")
    
    if fig is not None:
        return fig
    return None
"""
Visualization module for solar wind and geomagnetic tail reconnection analysis.
File: code/viz/plots.py
"""
import os
from typing import Optional, Tuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..config import EARTH_RADIUS_KM, TAIL_DISTANCE_RE


def plot_scatter(
    df: pd.DataFrame,
    optimal_lag: Optional[int] = None,
    output_path: Optional[str] = None
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Generate a scatter plot of lag-adjusted Vsw vs. Ey with regression line.

    Includes:
    - Correct axis labels with units (km/s for Vsw, mV/m for Ey)
    - Linear regression line and equation display
    - Optimal lag annotation if provided

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with columns 'Vsw' and 'Ey'.
    optimal_lag : int, optional
        Optimal lag in minutes to annotate on the plot.
    output_path : str, optional
        Path to save the figure. If None, figure is not saved.

    Returns
    -------
    fig, ax : matplotlib Figure, Axes
        The generated plot objects.
    """
    if 'Vsw' not in df.columns or 'Ey' not in df.columns:
        raise ValueError("DataFrame must contain 'Vsw' and 'Ey' columns.")

    # Drop NaNs for plotting
    plot_data = df[['Vsw', 'Ey']].dropna()
    if len(plot_data) < 2:
        raise ValueError("Not enough data points for scatter plot after NaN removal.")

    x = plot_data['Vsw'].values
    y = plot_data['Ey'].values

    # Perform linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(x, y, alpha=0.6, edgecolors='k', s=20, label='Data')

    # Plot regression line
    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = slope * x_line + intercept
    ax.plot(x_line, y_line, 'r-', linewidth=2, label=f'Fit: y={slope:.4f}x+{intercept:.4f}\nR²={r_value**2:.4f}')

    ax.set_xlabel('Solar Wind Speed (Vsw) [km/s]', fontsize=12)
    ax.set_ylabel('Tail Reconnection Rate (Ey) [mV/m]', fontsize=12)
    ax.set_title('Solar Wind Speed vs. Geomagnetic Tail Reconnection Rate', fontsize=14)
    ax.legend(loc='upper left')
    ax.grid(True, linestyle='--', alpha=0.7)

    # Annotate optimal lag if provided
    if optimal_lag is not None:
        annotation_text = f'Optimal Lag: {optimal_lag} min'
        ax.text(0.05, 0.95, annotation_text, transform=ax.transAxes,
                fontsize=11, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fig.savefig(output_path, dpi=300)
        plt.close(fig)

    return fig, ax


def plot_timeseries(
    df_vsw: pd.DataFrame,
    df_ey: pd.DataFrame,
    optimal_lag: Optional[int] = None,
    output_path: Optional[str] = None
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Generate a dual-axis time-series overlay of Vsw and Ey.

    Includes:
    - Timestamp on x-axis
    - Left y-axis for Vsw [km/s]
    - Right y-axis for Ey [mV/m]
    - Optimal lag annotation if provided

    Parameters
    ----------
    df_vsw : pd.DataFrame
        DataFrame with 'timestamp' and 'Vsw' columns.
    df_ey : pd.DataFrame
        DataFrame with 'timestamp' and 'Ey' columns.
    optimal_lag : int, optional
        Optimal lag in minutes to annotate.
    output_path : str, optional
        Path to save the figure.

    Returns
    -------
    fig, ax : matplotlib Figure, Axes
        The generated plot objects.
    """
    # Ensure timestamp is datetime and set as index for alignment
    if 'timestamp' in df_vsw.columns:
        df_vsw = df_vsw.set_index('timestamp')
    if 'timestamp' in df_ey.columns:
        df_ey = df_ey.set_index('timestamp')

    # Align indices
    common_index = df_vsw.index.intersection(df_ey.index)
    if len(common_index) == 0:
        raise ValueError("No common timestamps between Vsw and Ey data.")

    vsw_series = df_vsw.loc[common_index, 'Vsw'].dropna()
    ey_series = df_ey.loc[common_index, 'Ey'].dropna()

    # Re-align after dropna
    common_index_final = vsw_series.index.intersection(ey_series.index)
    if len(common_index_final) == 0:
        raise ValueError("No valid data points after NaN removal.")

    vsw_plot = vsw_series.loc[common_index_final]
    ey_plot = ey_series.loc[common_index_final]

    fig, ax1 = plt.subplots(figsize=(14, 6))

    color_vsw = 'tab:blue'
    ax1.set_xlabel('Time', fontsize=12)
    ax1.set_ylabel('Solar Wind Speed (Vsw) [km/s]', color=color_vsw, fontsize=12)
    ax1.plot(vsw_plot.index, vsw_plot.values, color=color_vsw, label='Vsw', linewidth=1.5)
    ax1.tick_params(axis='y', labelcolor=color_vsw)
    ax1.grid(True, linestyle='--', alpha=0.3)

    ax2 = ax1.twinx()
    color_ey = 'tab:red'
    ax2.set_ylabel('Tail Reconnection Rate (Ey) [mV/m]', color=color_ey, fontsize=12)
    ax2.plot(ey_plot.index, ey_plot.values, color=color_ey, label='Ey', linewidth=1.5, alpha=0.8)
    ax2.tick_params(axis='y', labelcolor=color_ey)

    # Combine legends
    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')

    plt.title('Time Series: Solar Wind Speed and Tail Reconnection Rate', fontsize=14)

    # Annotate optimal lag
    if optimal_lag is not None:
        annotation_text = f'Optimal Lag: {optimal_lag} min'
        ax1.text(0.05, 0.95, annotation_text, transform=ax1.transAxes,
                 fontsize=11, verticalalignment='top',
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fig.savefig(output_path, dpi=300)
        plt.close(fig)

    return fig, ax1


# Import stats locally to avoid circular dependency issues if any,
# though scipy.stats is standard.
from scipy import stats

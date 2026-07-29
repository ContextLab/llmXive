"""
Visualization module for generating plots.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/viz/plots.py
"""
import os
from typing import Optional, Tuple
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def plot_scatter(x: pd.Series, y: pd.Series, optimal_lag: int, output_path: str):
    """
    Generate scatter plot of lag-adjusted Vsw vs. Ey with regression line.
    
    Args:
        x: Solar wind time series (Vsw)
        y: THEMIS time series (Ey)
        optimal_lag: Optimal lag in minutes
        output_path: Path to save the plot
    """
    logger.info(f"Generating scatter plot with optimal lag {optimal_lag} min")
    
    # Apply lag shift
    x_lagged = x.shift(periods=optimal_lag // 5)  # Assuming 5-min cadence
    
    # Remove NaN pairs
    mask = ~(x_lagged.isna() | y.isna())
    x_clean = x_lagged[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 2:
        logger.error("Insufficient data for scatter plot")
        return
    
    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Scatter plot
    ax.scatter(x_clean, y_clean, alpha=0.5, s=20, label='Data points')
    
    # Regression line
    m, b = np.polyfit(x_clean, y_clean, 1)
    x_line = np.linspace(x_clean.min(), x_clean.max(), 100)
    y_line = m * x_line + b
    ax.plot(x_line, y_line, 'r-', linewidth=2, label=f'Fit: y={m:.3f}x+{b:.3f}')
    
    # Labels and title
    ax.set_xlabel('Solar Wind Speed (Vsw) [km/s]')
    ax.set_ylabel('Reconnection Rate (Ey) [mV/m]')
    ax.set_title(f'Scatter Plot (Optimal Lag: {optimal_lag} min)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Save plot
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    logger.info(f"Scatter plot saved to {output_path}")

def plot_timeseries(df_sw: pd.DataFrame, df_ey: pd.DataFrame, output_path: str):
    """
    Generate dual-axis time-series overlay of Vsw and Ey.
    
    Args:
        df_sw: Solar wind DataFrame
        df_ey: THEMIS DataFrame
        output_path: Path to save the plot
    """
    logger.info("Generating time-series plot")
    
    # Ensure data is aligned
    common_index = df_sw.index.intersection(df_ey.index)
    df_sw_clean = df_sw.loc[common_index]
    df_ey_clean = df_ey.loc[common_index]
    
    if len(df_sw_clean) < 2:
        logger.error("Insufficient data for time-series plot")
        return
    
    # Create plot
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Plot Vsw on left axis
    color_vsw = 'tab:blue'
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Solar Wind Speed (Vsw) [km/s]', color=color_vsw)
    ax1.plot(df_sw_clean.index, df_sw_clean['Vsw'], color=color_vsw, linewidth=1, label='Vsw')
    ax1.tick_params(axis='y', labelcolor=color_vsw)
    
    # Plot Ey on right axis
    ax2 = ax1.twinx()
    color_ey = 'tab:red'
    ax2.set_ylabel('Reconnection Rate (Ey) [mV/m]', color=color_ey)
    ax2.plot(df_ey_clean.index, df_ey_clean['Ey'], color=color_ey, linewidth=1, label='Ey')
    ax2.tick_params(axis='y', labelcolor=color_ey)
    
    # Title and legend
    plt.title('Time Series: Solar Wind Speed vs. Reconnection Rate')
    
    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    logger.info(f"Time-series plot saved to {output_path}")

"""
Visualization module for generating plots.

File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/viz/plots.py
"""
import os
from typing import Optional, Tuple
import matplotlib
matplotlib.use('Agg') # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
import logging

logger = logging.getLogger(__name__)

def plot_scatter(x: pd.Series, y: pd.Series, optimal_lag: int, output_path: str):
    """
    Generate scatter plot of lag-adjusted Vsw vs. Ey with regression line.
    
    Args:
        x: Solar wind speed series
        y: Reconnection rate series
        optimal_lag: Optimal lag in minutes
        output_path: Path to save the plot
    """
    plt.figure(figsize=(10, 6))
    
    # Scatter plot
    plt.scatter(x, y, alpha=0.5, label='Data')
    
    # Regression line
    m, b, r_value, p_value, std_err = stats.linregress(x, y)
    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = m * x_line + b
    plt.plot(x_line, y_line, 'r-', label=f'Regression (r={r_value:.2f})')
    
    plt.xlabel('Solar Wind Speed (Vsw) [km/s]')
    plt.ylabel('Reconnection Rate (Ey) [mV/m]')
    plt.title(f'Lag-Adjusted Vsw vs. Ey (Optimal Lag: {optimal_lag} min)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
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
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Plot Vsw
    color = 'tab:blue'
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Vsw [km/s]', color=color)
    ax1.plot(df_sw['timestamp'], df_sw['Vsw'], color=color, label='Vsw')
    ax1.tick_params(axis='y', labelcolor=color)
    
    # Plot Ey
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Ey [mV/m]', color=color)
    ax2.plot(df_ey['timestamp'], df_ey['Ey'], color=color, label='Ey', alpha=0.7)
    ax2.tick_params(axis='y', labelcolor=color)
    
    plt.title('Solar Wind Speed and Reconnection Rate Time Series')
    fig.tight_layout()
    
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Time series plot saved to {output_path}")
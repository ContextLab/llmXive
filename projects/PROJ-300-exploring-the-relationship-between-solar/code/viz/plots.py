"""
Visualization Module.

Generates scatter and time-series plots.

File path: code/viz/plots.py
"""
import os
from typing import Optional, Tuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from ..config import EARTH_RADIUS_KM, TAIL_DISTANCE_RE

def plot_scatter(
    x: pd.Series, 
    y: pd.Series, 
    optimal_lag: int, 
    output_path: str
):
    """
    Generates a scatter plot of Vsw vs Ey with regression line.
    
    Args:
        x: Vsw series.
        y: Ey series.
        optimal_lag: Optimal lag in minutes.
        output_path: Path to save the plot.
    """
    plt.figure(figsize=(10, 6))
    plt.scatter(x, y, alpha=0.5, label='Data')
    
    # Regression line
    m, b = np.polyfit(x.dropna(), y.dropna(), 1)
    x_line = np.linspace(x.min(), x.max(), 100)
    plt.plot(x_line, m*x_line + b, 'r-', label=f'Fit (r={m:.2f})')
    
    plt.xlabel('Solar Wind Speed (km/s)')
    plt.ylabel('Tail Reconnection Rate (nV)')
    plt.title(f'Vsw vs Ey (Lag = {optimal_lag} min)')
    plt.legend()
    plt.grid(True)
    
    plt.savefig(output_path, dpi=300)
    plt.close()

def plot_timeseries(
    df_sw: pd.DataFrame, 
    df_ey: pd.DataFrame, 
    optimal_lag: int, 
    output_path: str
):
    """
    Generates a dual-axis time-series overlay of Vsw and Ey.
    
    Args:
        df_sw: Solar wind DataFrame.
        df_ey: Ey DataFrame.
        optimal_lag: Optimal lag in minutes.
        output_path: Path to save the plot.
    """
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Vsw
    color = 'tab:blue'
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Vsw (km/s)', color=color)
    ax1.plot(df_sw.index, df_sw['Vsw'], color=color, label='Vsw')
    ax1.tick_params(axis='y', labelcolor=color)
    
    # Ey
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Ey (nV)', color=color)
    ax2.plot(df_ey.index, df_ey['Ey'], color=color, label='Ey', alpha=0.7)
    ax2.tick_params(axis='y', labelcolor=color)
    
    plt.title(f'Time Series Overlay (Lag = {optimal_lag} min)')
    
    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    plt.savefig(output_path, dpi=300)
    plt.close()

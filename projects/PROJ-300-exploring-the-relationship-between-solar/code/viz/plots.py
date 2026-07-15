"""
Visualization module for generating plots.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/viz/plots.py
"""
import os
from typing import Optional, Tuple
import matplotlib
# Use non-interactive backend for headless environments
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def plot_scatter(x: pd.Series, y: pd.Series, optimal_lag: float, output_path: str) -> None:
    """
    Generate a scatter plot of lag-adjusted Vsw vs Ey with regression line.
    
    Args:
        x: Vsw data.
        y: Ey data.
        optimal_lag: The optimal lag in minutes.
        output_path: Path to save the plot.
    """
    plt.figure(figsize=(10, 6))
    plt.scatter(x, y, alpha=0.6, label='Data')
    
    # Fit regression line
    z = np.polyfit(x.dropna(), y.dropna(), 1)
    p = np.poly1d(z)
    plt.plot(x, p(x), "r--", label=f'Fit (slope={z[0]:.3f})')
    
    plt.xlabel('Solar Wind Speed (km/s)')
    plt.ylabel('Tail Reconnection Rate (nV)')
    plt.title(f'Scatter Plot: Vsw vs Ey (Lag={optimal_lag:.1f} min)')
    plt.legend()
    plt.grid(True)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()

def plot_timeseries(df_sw: pd.DataFrame, df_ey: pd.DataFrame, optimal_lag: float, output_path: str) -> None:
    """
    Generate a dual-axis time-series overlay of Vsw and Ey.
    
    Args:
        df_sw: Solar wind DataFrame.
        df_ey: THEMIS DataFrame.
        optimal_lag: The optimal lag in minutes.
        output_path: Path to save the plot.
    """
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Plot Vsw
    color = 'tab:blue'
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Vsw (km/s)', color=color)
    ax1.plot(df_sw['timestamp'], df_sw['Vsw'], color=color, label='Vsw')
    ax1.tick_params(axis='y', labelcolor=color)
    
    # Plot Ey on secondary axis
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Ey (nV)', color=color)
    ax2.plot(df_ey['timestamp'], df_ey['Ey'], color=color, label='Ey', alpha=0.7)
    ax2.tick_params(axis='y', labelcolor=color)
    
    plt.title(f'Time Series: Vsw and Ey (Optimal Lag={optimal_lag:.1f} min)')
    fig.tight_layout()
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()

"""
Visualization module.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/viz/plots.py
"""
import os
from typing import Optional, Tuple
import matplotlib
matplotlib.use('Agg') # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

def plot_scatter(x: pd.Series, y: pd.Series, optimal_lag: int, output_path: str):
    """
    Generate scatter plot of lag-adjusted Vsw vs. Ey with regression line.
    
    Args:
        x: Solar wind speed (aligned).
        y: Ey (aligned).
        optimal_lag: The optimal lag used.
        output_path: Path to save the plot.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    plt.figure(figsize=(10, 6))
    plt.scatter(x, y, alpha=0.6, label='Data')
    
    # Regression line
    slope, intercept, r, p, se = stats.linregress(x, y)
    x_line = np.array([x.min(), x.max()])
    y_line = slope * x_line + intercept
    plt.plot(x_line, y_line, 'r-', label=f'Regression (r={r:.2f})')
    
    plt.xlabel('Vsw (km/s)')
    plt.ylabel('Ey (mV/m)')
    plt.title(f'Vsw vs Ey (Lag={optimal_lag} min)')
    plt.legend()
    plt.grid(True)
    
    plt.savefig(output_path)
    plt.close()

def plot_timeseries(df_sw: pd.DataFrame, df_ey: pd.DataFrame, output_path: str):
    """
    Generate dual-axis time-series overlay of Vsw and Ey.
    
    Args:
        df_sw: Solar wind DataFrame.
        df_ey: THEMIS DataFrame.
        output_path: Path to save the plot.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    color = 'tab:blue'
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Vsw (km/s)', color=color)
    ax1.plot(df_sw.index, df_sw['Vsw'], color=color, label='Vsw')
    ax1.tick_params(axis='y', labelcolor=color)
    
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Ey (mV/m)', color=color)
    ax2.plot(df_ey.index, df_ey['Ey'], color=color, label='Ey')
    ax2.tick_params(axis='y', labelcolor=color)
    
    plt.title('Solar Wind Speed and Tail Reconnection Rate')
    fig.tight_layout()
    
    plt.savefig(output_path)
    plt.close()

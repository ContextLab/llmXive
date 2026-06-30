"""
Visualization utilities for the pipeline.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/viz/plots.py
"""
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from typing import Optional, Tuple

def plot_scatter(
    x: pd.Series,
    y: pd.Series,
    output_path: str,
    optimal_lag: int,
    pearson_r: float
):
    """
    Generates a scatter plot of Vsw vs Ey with regression line.
    """
    plt.figure(figsize=(10, 6))
    plt.scatter(x, y, alpha=0.6, label='Data Points')
    
    # Regression line
    m, b = np.polyfit(x, y, 1)
    plt.plot(x, m*x + b, 'r-', label=f'Fit (r={pearson_r:.2f})')
    
    plt.xlabel('Solar Wind Speed (km/s)')
    plt.ylabel('Tail Reconnection Rate (nV/m)')
    plt.title(f'Lag-Adjusted Correlation (Lag={optimal_lag} min)')
    plt.legend()
    plt.grid(True)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()

def plot_timeseries(
    df_vsw: pd.DataFrame,
    df_ey: pd.DataFrame,
    output_path: str,
    optimal_lag: int
):
    """
    Generates a dual-axis time series plot.
    """
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    color1 = 'tab:blue'
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Vsw (km/s)', color=color1)
    ax1.plot(df_vsw.index, df_vsw['Vsw'], color=color1, label='Vsw')
    ax1.tick_params(axis='y', labelcolor=color1)
    
    ax2 = ax1.twinx()
    color2 = 'tab:red'
    ax2.set_ylabel('Ey (nV/m)', color=color2)
    ax2.plot(df_ey.index, df_ey['Ey'], color=color2, label='Ey', alpha=0.7)
    ax2.tick_params(axis='y', labelcolor=color2)
    
    plt.title(f'Time Series Overlay (Optimal Lag: {optimal_lag} min)')
    fig.tight_layout()
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()

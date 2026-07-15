"""
Visualization module.
Implements FR-008a (scatter) and FR-008b (timeseries).
File: projects/PROJ-300-exploring-the-relationship-between-solar/code/viz/plots.py
"""
import os
from typing import Optional, Tuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from ..config import EARTH_RADIUS_KM, TAIL_DISTANCE_RE

def plot_scatter(vsw: pd.Series, ey: pd.Series, optimal_lag: int, output_path: str):
    """
    Generate scatter plot of lag-adjusted Vsw vs. Ey.
    FR-008a: Scatter plot with regression line.
    
    Args:
        vsw: Solar wind speed series.
        ey: Tail reconnection rate series.
        optimal_lag: Optimal lag in minutes.
        output_path: Path to save the plot.
    """
    plt.figure(figsize=(10, 6))
    plt.scatter(vsw, ey, alpha=0.5, label='Data')
    
    # Regression line
    m, b = np.polyfit(vsw, ey, 1)
    x_line = np.linspace(vsw.min(), vsw.max(), 100)
    y_line = m * x_line + b
    plt.plot(x_line, y_line, 'r-', label=f'Regression (lag={optimal_lag} min)')
    
    plt.xlabel('Solar Wind Speed (km/s)')
    plt.ylabel('Tail Reconnection Rate (nV)')
    plt.title(f'Lag-Adjusted Correlation (Optimal Lag: {optimal_lag} min)')
    plt.legend()
    plt.grid(True)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()

def plot_timeseries(timestamp: pd.Series, vsw: pd.Series, ey: pd.Series, optimal_lag: int, output_path: str):
    """
    Generate dual-axis time-series overlay of Vsw and Ey.
    FR-008b: Dual-axis time-series plot.
    
    Args:
        timestamp: Timestamp series.
        vsw: Solar wind speed series.
        ey: Tail reconnection rate series.
        optimal_lag: Optimal lag in minutes.
        output_path: Path to save the plot.
    """
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    color1 = 'tab:blue'
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Solar Wind Speed (km/s)', color=color1)
    ax1.plot(timestamp, vsw, color=color1, label='Vsw')
    ax1.tick_params(axis='y', labelcolor=color1)
    
    ax2 = ax1.twinx()
    color2 = 'tab:red'
    ax2.set_ylabel('Tail Reconnection Rate (nV)', color=color2)
    ax2.plot(timestamp, ey, color=color2, label='Ey')
    ax2.tick_params(axis='y', labelcolor=color2)
    
    plt.title(f'Time Series Overlay (Optimal Lag: {optimal_lag} min)')
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()

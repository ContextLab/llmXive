"""
Visualization module for generating plots.
File: projects/PROJ-300-exploring-the-relationship-between-solar/code/viz/plots.py
"""
import os
from typing import Optional, Tuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from ..config import EARTH_RADIUS_KM, TAIL_DISTANCE_RE

def plot_scatter(x: pd.Series, y: pd.Series, output_path: str, optimal_lag: Optional[float] = None):
    """
    Generate scatter plot of lag-adjusted Vsw vs. Ey with regression line.
    """
    plt.figure(figsize=(10, 6))
    plt.scatter(x, y, alpha=0.6, label='Data')
    
    # Regression line
    if len(x) > 1:
        z = np.polyfit(x.dropna(), y.dropna(), 1)
        p = np.poly1d(z)
        plt.plot(x.dropna(), p(x.dropna()), "r--", label=f'Regression (r={np.corrcoef(x.dropna(), y.dropna())[0,1]:.2f})')
    
    plt.xlabel('Solar Wind Speed (km/s)')
    plt.ylabel('Tail Reconnection Rate (Ey, nV/m)')
    plt.title(f'Lag-Adjusted Vsw vs Ey (Lag: {optimal_lag:.1f} min)' if optimal_lag else 'Lag-Adjusted Vsw vs Ey')
    plt.legend()
    plt.grid(True)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()

def plot_timeseries(df1: pd.DataFrame, df2: pd.DataFrame, output_path: str, optimal_lag: Optional[float] = None):
    """
    Generate dual-axis time-series overlay of Vsw and Ey.
    """
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    color = 'tab:blue'
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Vsw (km/s)', color=color)
    ax1.plot(df1.index, df1['Vsw'], color=color, label='Vsw')
    ax1.tick_params(axis='y', labelcolor=color)
    
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Ey (nV/m)', color=color)
    ax2.plot(df2.index, df2['Ey'], color=color, label='Ey', alpha=0.7)
    ax2.tick_params(axis='y', labelcolor=color)
    
    title = f'Vsw and Ey Time Series (Lag: {optimal_lag:.1f} min)' if optimal_lag else 'Vsw and Ey Time Series'
    plt.title(title)
    
    fig.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()
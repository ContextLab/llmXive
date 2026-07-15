"""
Visualization module.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/viz/plots.py
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
    """
    plt.figure(figsize=(10, 6))
    plt.scatter(vsw, ey, alpha=0.5, label='Data Points')
    
    # Add regression line
    z = np.polyfit(vsw.dropna(), ey.dropna(), 1)
    p = np.poly1d(z)
    plt.plot(vsw.dropna(), p(vsw.dropna()), "r--", label=f'Fit (r={z[0]:.2f})')
    
    plt.xlabel(f'Solar Wind Speed (km/s) [Lag={optimal_lag} min]')
    plt.ylabel('Reconnection Rate Ey (mV/m)')
    plt.title(f'Lag-Adjusted Correlation (L*={optimal_lag} min)')
    plt.legend()
    plt.grid(True)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()

def plot_timeseries(df_sw: pd.DataFrame, df_ey: pd.DataFrame, optimal_lag: int, output_path: str):
    """
    Generate dual-axis time-series overlay.
    """
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    color = 'tab:blue'
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Vsw (km/s)', color=color)
    ax1.plot(df_sw.index, df_sw['Vsw'], color=color, label='Vsw')
    ax1.tick_params(axis='y', labelcolor=color)
    
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Ey (mV/m)', color=color)
    ax2.plot(df_ey.index, df_ey['Ey'], color=color, label='Ey', alpha=0.7)
    ax2.tick_params(axis='y', labelcolor=color)
    
    plt.title(f'Time Series Overlay (Optimal Lag={optimal_lag} min)')
    fig.tight_layout()
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()
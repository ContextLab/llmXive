"""
Visualization generation for statistical analysis (T037).
Generates scatter plots, KDE curves, and heatmaps for halo metrics.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from utils.logging import get_logger

logger = get_logger(__name__)

def setup_plot_style():
    """Configure matplotlib/seaborn style for publication quality."""
    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams['font.size'] = 12
    plt.rcParams['axes.labelsize'] = 14
    plt.rcParams['axes.titlesize'] = 16

def plot_metric_distributions(
    df: pd.DataFrame,
    metrics: List[str] = ['shape_s', 'spin_lambda', 'concentration_c'],
    output_dir: Optional[str] = None
) -> List[str]:
    """
    Plot KDE distributions for specified metrics.
    
    Args:
        df: DataFrame containing metric columns.
        metrics: List of column names to plot.
        output_dir: Directory to save figures. If None, shows plots.
        
    Returns:
        List of paths to saved figures.
    """
    setup_plot_style()
    saved_paths = []
    
    for metric in metrics:
        if metric not in df.columns:
            logger.warning(f"Metric {metric} not found in DataFrame, skipping.")
            continue
        
        plt.figure(figsize=(10, 6))
        sns.kdeplot(data=df, x=metric, fill=True, alpha=0.4)
        plt.title(f'Distribution of {metric.replace("_", " ").title()}')
        plt.xlabel(metric.replace("_", " ").title())
        plt.ylabel('Density')
        
        if output_dir:
            out_path = Path(output_dir) / f"distribution_{metric}.png"
            plt.savefig(out_path, dpi=300, bbox_inches='tight')
            saved_paths.append(str(out_path))
            logger.info(f"Saved distribution plot: {out_path}")
        else:
            plt.show()
        plt.close()
        
    return saved_paths

def plot_metric_vs_mass(
    df: pd.DataFrame,
    metrics: List[str] = ['shape_s', 'spin_lambda', 'concentration_c'],
    mass_col: str = 'halo_mass',
    output_dir: Optional[str] = None
) -> List[str]:
    """
    Plot scatter plots of metrics vs halo mass.
    
    Args:
        df: DataFrame.
        metrics: List of metric columns.
        mass_col: Column name for halo mass.
        output_dir: Directory to save figures.
        
    Returns:
        List of paths to saved figures.
    """
    setup_plot_style()
    saved_paths = []
    
    if mass_col not in df.columns:
        logger.warning(f"Mass column {mass_col} not found.")
        return saved_paths

    for metric in metrics:
        if metric not in df.columns:
            continue
        
        plt.figure(figsize=(10, 6))
        # Use log scale for mass if it spans orders of magnitude
        if df[mass_col].max() > df[mass_col].min() * 10:
            plt.xscale('log')
        
        sns.scatterplot(data=df, x=mass_col, y=metric, alpha=0.5, s=20)
        plt.title(f'{metric.replace("_", " ").title()} vs Halo Mass')
        plt.xlabel(f'Halo Mass ({mass_col})')
        plt.ylabel(metric.replace("_", " ").title())
        
        if output_dir:
            out_path = Path(output_dir) / f"scatter_{metric}_vs_mass.png"
            plt.savefig(out_path, dpi=300, bbox_inches='tight')
            saved_paths.append(str(out_path))
            logger.info(f"Saved scatter plot: {out_path}")
        else:
            plt.show()
        plt.close()
        
    return saved_paths

def plot_correlation_heatmap(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    output_dir: Optional[str] = None
) -> List[str]:
    """
    Plot correlation heatmap of selected metrics.
    
    Args:
        df: DataFrame.
        columns: Columns to include in correlation. If None, uses numeric columns.
        output_dir: Directory to save figures.
        
    Returns:
        List of paths to saved figures.
    """
    setup_plot_style()
    saved_paths = []
    
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if len(columns) < 2:
        logger.warning("Not enough numeric columns for correlation heatmap.")
        return saved_paths

    corr_matrix = df[columns].corr()
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, fmt=".2f")
    plt.title('Correlation Matrix of Halo Metrics')
    
    if output_dir:
        out_path = Path(output_dir) / "correlation_heatmap.png"
        plt.savefig(out_path, dpi=300, bbox_inches='tight')
        saved_paths.append(str(out_path))
        logger.info(f"Saved heatmap: {out_path}")
    else:
        plt.show()
    plt.close()
    
    return saved_paths

def generate_all_visualizations(
    df: pd.DataFrame,
    output_dir: str
) -> Dict[str, List[str]]:
    """
    Generate all standard visualizations for a dataset.
    
    Args:
        df: Input DataFrame.
        output_dir: Directory to save all figures.
        
    Returns:
        Dictionary mapping plot type to list of file paths.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    results = {
        "distributions": [],
        "scatter_vs_mass": [],
        "correlation": []
    }
    
    results["distributions"] = plot_metric_distributions(
        df, output_dir=output_dir
    )
    results["scatter_vs_mass"] = plot_metric_vs_mass(
        df, output_dir=output_dir
    )
    results["correlation"] = plot_correlation_heatmap(
        df, output_dir=output_dir
    )
    
    return results
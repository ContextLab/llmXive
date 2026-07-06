"""
Visualization utilities for the crack propagation prediction pipeline.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from code.config import ensure_dirs, FIGURES_DIR
from code.logging_config import get_logger

logger = get_logger(__name__)

def generate_pd_plot(
    df: pd.DataFrame,
    feature: str,
    target: str,
    output_path: Optional[str] = None
) -> Path:
    """
    Generate a partial dependence plot.
    
    Args:
        df: DataFrame with features and target
        feature: Feature name for x-axis
        target: Target variable name
        output_path: Optional path to save the plot
        
    Returns:
        Path to the saved plot
    """
    ensure_dirs()
    
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x=feature, y=target, alpha=0.6)
    plt.xlabel(feature)
    plt.ylabel(target)
    plt.title(f"Partial Dependence: {target} vs {feature}")
    
    if output_path:
        output_path = Path(output_path)
    else:
        output_path = FIGURES_DIR / f"pd_plot_{feature}.png"
    
    plt.savefig(output_path)
    plt.close()
    
    logger.info(f"Saved PD plot to {output_path}")
    return output_path

def plot_log_log_scatter(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    output_path: Optional[str] = None
) -> Path:
    """
    Plot log-log scatter plot for Paris Law verification.
    
    Args:
        df: DataFrame with data
        x_col: Column name for x-axis (delta_K)
        y_col: Column name for y-axis (da/dN)
        output_path: Optional path to save the plot
        
    Returns:
        Path to the saved plot
    """
    ensure_dirs()
    
    plt.figure(figsize=(10, 6))
    plt.scatter(np.log10(df[x_col]), np.log10(df[y_col]), alpha=0.6)
    plt.xlabel(f"log10({x_col})")
    plt.ylabel(f"log10({y_col})")
    plt.title("Log-Log Scatter Plot: Paris Law Verification")
    plt.grid(True, alpha=0.3)
    
    if output_path:
        output_path = Path(output_path)
    else:
        output_path = FIGURES_DIR / "log_log_scatter.png"
    
    plt.savefig(output_path)
    plt.close()
    
    logger.info(f"Saved log-log scatter plot to {output_path}")
    return output_path

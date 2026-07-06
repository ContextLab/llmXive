"""
Visualization utilities for crack propagation analysis.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

def generate_pd_plot(
    model,
    feature_name: str,
    X: pd.DataFrame,
    y: Optional[pd.Series] = None,
    out_path: Optional[Union[str, Path]] = None
) -> None:
    """
    Generate a Partial Dependence Plot for a given feature.
    
    Args:
        model: Trained model with predict method.
        feature_name: Name of the feature to plot.
        X: Feature dataframe.
        y: Target series (optional, for reference).
        out_path: Path to save the plot.
    """
    try:
        import matplotlib.pyplot as plt
        from sklearn.inspection import PartialDependenceDisplay
    except ImportError as e:
        logger.error(f"Missing dependencies for plotting: {e}")
        return

    fig, ax = plt.subplots()
    PartialDependenceDisplay.from_estimator(model, X, [feature_name], ax=ax)
    plt.title(f"Partial Dependence: {feature_name}")
    
    if out_path:
        plt.savefig(out_path)
        logger.info(f"Saved PDP to {out_path}")
    else:
        plt.show()

def plot_log_log_scatter(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    out_path: Optional[Union[str, Path]] = None
) -> None:
    """
    Plot a log-log scatter plot for da/dN vs Delta K.
    
    Args:
        df: DataFrame containing the data.
        x_col: Column name for x-axis (Delta K).
        y_col: Column name for y-axis (da/dN).
        out_path: Path to save the plot.
    """
    import matplotlib.pyplot as plt

    plt.figure(figsize=(8, 6))
    plt.scatter(df[x_col], df[y_col], alpha=0.5)
    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.title(f"Log-Log Scatter: {y_col} vs {x_col}")
    plt.grid(True, which="both", ls="-", alpha=0.2)

    if out_path:
        plt.savefig(out_path)
        logger.info(f"Saved log-log scatter to {out_path}")
    else:
        plt.show()

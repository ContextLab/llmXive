"""Plotting utilities for visualization."""
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional, Tuple

from code.data.paths import get_results_path

logger = logging.getLogger(__name__)

def plot_variability_vs_flexibility(
    variability: np.ndarray,
    flexibility: np.ndarray,
    beta: float,
    intercept: float,
    r_value: float,
    p_value: float,
    output_path: Optional[str] = None
) -> str:
    """
    Create a scatter plot of variability vs flexibility with regression line.
    
    Args:
        variability: Array of variability metrics.
        flexibility: Array of flexibility scores.
        beta: Regression coefficient for variability.
        intercept: Regression intercept.
        r_value: Pearson correlation coefficient.
        p_value: Statistical p-value.
        output_path: Optional path to save figure. Defaults to results directory.
    
    Returns:
        Path to the saved figure.
    """
    if output_path is None:
        output_path = str(get_results_path() / "variability_vs_flexibility.png")
    
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # Scatter plot
    ax.scatter(variability, flexibility, alpha=0.6, s=50, color='steelblue')
    
    # Regression line
    x_line = np.array([variability.min(), variability.max()])
    y_line = intercept + beta * x_line
    ax.plot(x_line, y_line, 'r-', linewidth=2, label=f'Regression line (β={beta:.4f})')
    
    # Labels and title
    ax.set_xlabel('RSFC Variability (PCA Component 1)', fontsize=12)
    ax.set_ylabel('Cognitive Flexibility Score', fontsize=12)
    ax.set_title(
        f'RSFC Variability vs Cognitive Flexibility\n'
        f'r={r_value:.4f}, p={p_value:.4f}',
        fontsize=14
    )
    
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved figure to {output_path}")
    return output_path

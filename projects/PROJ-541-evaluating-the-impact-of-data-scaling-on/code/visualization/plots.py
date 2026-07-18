import os
import logging
from pathlib import Path
from typing import Optional
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def generate_error_rate_plot(aggregate_metrics: pd.DataFrame, output_path: str = "figures/error_rate_plot.png"):
    """
    Generate error rate plot showing empirical rate vs nominal alpha with 95% CI.
    
    Parameters:
    -----------
    aggregate_metrics : pd.DataFrame
        DataFrame containing aggregate metrics with columns:
        - scaling_method
        - empirical_error_rate
        - ci_lower
        - ci_upper
    output_path : str
        Path to save the plot
    """
    if aggregate_metrics is None or aggregate_metrics.empty:
        logger.error("No aggregate metrics provided for plotting")
        return
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set style
    sns.set(style="whitegrid")
    plt.figure(figsize=(10, 6))
    
    # Plot error rates with confidence intervals
    x = range(len(aggregate_metrics))
    y = aggregate_metrics['empirical_error_rate'].values
    yerr = [y - aggregate_metrics['ci_lower'].values, aggregate_metrics['ci_upper'].values - y]
    
    plt.errorbar(x, y, yerr=yerr, fmt='o', capsize=5, label='Empirical Error Rate', color='blue')
    
    # Plot nominal alpha line
    plt.axhline(y=0.05, color='red', linestyle='--', label='Nominal Alpha (0.05)')
    
    # Customize plot
    plt.xticks(x, aggregate_metrics['scaling_method'], rotation=45)
    plt.xlabel('Scaling Method')
    plt.ylabel('Error Rate')
    plt.title('Empirical Type I Error Rate vs Nominal Alpha')
    plt.legend()
    plt.ylim(0, 0.15)
    
    # Save plot
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    logger.info(f"Error rate plot saved to {output_path}")

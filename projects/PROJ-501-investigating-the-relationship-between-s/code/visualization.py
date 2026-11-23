import logging
import os
from pathlib import Path
from typing import Optional
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

# Ensure analysis outputs explicitly frame findings as "associational" only (SC-005)
ASSOCIATIONAL_CAPTION = (
    "Associational Relationship: Cumulative XUV Flux vs. Retention Fraction. "
    "Note: This plot illustrates a statistical association. Causality is not established."
)

def plot_flux_vs_retention(df: pd.DataFrame, output_path: str):
    """
    Generate scatter plot: X-axis = Cumulative XUV Flux, Y-axis = Retention Fraction.
    Includes regression line and labels.
    Ensures the plot title and caption explicitly frame findings as associational (SC-005).
    """
    logger = logging.getLogger(__name__)
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepare data
    x = df['cumulative_flux'].values
    y = df['retention_fraction'].values
    
    # Filter out non-finite values for plotting
    mask = np.isfinite(x) & np.isfinite(y)
    x_plot = x[mask]
    y_plot = y[mask]
    
    if len(x_plot) == 0:
        logger.error("No valid data points for plotting.")
        raise ValueError("No valid data points for plotting.")
    
    # Create figure
    plt.figure(figsize=(10, 6))
    
    # Scatter plot
    plt.scatter(x_plot, y_plot, alpha=0.6, edgecolors='k', s=50, label='Systems')
    
    # Add regression line (linear fit for visualization)
    if len(x_plot) > 1:
        m, b = np.polyfit(x_plot, y_plot, 1)
        x_line = np.linspace(min(x_plot), max(x_plot), 100)
        y_line = m * x_line + b
        plt.plot(x_line, y_line, 'r-', linewidth=2, label='Linear Trend')
        
        # Calculate Spearman rho for annotation
        rho, p_val = spearmanr(x_plot, y_plot)
        annotation = f"Spearman ρ = {rho:.3f}, p = {p_val:.3e}"
        plt.text(0.05, 0.95, annotation, transform=plt.gca().transAxes, 
                 fontsize=10, verticalalignment='top', 
                 bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Labels and Title (Explicitly associational per SC-005)
    plt.xlabel('Cumulative XUV Flux (erg/cm²)')
    plt.ylabel('Atmospheric Retention Fraction')
    plt.title('Associational Relationship: Cumulative XUV Flux vs. Retention Fraction')
    
    # Add caption/legend with associational disclaimer
    plt.figtext(0.5, 0.01, ASSOCIATIONAL_CAPTION, 
                ha='center', fontsize=8, style='italic', wrap=True)
    
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Save plot
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Plot saved to {output_path}")

def run_visualization_pipeline(input_path: str = "data/processed/derived_physics.csv",
                               output_path: str = "data/results/flux_vs_retention.png"):
    """
    Main pipeline to generate the visualization.
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting visualization pipeline...")
    
    # Load data
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} records from {input_path}")
    
    # Generate plot
    plot_flux_vs_retention(df, output_path)
    
    logger.info("Visualization pipeline complete.")
    return output_path

if __name__ == "__main__":
    run_visualization_pipeline()
"""
Task T046: Generate final figures (linear fit, threshold sensitivity).

This script loads the processed dataset and sensitivity analysis results
to generate publication-ready figures for the paper.

Outputs:
  - paper/figures/linear_fit_age_burden.png
  - paper/figures/threshold_sensitivity.png
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments
import matplotlib.pyplot as plt
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_output_dir():
    """Ensure the paper/figures directory exists."""
    fig_dir = Path("paper/figures")
    fig_dir.mkdir(parents=True, exist_ok=True)
    return fig_dir

def load_processed_dataset():
    """Load the final processed dataset."""
    path = Path("code/data/processed/mito_aging_dataset.csv")
    if not path.exists():
        raise FileNotFoundError(
            f"Processed dataset not found at {path}. "
            "Please run the data pipeline (T012-T020) first."
        )
    logger.info(f"Loading processed dataset from {path}")
    return pd.read_csv(path)

def load_sensitivity_results():
    """Load sensitivity analysis results."""
    path = Path("code/data/processed/sensitivity_analysis.csv")
    if not path.exists():
        raise FileNotFoundError(
            f"Sensitivity results not found at {path}. "
            "Please run the sensitivity analysis (T032-T038) first."
        )
    logger.info(f"Loading sensitivity results from {path}")
    return pd.read_csv(path)

def plot_linear_fit(df, output_path):
    """
    Plot linear fit of Age vs Heteroplasmy Burden.
    
    Creates a scatter plot with a linear regression line,
    95% confidence interval, and annotated statistics.
    """
    logger.info("Generating linear fit figure...")
    
    # Extract variables
    x = df['burden']
    y = df['age']
    
    # Calculate linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Scatter plot with transparency
    ax.scatter(x, y, alpha=0.4, s=20, c='#1f77b4', label='Samples')
    
    # Plot regression line
    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = slope * x_line + intercept
    ax.plot(x_line, y_line, 'r-', linewidth=2, label=f'Linear Fit (r={r_value:.3f})')
    
    # Add confidence interval (optional, simplified)
    # Using standard error for a rough CI band
    y_pred = slope * x_line + intercept
    margin = 1.96 * std_err * np.sqrt(1 + 1/len(x) + (x_line - x.mean())**2 / ((len(x)-1) * x.var()))
    ax.fill_between(x_line, y_pred - margin, y_pred + margin, color='red', alpha=0.2, label='95% CI')
    
    # Labels and title
    ax.set_xlabel('Heteroplasmy Burden (variants/sample)', fontsize=12)
    ax.set_ylabel('Age (years)', fontsize=12)
    ax.set_title('Correlation between Mitochondrial Heteroplasmy Burden and Age', fontsize=14)
    
    # Annotation with statistics
    stats_text = f'r = {r_value:.3f}\np = {p_value:.2e}\nn = {len(x)}'
    ax.text(0.05, 0.95, stats_text, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    
    # Save figure
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved linear fit figure to {output_path}")

def plot_threshold_sensitivity(df_sens, output_path):
    """
    Plot threshold sensitivity analysis.
    
    Shows how the correlation coefficient (r) changes across different
    heteroplasmy burden thresholds (e.g., 0.5%, 1.0%, 2.0%).
    """
    logger.info("Generating threshold sensitivity figure...")
    
    # Ensure we have the necessary columns
    if 'threshold' not in df_sens.columns or 'correlation' not in df_sens.columns:
        raise ValueError("Sensitivity results missing 'threshold' or 'correlation' columns")
    
    # Sort by threshold
    df_sorted = df_sens.sort_values('threshold')
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot correlation vs threshold
    ax.plot(df_sorted['threshold'], df_sorted['correlation'], 'o-', 
            color='darkgreen', linewidth=2, markersize=8, label='Spearman r')
    
    # Add error bars if available (e.g., p-values or standard errors)
    if 'p_value' in df_sorted.columns:
        # Convert p-values to -log10 for visualization if needed, or just annotate
        pass
    
    # Labels and title
    ax.set_xlabel('Heteroplasmy Threshold (%)', fontsize=12)
    ax.set_ylabel('Correlation Coefficient (Spearman r)', fontsize=12)
    ax.set_title('Sensitivity of Age-Burden Correlation to Threshold Choice', fontsize=14)
    
    # Grid
    ax.grid(True, alpha=0.3)
    
    # Annotate points
    for i, row in df_sorted.iterrows():
        ax.annotate(f"r={row['correlation']:.3f}", 
                    (row['threshold'], row['correlation']),
                    textcoords="offset points", xytext=(0,10), ha='center', fontsize=9)
    
    ax.legend(loc='upper left')
    
    # Save figure
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved threshold sensitivity figure to {output_path}")

def main():
    """Main entry point for figure generation."""
    try:
        # Ensure output directory
        fig_dir = ensure_output_dir()
        
        # Load data
        df_processed = load_processed_dataset()
        df_sens = load_sensitivity_results()
        
        # Generate Figure 1: Linear Fit
        path_linear = fig_dir / "linear_fit_age_burden.png"
        plot_linear_fit(df_processed, path_linear)
        
        # Generate Figure 2: Threshold Sensitivity
        path_sens = fig_dir / "threshold_sensitivity.png"
        plot_threshold_sensitivity(df_sens, path_sens)
        
        logger.info("All figures generated successfully.")
        
    except Exception as e:
        logger.error(f"Failed to generate figures: {e}")
        raise

if __name__ == "__main__":
    main()
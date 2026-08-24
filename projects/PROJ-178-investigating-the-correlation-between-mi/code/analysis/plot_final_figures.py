"""
plot_final_figures.py

Generates the final figures for the mitochondrial DNA aging correlation study:
1. Linear fit scatter plot of Age vs. Heteroplasmy Burden.
2. Threshold sensitivity plot showing correlation coefficients across VAF thresholds.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless execution

from config.environment import get_local_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_output_dir():
    """Ensure the paper/figures directory exists."""
    paths = get_local_paths()
    figures_dir = paths['figures_dir']
    figures_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory ensured: {figures_dir}")
    return figures_dir

def load_processed_dataset():
    """
    Load the main processed dataset.
    Expected path: code/data/processed/mito_aging_dataset.csv
    """
    paths = get_local_paths()
    dataset_path = paths['processed_dataset_path']
    
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(
            f"Processed dataset not found at {dataset_path}. "
            "Ensure T018/T020 has completed successfully."
        )
    
    logger.info(f"Loading processed dataset from {dataset_path}")
    df = pd.read_csv(dataset_path)
    
    # Validate required columns
    required_cols = ['age', 'burden', 'sample_id']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in dataset: {missing}")
    
    return df

def load_sensitivity_results():
    """
    Load sensitivity analysis results.
    Expected path: code/data/processed/sensitivity_results.csv
    """
    paths = get_local_paths()
    sensitivity_path = paths['sensitivity_results_path']
    
    if not os.path.exists(sensitivity_path):
        raise FileNotFoundError(
            f"Sensitivity results not found at {sensitivity_path}. "
            "Ensure T032 has completed successfully."
        )
    
    logger.info(f"Loading sensitivity results from {sensitivity_path}")
    df = pd.read_csv(sensitivity_path)
    
    # Validate required columns
    required_cols = ['threshold', 'coefficient', 'p_value']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in sensitivity results: {missing}")
    
    return df

def plot_linear_fit(df, output_path):
    """
    Generate a scatter plot of Age vs. Heteroplasmy Burden with a linear fit line.
    
    Args:
        df: DataFrame with 'age' and 'burden' columns.
        output_path: Path to save the figure.
    """
    logger.info("Generating linear fit plot...")
    
    plt.figure(figsize=(10, 6))
    
    # Scatter plot
    plt.scatter(df['age'], df['burden'], alpha=0.6, s=20, color='#1f77b4', label='Samples')
    
    # Linear fit
    z = np.polyfit(df['age'], df['burden'], 1)
    p = np.poly1d(z)
    x_line = np.linspace(df['age'].min(), df['age'].max(), 100)
    plt.plot(x_line, p(x_line), "r-", linewidth=2, label=f'Linear Fit (slope={z[0]:.2e})')
    
    # Labels and Title
    plt.xlabel('Age (years)', fontsize=12)
    plt.ylabel('Heteroplasmy Burden (VAF ≥ 1%)', fontsize=12)
    plt.title('Correlation between Mitochondrial Heteroplasmy Burden and Age', fontsize=14)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Save figure
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    logger.info(f"Linear fit plot saved to {output_path}")

def plot_threshold_sensitivity(df, output_path):
    """
    Generate a line plot showing the correlation coefficient across different VAF thresholds.
    
    Args:
        df: DataFrame with 'threshold', 'coefficient', and 'p_value' columns.
        output_path: Path to save the figure.
    """
    logger.info("Generating threshold sensitivity plot...")
    
    # Ensure thresholds are numeric and sorted
    df = df.sort_values('threshold')
    
    plt.figure(figsize=(10, 6))
    
    # Plot coefficient
    plt.plot(df['threshold'], df['coefficient'], marker='o', linewidth=2, color='#2ca02c', label='Spearman Coefficient')
    
    # Fill between for visual clarity if we had error bars, but here just the line
    # Add p-value annotation if significant
    for _, row in df.iterrows():
        annot = f"p={row['p_value']:.3g}" if row['p_value'] < 0.05 else ""
        if annot:
            plt.annotate(annot, (row['threshold'], row['coefficient']), 
                       textcoords="offset points", xytext=(0,10), ha='center', fontsize=9)
    
    plt.xlabel('VAF Threshold', fontsize=12)
    plt.ylabel('Spearman Correlation Coefficient', fontsize=12)
    plt.title('Sensitivity Analysis: Correlation Coefficient vs. VAF Threshold', fontsize=14)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Save figure
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    logger.info(f"Threshold sensitivity plot saved to {output_path}")

def main():
    """Main entry point to generate all final figures."""
    try:
        # Ensure output directory
        figures_dir = ensure_output_dir()
        
        # Load data
        df_dataset = load_processed_dataset()
        df_sensitivity = load_sensitivity_results()
        
        # Define output paths
        path_linear = figures_dir / "linear_fit_age_burden.png"
        path_sensitivity = figures_dir / "threshold_sensitivity.png"
        
        # Generate plots
        plot_linear_fit(df_dataset, path_linear)
        plot_threshold_sensitivity(df_sensitivity, path_sensitivity)
        
        logger.info("All final figures generated successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error generating figures: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

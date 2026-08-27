"""
Final figure generation for the mitochondrial aging correlation study.
Generates:
1. Rank-OLS fit plot
2. Threshold sensitivity plot
3. Subgroup comparison plot
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Ensure plot directory exists
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments

logger = logging.getLogger(__name__)

def ensure_output_dir():
    """Ensure the paper/figures directory exists."""
    fig_dir = Path("paper/figures")
    fig_dir.mkdir(parents=True, exist_ok=True)
    return fig_dir

def load_processed_dataset():
    """Load the main processed dataset containing age and heteroplasmy burden."""
    # Path relative to project root
    data_path = Path("code/data/processed/mito_aging_dataset.csv")
    if not data_path.exists():
        raise FileNotFoundError(f"Processed dataset not found at {data_path}. "
                                "Please run data acquisition tasks first.")
    return pd.read_csv(data_path)

def load_sensitivity_results():
    """Load sensitivity analysis results (threshold sweep)."""
    # Path relative to project root
    data_path = Path("code/data/processed/sensitivity_results.csv")
    if not data_path.exists():
        logger.warning(f"Sensitivity results not found at {data_path}. "
                       "Skipping threshold sensitivity plot.")
        return None
    return pd.read_csv(data_path)

def load_subgroup_results():
    """Load subgroup analysis results."""
    # Path relative to project root
    data_path = Path("code/data/processed/subgroup_results.csv")
    if not data_path.exists():
        logger.warning(f"Subgroup results not found at {data_path}. "
                       "Skipping subgroup comparison plot.")
        return None
    return pd.read_csv(data_path)

def plot_linear_fit(df, output_path):
    """
    Plot the Rank-OLS fit: Rank(Age) vs Rank(Heteroplasmy Burden).
    Includes a regression line and 95% CI.
    """
    logger.info("Generating Rank-OLS fit plot...")
    
    # Prepare data: Rank transform
    df_plot = df.copy()
    # Handle potential NaNs
    df_plot = df_plot.dropna(subset=['age', 'heteroplasmy_burden'])
    
    if df_plot.empty:
        logger.warning("No valid data for linear fit plot.")
        return

    df_plot['rank_age'] = df_plot['age'].rank()
    df_plot['rank_burden'] = df_plot['heteroplasmy_burden'].rank()

    plt.figure(figsize=(8, 6))
    sns.set_style("whitegrid")
    
    # Scatter plot with regression
    sns.regplot(
        data=df_plot,
        x='rank_burden',
        y='rank_age',
        scatter_kws={'alpha': 0.4, 's': 20},
        line_kws={'color': 'red', 'linewidth': 2},
        ci=95
    )
    
    plt.title('Rank-OLS Fit: Age vs Heteroplasmy Burden', fontsize=14)
    plt.xlabel('Rank(Heteroplasmy Burden)', fontsize=12)
    plt.ylabel('Rank(Age)', fontsize=12)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved linear fit plot to {output_path}")

def plot_threshold_sensitivity(df_sensitivity, output_path):
    """
    Plot threshold sensitivity: Correlation coefficient vs VAF threshold.
    """
    logger.info("Generating threshold sensitivity plot...")
    
    if df_sensitivity is None or df_sensitivity.empty:
        return

    plt.figure(figsize=(8, 6))
    sns.set_style("whitegrid")
    
    # Ensure threshold is numeric for plotting
    df_sensitivity['threshold'] = pd.to_numeric(df_sensitivity['threshold'], errors='coerce')
    df_valid = df_sensitivity.dropna(subset=['threshold', 'coefficient'])
    
    if df_valid.empty:
        logger.warning("No valid data for sensitivity plot.")
        return

    plt.plot(
        df_valid['threshold'],
        df_valid['coefficient'],
        marker='o',
        linestyle='-',
        color='darkblue',
        linewidth=2,
        markersize=8
    )
    
    plt.title('Threshold Sensitivity Analysis', fontsize=14)
    plt.xlabel('VAF Threshold (%)', fontsize=12)
    plt.ylabel('Correlation Coefficient', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved sensitivity plot to {output_path}")

def plot_subgroup_comparison(df_subgroup, output_path):
    """
    Plot subgroup comparison: Coefficient by ancestry group.
    """
    logger.info("Generating subgroup comparison plot...")
    
    if df_subgroup is None or df_subgroup.empty:
        return

    plt.figure(figsize=(10, 6))
    sns.set_style("whitegrid")
    
    # Sort by ancestry for consistent plotting
    # Assuming 'ancestry' column exists
    df_plot = df_subgroup.sort_values('ancestry')
    
    plt.bar(
        df_plot['ancestry'],
        df_plot['coefficient'],
        color='teal',
        edgecolor='black',
        alpha=0.8
    )
    
    # Add error bars if p-values or standard errors are available
    # For now, just plotting coefficients as per task description
    
    plt.title('Subgroup Analysis: Correlation by Ancestry', fontsize=14)
    plt.xlabel('Ancestry Group', fontsize=12)
    plt.ylabel('Correlation Coefficient', fontsize=12)
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved subgroup plot to {output_path}")

def main():
    """Main entry point to generate all final figures."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    fig_dir = ensure_output_dir()
    
    try:
        # 1. Load Data
        df_main = load_processed_dataset()
        df_sens = load_sensitivity_results()
        df_sub = load_subgroup_results()
        
        # 2. Generate Plots
        # Plot 1: Rank-OLS Fit
        plot_linear_fit(df_main, fig_dir / "rank_ols_fit.png")
        
        # Plot 2: Threshold Sensitivity
        plot_threshold_sensitivity(df_sens, fig_dir / "threshold_sensitivity.png")
        
        # Plot 3: Subgroup Comparison
        plot_subgroup_comparison(df_sub, fig_dir / "subgroup_comparison.png")
        
        logger.info("All final figures generated successfully.")
        
    except Exception as e:
        logger.error(f"Failed to generate figures: {e}")
        raise

if __name__ == "__main__":
    main()

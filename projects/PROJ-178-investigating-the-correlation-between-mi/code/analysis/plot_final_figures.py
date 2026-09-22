"""
plot_final_figures.py

Generates the final figures for the mitochondrial DNA variation and aging study:
1. Rank-OLS fit (scatter with regression line)
2. Threshold sensitivity analysis
3. Subgroup comparison (ancestry-based)

Outputs are written to paper/figures/
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
import seaborn as sns

from config.environment import get_local_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_output_dir():
    """Ensure the output directory exists."""
    paths = get_local_paths()
    fig_dir = paths['figures_dir']
    fig_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directory: {fig_dir}")
    return fig_dir

def load_processed_dataset():
    """Load the main processed dataset."""
    paths = get_local_paths()
    data_path = paths['processed_dataset_path']
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Processed dataset not found at {data_path}. "
                                "Run the data pipeline first.")
    df = pd.read_csv(data_path)
    logger.info(f"Loaded processed dataset with {len(df)} samples")
    return df

def load_sensitivity_results():
    """Load threshold sensitivity results."""
    paths = get_local_paths()
    data_path = paths['sensitivity_results_path']
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Sensitivity results not found at {data_path}")
    df = pd.read_csv(data_path)
    logger.info(f"Loaded sensitivity results with {len(df)} rows")
    return df

def load_subgroup_results():
    """Load subgroup analysis results."""
    paths = get_local_paths()
    data_path = paths['subgroup_results_path']
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Subgroup results not found at {data_path}")
    df = pd.read_csv(data_path)
    logger.info(f"Loaded subgroup results with {len(df)} rows")
    return df

def plot_linear_fit(df, output_path):
    """
    Plot the Rank-OLS fit: heteroplasmy burden vs age with regression line.
    """
    logger.info("Generating Rank-OLS fit plot...")
    
    plt.figure(figsize=(10, 8))
    sns.set_style("whitegrid")
    
    # Scatter plot
    sns.scatterplot(
        data=df,
        x='heteroplasmy_burden',
        y='age',
        alpha=0.6,
        color='#2E86AB',
        label='Samples'
    )
    
    # Regression line (Rank-OLS fit)
    # We use seaborn's regplot which fits a linear model
    # Note: This is a visual representation; the actual Rank-OLS was done in model.py
    sns.regplot(
        data=df,
        x='heteroplasmy_burden',
        y='age',
        scatter=False,
        color='#A23B72',
        line_kws={'linewidth': 2, 'label': 'Rank-OLS Fit'}
    )
    
    plt.xlabel('Heteroplasmy Burden (VAF ≥ 1%)', fontsize=12)
    plt.ylabel('Age (years)', fontsize=12)
    plt.title('Mitochondrial Heteroplasmy Burden vs Age', fontsize=14, fontweight='bold')
    plt.legend(fontsize=10)
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved Rank-OLS fit plot to {output_path}")

def plot_threshold_sensitivity(df, output_path):
    """
    Plot threshold sensitivity analysis: correlation coefficient vs VAF threshold.
    """
    logger.info("Generating threshold sensitivity plot...")
    
    plt.figure(figsize=(10, 6))
    sns.set_style("whitegrid")
    
    # Sort by threshold for proper line drawing
    df_sorted = df.sort_values('threshold')
    
    plt.plot(
        df_sorted['threshold'],
        df_sorted['coefficient'],
        marker='o',
        linewidth=2,
        markersize=8,
        color='#F18F01',
        label='Correlation Coefficient'
    )
    
    # Add horizontal line at 0
    plt.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.7)
    
    plt.xlabel('VAF Threshold (%)', fontsize=12)
    plt.ylabel('Correlation Coefficient', fontsize=12)
    plt.title('Sensitivity Analysis: Correlation vs VAF Threshold', fontsize=14, fontweight='bold')
    plt.legend(fontsize=10)
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved threshold sensitivity plot to {output_path}")

def plot_subgroup_comparison(df, output_path):
    """
    Plot subgroup comparison: correlation coefficients by ancestry.
    """
    logger.info("Generating subgroup comparison plot...")
    
    plt.figure(figsize=(10, 6))
    sns.set_style("whitegrid")
    
    # Bar plot with error bars if available (using p-value as proxy for significance)
    # Assuming df has 'ancestry', 'coefficient', and 'p_value' columns
    sns.barplot(
        data=df,
        x='ancestry',
        y='coefficient',
        palette='viridis',
        edgecolor='black',
        alpha=0.8
    )
    
    # Add horizontal line at 0
    plt.axhline(y=0, color='gray', linestyle='--', linewidth=1, alpha=0.7)
    
    plt.xlabel('Ancestry Group', fontsize=12)
    plt.ylabel('Correlation Coefficient', fontsize=12)
    plt.title('Subgroup Analysis: Correlation by Ancestry', fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved subgroup comparison plot to {output_path}")

def main():
    """Main function to generate all final figures."""
    logger.info("Starting final figure generation...")
    
    try:
        # Ensure output directory exists
        fig_dir = ensure_output_dir()
        
        # Load data
        processed_df = load_processed_dataset()
        sensitivity_df = load_sensitivity_results()
        subgroup_df = load_subgroup_results()
        
        # Generate plots
        plot_linear_fit(
            processed_df,
            os.path.join(fig_dir, 'rank_ols_fit.png')
        )
        
        plot_threshold_sensitivity(
            sensitivity_df,
            os.path.join(fig_dir, 'threshold_sensitivity.png')
        )
        
        plot_subgroup_comparison(
            subgroup_df,
            os.path.join(fig_dir, 'subgroup_comparison.png')
        )
        
        logger.info("All final figures generated successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error generating figures: {e}")
        raise

if __name__ == '__main__':
    main()

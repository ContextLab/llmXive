"""
Final Figure Generation for Mitochondrial Aging Correlation Study.

Generates publication-ready figures:
1. Linear fit of Heteroplasmy Burden vs Age with confidence interval.
2. Threshold Sensitivity plot showing correlation stability across VAF cutoffs.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Ensure standard matplotlib backend for non-interactive environments
if os.environ.get('DISPLAY') is None:
    plt.switch_backend('Agg')

# Set visual style
sns.set_theme(style="whitegrid", context="talk", font="DejaVu Sans")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 12

def ensure_output_dir(output_dir: str) -> Path:
    """Create the output directory if it does not exist."""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directory: {path}")
    return path

def load_processed_dataset(filepath: str) -> pd.DataFrame:
    """
    Load the main processed dataset containing age and burden.
    Expects columns: 'age', 'burden', 'population', 'sex'.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Processed dataset not found at {filepath}")
    
    logger.info(f"Loading processed dataset from {filepath}")
    df = pd.read_csv(filepath)
    
    # Basic validation
    required_cols = ['age', 'burden']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in dataset: {missing}")
    
    # Drop rows with missing critical values
    initial_count = len(df)
    df = df.dropna(subset=required_cols)
    dropped = initial_count - len(df)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows due to missing critical values.")
    
    logger.info(f"Loaded {len(df)} samples for plotting.")
    return df

def load_sensitivity_results(filepath: str) -> pd.DataFrame:
    """
    Load sensitivity analysis results.
    Expects columns: 'threshold', 'correlation', 'p_value', 'n_samples'.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Sensitivity results not found at {filepath}")
    
    logger.info(f"Loading sensitivity results from {filepath}")
    df = pd.read_csv(filepath)
    
    required_cols = ['threshold', 'correlation']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in sensitivity results: {missing}")
    
    logger.info(f"Loaded {len(df)} threshold points.")
    return df

def plot_linear_fit(df: pd.DataFrame, output_path: Path):
    """
    Plot Heteroplasmy Burden vs Age with a linear regression fit and 95% CI.
    """
    logger.info("Generating linear fit plot...")
    
    plt.figure(figsize=(10, 7))
    
    # Use seaborn regplot for automatic regression and confidence interval
    # We use a subset for the scatter to avoid overplotting if dataset is large
    # but regplot handles the regression on the full data.
    plot_kwargs = {
        'x': 'age',
        'y': 'burden',
        'data': df,
        'scatter_kws': {
            'alpha': 0.4, 
            's': 20, 
            'color': '#2c7bb6',
            'edgecolors': 'w',
            'linewidths': 0.2
        },
        'line_kws': {
            'color': '#d7191c',
            'lw': 2.5,
            'label': 'Linear Fit'
        },
        'ci': 95,
        'truncate': False
    }
    
    sns.regplot(**plot_kwargs)
    
    plt.title('Heteroplasmy Burden vs. Age', fontsize=16, fontweight='bold')
    plt.xlabel('Age (years)', fontsize=14)
    plt.ylabel('Heteroplasmy Burden (VAF ≥ 1%)', fontsize=14)
    plt.legend(loc='upper left')
    
    # Calculate and annotate correlation coefficient
    corr, p_val = df['age'].corr(df['burden'], method='spearman'), 0.0 # Placeholder for p-value annotation if needed
    # Using numpy for simple pearson for annotation or just the visual
    pearson_r = df['age'].corr(df['burden'])
    annotation = f"Spearman ρ = {df['age'].corr(df['burden'], method='spearman'):.3f}"
    plt.text(
        0.05, 0.95, annotation,
        transform=plt.gca().transAxes,
        fontsize=12,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )
    
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved linear fit plot to {output_path}")

def plot_threshold_sensitivity(df: pd.DataFrame, output_path: Path):
    """
    Plot Correlation Coefficient vs. Heteroplasmy Threshold.
    Shows robustness of the finding across different VAF cutoffs.
    """
    logger.info("Generating threshold sensitivity plot...")
    
    plt.figure(figsize=(10, 6))
    
    # Sort by threshold to ensure line connects correctly
    df_sorted = df.sort_values('threshold')
    
    plt.plot(
        df_sorted['threshold'], 
        df_sorted['correlation'], 
        marker='o', 
        linewidth=2.5, 
        markersize=8,
        color='#e63946',
        label='Spearman Correlation'
    )
    
    # Add a horizontal line at 0 for reference
    plt.axhline(0, color='gray', linestyle='--', linewidth=1, alpha=0.7)
    
    # Fill area if we have confidence intervals (optional, assuming simple line for now)
    # If p-values were available, we could shade non-significant regions, but keeping it clean.
    
    plt.title('Robustness of Correlation Across Heteroplasmy Thresholds', fontsize=16, fontweight='bold')
    plt.xlabel('Heteroplasmy Threshold (VAF %)', fontsize=14)
    plt.ylabel('Spearman Correlation Coefficient (ρ)', fontsize=14)
    plt.xticks(df_sorted['threshold']) # Show all tick marks
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved threshold sensitivity plot to {output_path}")

def main():
    """Main entry point to generate all final figures."""
    logger.info("Starting final figure generation...")
    
    # Define paths based on project structure
    # Assuming standard paths derived from T020 and T038
    processed_data_path = "code/data/processed/mito_aging_dataset.csv"
    sensitivity_data_path = "code/data/processed/sensitivity_analysis.csv"
    figures_dir = "paper/figures"
    
    output_dir = ensure_output_dir(figures_dir)
    
    # 1. Load Data
    try:
        df_main = load_processed_dataset(processed_data_path)
    except FileNotFoundError as e:
        logger.error(f"Cannot generate figures: {e}")
        sys.exit(1)
    
    try:
        df_sens = load_sensitivity_results(sensitivity_data_path)
    except FileNotFoundError as e:
        logger.error(f"Cannot generate figures: {e}")
        sys.exit(1)
    
    # 2. Generate Plots
    plot_linear_fit(df_main, output_dir / "linear_fit_burden_age.png")
    plot_threshold_sensitivity(df_sens, output_dir / "threshold_sensitivity.png")
    
    logger.info("All final figures generated successfully.")

if __name__ == "__main__":
    main()
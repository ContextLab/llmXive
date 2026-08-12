import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import numpy as np

# Ensure non-interactive backend for server environments
matplotlib.use('Agg')

logger = logging.getLogger(__name__)

# Constants
DPI = 300
PLOTS_DIR = Path("results/plots")

def _ensure_plots_dir():
    """Create the plots directory if it doesn't exist."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

def _load_filtered_data() -> pd.DataFrame:
    """
    Load the filtered dataset produced by T035.
    Expects results/filtered_data.csv to exist.
    """
    input_path = Path("results/filtered_data.csv")
    if not input_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {input_path}. "
            "Please ensure T035 (filter_utility_collapse) has been run successfully."
        )
    df = pd.read_csv(input_path)
    # Ensure numeric types for calculations
    numeric_cols = ['epsilon', 'alpha', 'global_accuracy', 'minority_accuracy', 'majority_accuracy']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def plot_accuracy_gap_vs_alpha(df: Optional[pd.DataFrame] = None):
    """
    Plot accuracy gap (Majority - Minority) vs Alpha.
    """
    if df is None:
        df = _load_filtered_data()

    _ensure_plots_dir()
    
    plt.figure(figsize=(10, 6))
    
    # Group by alpha to aggregate across epsilons/seeds if needed, 
    # or plot distinct points. We will plot distinct points colored by epsilon.
    # X-axis: Alpha
    # Y-axis: Gap (Majority - Minority)
    
    if 'alpha' not in df.columns or 'majority_accuracy' not in df.columns or 'minority_accuracy' not in df.columns:
        logger.error("Required columns (alpha, majority_accuracy, minority_accuracy) missing from data.")
        return

    gap = df['majority_accuracy'] - df['minority_accuracy']
    
    # Plot points, colored by epsilon
    scatter = plt.scatter(
        df['alpha'], gap, 
        c=df['epsilon'], 
        cmap='viridis', 
        alpha=0.7, 
        edgecolors='k', 
        s=100
    )
    
    plt.xlabel('Dirichlet Alpha (Heterogeneity)')
    plt.ylabel('Accuracy Gap (Majority - Minority)')
    plt.title('Accuracy Gap vs. Heterogeneity (Alpha)')
    plt.colorbar(scatter, label='Privacy Budget (Epsilon)')
    plt.grid(True, linestyle='--', alpha=0.6)
    
    output_path = PLOTS_DIR / "accuracy_gap_vs_alpha.png"
    plt.savefig(output_path, dpi=DPI, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved plot: {output_path}")

def plot_accuracy_vs_epsilon(df: Optional[pd.DataFrame] = None):
    """
    Plot Accuracy vs Epsilon for different Alpha values.
    """
    if df is None:
        df = _load_filtered_data()

    _ensure_plots_dir()

    plt.figure(figsize=(10, 6))

    if 'epsilon' not in df.columns or 'global_accuracy' not in df.columns or 'alpha' not in df.columns:
        logger.error("Required columns (epsilon, global_accuracy, alpha) missing from data.")
        return

    # Get unique alphas for legend
    unique_alphas = sorted(df['alpha'].dropna().unique())
    
    # If alpha is float, round for display or group
    # We will plot mean accuracy per epsilon for each alpha
    for alpha in unique_alphas:
        subset = df[df['alpha'] == alpha]
        # Group by epsilon and calculate mean accuracy
        grouped = subset.groupby('epsilon')['global_accuracy'].mean().reset_index()
        
        plt.plot(
            grouped['epsilon'], 
            grouped['global_accuracy'], 
            marker='o', 
            label=f'Alpha = {alpha}',
            linewidth=2
        )

    plt.xlabel('Privacy Budget (Epsilon)')
    plt.ylabel('Global Accuracy')
    plt.title('Global Accuracy vs. Privacy Budget (Epsilon)')
    plt.legend(title='Heterogeneity (Alpha)')
    plt.grid(True, linestyle='--', alpha=0.6)
    
    output_path = PLOTS_DIR / "accuracy_vs_epsilon.png"
    plt.savefig(output_path, dpi=DPI, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved plot: {output_path}")

def plot_minority_degradation_overlay(df: Optional[pd.DataFrame] = None):
    """
    Mandated by Constitution Principle VII:
    Generate an overlay plot showing minority-client degradation curves 
    against global accuracy curves.
    
    X-axis: Epsilon (Privacy Budget)
    Y-axis: Accuracy
    Lines: Global Accuracy (average) vs Minority Accuracy (average)
    """
    if df is None:
        df = _load_filtered_data()

    _ensure_plots_dir()

    plt.figure(figsize=(10, 6))

    if 'epsilon' not in df.columns or 'global_accuracy' not in df.columns or 'minority_accuracy' not in df.columns:
        logger.error("Required columns (epsilon, global_accuracy, minority_accuracy) missing from data.")
        return

    # Aggregate by epsilon to get mean curves
    global_means = df.groupby('epsilon')['global_accuracy'].mean().reset_index()
    minority_means = df.groupby('epsilon')['minority_accuracy'].mean().reset_index()

    # Plot Global Accuracy
    plt.plot(
        global_means['epsilon'], 
        global_means['global_accuracy'], 
        marker='s', 
        linewidth=3, 
        label='Global Accuracy',
        color='#1f77b4' # Blue
    )

    # Plot Minority Accuracy
    plt.plot(
        minority_means['epsilon'], 
        minority_means['minority_accuracy'], 
        marker='o', 
        linewidth=3, 
        label='Minority Client Accuracy',
        color='#d62728', # Red
        linestyle='--'
    )

    plt.xlabel('Privacy Budget (Epsilon)')
    plt.ylabel('Accuracy')
    plt.title('Minority Client Degradation vs. Global Accuracy\n(Overlay Plot)')
    plt.legend(loc='lower right')
    plt.grid(True, linestyle='--', alpha=0.6)
    
    # Ensure epsilon axis is sorted
    plt.xlim(left=min(df['epsilon'].min(), 0))
    
    output_path = PLOTS_DIR / "minority_degradation_overlay.png"
    plt.savefig(output_path, dpi=DPI, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved plot: {output_path}")

def generate_all_plots(df: Optional[pd.DataFrame] = None):
    """
    Generate all required plots:
    1. Accuracy Gap vs Alpha
    2. Accuracy vs Epsilon
    3. Minority Degradation Overlay
    """
    logger.info("Generating all analysis plots...")
    
    if df is None:
        df = _load_filtered_data()
    
    plot_accuracy_gap_vs_alpha(df)
    plot_accuracy_vs_epsilon(df)
    plot_minority_degradation_overlay(df)
    
    logger.info("All plots generated successfully.")

# Entry point for direct execution
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_all_plots()

import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import numpy as np

# Ensure we use a backend that supports saving files without display
matplotlib.use('Agg')

logger = logging.getLogger(__name__)

def load_filtered_data() -> pd.DataFrame:
    """
    Loads the filtered dataset produced by T035.
    Returns:
        pd.DataFrame: The filtered data containing global and minority accuracies.
    """
    path = Path("results/filtered_data.csv")
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}. "
                                "Ensure T035 has been executed successfully.")
    
    df = pd.read_csv(path)
    
    # Ensure numeric types for calculations
    numeric_cols = ['global_accuracy', 'minority_accuracy', 'alpha', 'epsilon']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def plot_accuracy_gap_vs_alpha(df: pd.DataFrame, output_path: Optional[Path] = None) -> None:
    """
    Plots the accuracy gap (Global - Minority) vs Alpha.
    """
    if output_path is None:
        output_path = Path("results/plots/accuracy_gap_vs_alpha.png")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Calculate gap if not present
    if 'accuracy_gap' not in df.columns:
        df['accuracy_gap'] = df['global_accuracy'] - df['minority_accuracy']
    
    # Group by alpha to calculate mean and std
    gap_stats = df.groupby('alpha')['accuracy_gap'].agg(['mean', 'std']).reset_index()
    
    plt.figure(figsize=(10, 6))
    plt.errorbar(gap_stats['alpha'], gap_stats['mean'], yerr=gap_stats['std'], 
                 fmt='-o', capsize=5, label='Accuracy Gap (Global - Minority)')
    
    plt.xlabel('Alpha (Heterogeneity)')
    plt.ylabel('Accuracy Gap')
    plt.title('Accuracy Gap vs Data Heterogeneity (Alpha)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved accuracy gap plot to {output_path}")

def plot_accuracy_vs_epsilon(df: pd.DataFrame, output_path: Optional[Path] = None) -> None:
    """
    Plots accuracy vs Epsilon for different Alpha values.
    """
    if output_path is None:
        output_path = Path("results/plots/accuracy_vs_epsilon.png")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    alphas = df['alpha'].unique()
    
    plt.figure(figsize=(10, 6))
    
    for alpha in sorted(alphas):
        subset = df[df['alpha'] == alpha]
        # Calculate mean accuracy per epsilon
        agg = subset.groupby('epsilon')['global_accuracy'].mean().reset_index()
        plt.plot(agg['epsilon'], agg['global_accuracy'], '-o', label=f'Alpha={alpha}')
    
    plt.xlabel('Privacy Budget (Epsilon)')
    plt.ylabel('Global Accuracy')
    plt.title('Global Accuracy vs Privacy Budget')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved accuracy vs epsilon plot to {output_path}")

def plot_minority_degradation_overlay(df: pd.DataFrame, output_path: Optional[Path] = None) -> None:
    """
    Generates an overlay plot showing minority-client degradation curves against 
    global accuracy curves as mandated by Constitution Principle VII.
    
    Y-axis: Accuracy
    X-axis: Epsilon (Privacy Budget)
    Lines: Global Accuracy and Minority Accuracy for each Alpha.
    """
    if output_path is None:
        output_path = Path("results/plots/minority_vs_global_overlay.png")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    alphas = sorted(df['alpha'].unique())
    colors = plt.cm.viridis(np.linspace(0, 1, len(alphas)))
    
    plt.figure(figsize=(12, 8))
    
    for i, alpha in enumerate(alphas):
        subset = df[df['alpha'] == alpha]
        
        # Aggregate Global Accuracy
        global_agg = subset.groupby('epsilon')['global_accuracy'].mean().reset_index()
        plt.plot(global_agg['epsilon'], global_agg['global_accuracy'], 
                 marker='o', linestyle='-', color=colors[i], 
                 label=f'Global (α={alpha})', linewidth=2)
        
        # Aggregate Minority Accuracy
        minority_agg = subset.groupby('epsilon')['minority_accuracy'].mean().reset_index()
        # Use dashed line for minority to distinguish
        plt.plot(minority_agg['epsilon'], minority_agg['minority_accuracy'], 
                 marker='s', linestyle='--', color=colors[i], 
                 label=f'Minority (α={alpha})', linewidth=2, alpha=0.8)
    
    plt.xlabel('Privacy Budget (Epsilon)')
    plt.ylabel('Accuracy')
    plt.title('Minority vs Global Accuracy Degradation Curves\nOverlay by Heterogeneity (Alpha)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(loc='lower left', bbox_to_anchor=(1, 0))
    plt.tight_layout()
    
    # Save with specific DPI requirement (300)
    plt.savefig(output_path, dpi=300, format='png')
    plt.close()
    logger.info(f"Saved minority vs global overlay plot to {output_path}")

def generate_all_plots() -> None:
    """
    Main entry point to generate all required plots for US3.
    Ensures directories exist and loads data from the filtered CSV.
    """
    plots_dir = Path("results/plots")
    plots_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        df = load_filtered_data()
        logger.info(f"Loaded {len(df)} rows from filtered data.")
        
        plot_accuracy_gap_vs_alpha(df, plots_dir / "accuracy_gap_vs_alpha.png")
        plot_accuracy_vs_epsilon(df, plots_dir / "accuracy_vs_epsilon.png")
        plot_minority_degradation_overlay(df, plots_dir / "minority_vs_global_overlay.png")
        
        logger.info("All plots generated successfully.")
    except FileNotFoundError as e:
        logger.error(str(e))
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_all_plots()

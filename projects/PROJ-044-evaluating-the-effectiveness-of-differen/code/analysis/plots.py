import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import numpy as np

# Ensure non-interactive backend for headless environments
matplotlib.use('Agg')

logger = logging.getLogger(__name__)

PLOTS_DIR = Path("results/plots")

def _ensure_plot_dir():
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

def _save_fig(fig: plt.Figure, filename: str, dpi: int = 300):
    """Save figure with high resolution."""
    filepath = PLOTS_DIR / filename
    fig.savefig(filepath, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved plot: {filepath}")

def load_filtered_data() -> pd.DataFrame:
    """
    Load the filtered dataset produced by T035.
    Expects results/filtered_data.csv to exist.
    """
    path = Path("results/filtered_data.csv")
    if not path.exists():
        raise FileNotFoundError(
            f"Required input file {path} not found. "
            "Ensure T035 (filter_utility_collapse) and T027a (filter_time_limited) have run."
        )
    df = pd.read_csv(path)
    # Ensure numeric types if necessary
    numeric_cols = ['global_accuracy', 'minority_accuracy', 'majority_accuracy', 'alpha', 'epsilon']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def plot_accuracy_gap_vs_alpha(df: Optional[pd.DataFrame] = None):
    """
    Plot accuracy gap (Majority - Minority) vs Alpha.
    """
    if df is None:
        df = load_filtered_data()

    _ensure_plot_dir()

    # Group by alpha and calculate mean gap
    df['accuracy_gap'] = df['majority_accuracy'] - df['minority_accuracy']
    gap_by_alpha = df.groupby('alpha')['accuracy_gap'].mean().reset_index()

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(gap_by_alpha['alpha'], gap_by_alpha['accuracy_gap'], marker='o', linestyle='-', color='red', label='Mean Accuracy Gap')
    ax.set_xlabel('Alpha (Heterogeneity)')
    ax.set_ylabel('Accuracy Gap (Majority - Minority)')
    ax.set_title('Accuracy Gap vs. Heterogeneity (Alpha)')
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend()

    _save_fig(fig, "accuracy_gap_vs_alpha.png")

def plot_accuracy_vs_epsilon(df: Optional[pd.DataFrame] = None):
    """
    Plot Global Accuracy vs. Epsilon for different Alpha values.
    """
    if df is None:
        df = load_filtered_data()

    _ensure_plot_dir()

    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot lines for each alpha
    alphas = sorted(df['alpha'].unique())
    colors = plt.cm.viridis(np.linspace(0, 1, len(alphas)))

    for alpha, color in zip(alphas, colors):
        subset = df[df['alpha'] == alpha]
        # Aggregate by epsilon
        agg = subset.groupby('epsilon')['global_accuracy'].mean().reset_index()
        ax.plot(agg['epsilon'], agg['global_accuracy'], marker='s', color=color,
                label=f'Alpha={alpha}', linewidth=2)

    ax.set_xlabel('Epsilon (Privacy Budget)')
    ax.set_ylabel('Global Accuracy')
    ax.set_title('Global Accuracy vs. Privacy Budget (Epsilon)')
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend(title='Alpha Value')

    _save_fig(fig, "accuracy_vs_epsilon.png")

def plot_minority_degradation_overlay(df: Optional[pd.DataFrame] = None):
    """
    Mandated by Constitution Principle VII:
    Generate an overlay plot showing minority-client degradation curves 
    against global accuracy curves.
    """
    if df is None:
        df = load_filtered_data()

    _ensure_plot_dir()

    fig, ax1 = plt.subplots(figsize=(12, 7))

    # Sort unique alphas for consistent coloring
    alphas = sorted(df['alpha'].unique())
    colors = plt.cm.plasma(np.linspace(0, 1, len(alphas)))

    # Plot Global Accuracy curves (Left Y-axis)
    for i, alpha in enumerate(alphas):
        subset = df[df['alpha'] == alpha]
        agg_global = subset.groupby('epsilon')['global_accuracy'].mean().reset_index()
        ax1.plot(agg_global['epsilon'], agg_global['global_accuracy'], 
                 marker='o', color=colors[i], linestyle='-', linewidth=2.5,
                 label=f'Global Acc (α={alpha})', zorder=3)

    ax1.set_xlabel('Epsilon (Privacy Budget)', fontsize=12)
    ax1.set_ylabel('Global Accuracy', color='blue', fontsize=12)
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.grid(True, which='both', linestyle='--', alpha=0.5, zorder=0)
    ax1.set_title('Global vs. Minority Accuracy Degradation under Differential Privacy', fontsize=14)

    # Create secondary y-axis for Minority Accuracy
    ax2 = ax1.twinx()
    ax2.set_ylabel('Minority Accuracy', color='red', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='red')

    # Plot Minority Accuracy curves (Right Y-axis) - Overlay
    for i, alpha in enumerate(alphas):
        subset = df[df['alpha'] == alpha]
        agg_minority = subset.groupby('epsilon')['minority_accuracy'].mean().reset_index()
        ax2.plot(agg_minority['epsilon'], agg_minority['minority_accuracy'], 
                 marker='s', color=colors[i], linestyle='--', linewidth=2.5,
                 label=f'Minority Acc (α={alpha})', zorder=3)

    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    # Sort legends by alpha for clarity
    combined_lines = lines1 + lines2
    combined_labels = labels1 + labels2
    
    # Sort by alpha value in label string
    def sort_key(label):
        try:
            return float(label.split('α=')[1].split(')')[0])
        except:
            return 999

    sorted_indices = sorted(range(len(combined_labels)), key=lambda i: sort_key(combined_labels[i]))
    
    ax1.legend([combined_lines[i] for i in sorted_indices], 
               [combined_labels[i] for i in sorted_indices], 
               loc='lower right', fontsize=10)

    # Ensure tight layout
    fig.tight_layout()

    _save_fig(fig, "minority_degradation_overlay.png")

def generate_all_plots():
    """
    Entry point to generate all required plots for T026.
    """
    logger.info("Generating all plots for T026...")
    try:
        df = load_filtered_data()
        plot_accuracy_gap_vs_alpha(df)
        plot_accuracy_vs_epsilon(df)
        plot_minority_degradation_overlay(df)
        logger.info("All plots generated successfully.")
    except FileNotFoundError as e:
        logger.error(f"Failed to generate plots: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during plot generation: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_all_plots()
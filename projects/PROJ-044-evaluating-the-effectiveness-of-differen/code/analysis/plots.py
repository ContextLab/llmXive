import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import numpy as np

# Configure matplotlib for high resolution and non-interactive backend if needed
matplotlib.use('Agg')  # Use non-interactive backend for script execution

logger = logging.getLogger(__name__)

def _ensure_output_dir(output_path: Path) -> None:
    """Ensure the directory for the output path exists."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

def plot_accuracy_gap_vs_alpha(
    df: pd.DataFrame,
    output_path: Path,
    dpi: int = 300
) -> None:
    """
    Plot the accuracy gap (Global - Minority) vs Alpha.
    
    Args:
        df: Filtered DataFrame containing accuracy metrics.
        output_path: Path to save the plot (PNG).
        dpi: Resolution in dots per inch.
    """
    _ensure_output_dir(output_path)
    
    # Group by alpha and calculate mean gap
    df['accuracy_gap'] = df['global_accuracy'] - df['minority_accuracy']
    
    gap_stats = df.groupby('alpha')['accuracy_gap'].mean().reset_index()
    
    plt.figure(figsize=(10, 6))
    plt.plot(gap_stats['alpha'], gap_stats['accuracy_gap'], marker='o', linestyle='-', color='blue')
    plt.xlabel('Dirichlet Alpha (α) - Heterogeneity Level')
    plt.ylabel('Accuracy Gap (Global - Minority)')
    plt.title('Accuracy Gap vs. Heterogeneity (α)')
    plt.grid(True, which='both', linestyle='--', alpha=0.7)
    plt.xticks(gap_stats['alpha'])
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi)
    plt.close()
    
    logger.info(f"Saved accuracy gap vs alpha plot to {output_path}")

def plot_accuracy_vs_epsilon(
    df: pd.DataFrame,
    output_path: Path,
    dpi: int = 300
) -> None:
    """
    Plot Global and Minority accuracy vs Epsilon (Privacy Budget).
    
    Args:
        df: Filtered DataFrame containing accuracy metrics.
        output_path: Path to save the plot (PNG).
        dpi: Resolution in dots per inch.
    """
    _ensure_output_dir(output_path)
    
    plt.figure(figsize=(10, 6))
    
    # Plot Global Accuracy
    global_stats = df.groupby('epsilon')['global_accuracy'].mean().reset_index()
    plt.plot(global_stats['epsilon'], global_stats['global_accuracy'], 
             marker='s', linestyle='-', label='Global Accuracy', color='green')
    
    # Plot Minority Accuracy
    minority_stats = df.groupby('epsilon')['minority_accuracy'].mean().reset_index()
    plt.plot(minority_stats['epsilon'], minority_stats['minority_accuracy'], 
             marker='^', linestyle='--', label='Minority Accuracy', color='red')
    
    plt.xlabel('Privacy Budget (ε)')
    plt.ylabel('Accuracy')
    plt.title('Accuracy vs. Privacy Budget (ε)')
    plt.legend()
    plt.grid(True, which='both', linestyle='--', alpha=0.7)
    plt.xticks(global_stats['epsilon'])
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi)
    plt.close()
    
    logger.info(f"Saved accuracy vs epsilon plot to {output_path}")

def plot_minority_degradation_overlay(
    df: pd.DataFrame,
    output_path: Path,
    dpi: int = 300
) -> None:
    """
    Generate an overlay plot showing minority-client degradation curves 
    against global accuracy curves, as mandated by Constitution Principle VII.
    
    This plot visualizes how minority accuracy degrades relative to global 
    accuracy as heterogeneity (alpha) increases.
    
    Args:
        df: Filtered DataFrame containing accuracy metrics.
        output_path: Path to save the plot (PNG).
        dpi: Resolution in dots per inch.
    """
    _ensure_output_dir(output_path)
    
    # Sort by alpha for consistent plotting
    df_sorted = df.sort_values('alpha')
    
    plt.figure(figsize=(12, 7))
    
    # Plot Global Accuracy (Secondary Y-axis or primary with distinct style)
    # We will use Alpha as the X-axis for heterogeneity analysis
    global_mean = df.groupby('alpha')['global_accuracy'].mean()
    minority_mean = df.groupby('alpha')['minority_accuracy'].mean()
    
    # Plot Global Accuracy
    plt.plot(global_mean.index, global_mean.values, 
             marker='o', linestyle='-', linewidth=2, 
             label='Global Accuracy', color='navy')
    
    # Plot Minority Accuracy
    plt.plot(minority_mean.index, minority_mean.values, 
             marker='s', linestyle='--', linewidth=2, 
             label='Minority Accuracy', color='crimson')
    
    # Calculate and plot degradation ratio (Minority / Global) on a secondary axis
    # This highlights the relative degradation
    ratio = minority_mean / global_mean
    
    ax2 = plt.gca().twinx()
    ax2.plot(ratio.index, ratio.values, 
             marker='^', linestyle=':', linewidth=2, 
             label='Minority/Global Ratio', color='darkorange')
    
    plt.xlabel('Dirichlet Alpha (α) - Heterogeneity Level')
    plt.ylabel('Accuracy', color='navy')
    ax2.set_ylabel('Minority / Global Ratio', color='darkorange')
    
    plt.title('Minority Client Degradation vs. Global Accuracy (Overlay)')
    
    # Combine legends from both axes
    lines1, labels1 = plt.gca().get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    plt.legend(lines1 + lines2, labels1 + labels2, loc='best')
    
    plt.grid(True, which='both', linestyle='--', alpha=0.5)
    plt.xticks(global_mean.index)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi)
    plt.close()
    
    logger.info(f"Saved minority degradation overlay plot to {output_path}")

def generate_all_plots(
    df: pd.DataFrame,
    output_dir: Path,
    dpi: int = 300
) -> List[Path]:
    """
    Generate all required plots for User Story 3 analysis.
    
    Args:
        df: Filtered DataFrame containing accuracy metrics.
        output_dir: Directory to save all plots.
        dpi: Resolution for plots.
        
    Returns:
        List of paths to generated plot files.
    """
    output_dir = Path(output_dir)
    generated_plots = []
    
    # 1. Accuracy Gap vs Alpha
    plot_gap_path = output_dir / "accuracy_gap_vs_alpha.png"
    plot_accuracy_gap_vs_alpha(df, plot_gap_path, dpi)
    generated_plots.append(plot_gap_path)
    
    # 2. Accuracy vs Epsilon
    plot_epsilon_path = output_dir / "accuracy_vs_epsilon.png"
    plot_accuracy_vs_epsilon(df, plot_epsilon_path, dpi)
    generated_plots.append(plot_epsilon_path)
    
    # 3. Minority Degradation Overlay (Constitution Principle VII)
    plot_overlay_path = output_dir / "minority_degradation_overlay.png"
    plot_minority_degradation_overlay(df, plot_overlay_path, dpi)
    generated_plots.append(plot_overlay_path)
    
    logger.info(f"Generated {len(generated_plots)} plots in {output_dir}")
    return generated_plots
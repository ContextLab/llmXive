"""
Plotting module for DP-FL analysis.

Generates:
1. Accuracy gap vs. α curves
2. Accuracy vs. ε curves
3. Overlay plot: Minority-client degradation vs. Global accuracy (Constitution Principle VII)
"""
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any

import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import numpy as np

# Ensure non-interactive backend for headless execution
matplotlib.use('Agg')

logger = logging.getLogger(__name__)


def _ensure_output_dir(output_path: Path) -> None:
    """Ensure the directory for the output file exists."""
    output_path.parent.mkdir(parents=True, exist_ok=True)


def plot_accuracy_gap_vs_alpha(
    df: pd.DataFrame,
    output_path: Path,
    epsilon_values: Optional[List[float]] = None
) -> None:
    """
    Plot accuracy gap (Global - Minority) vs. Alpha.
    
    Args:
        df: DataFrame containing 'alpha', 'epsilon', 'global_accuracy', 'minority_accuracy'.
        output_path: Path to save the plot.
        epsilon_values: Optional list of epsilon values to plot separately. If None, aggregates all.
    """
    _ensure_output_dir(output_path)
    
    plt.figure(figsize=(10, 6))
    
    if epsilon_values is None:
        # Aggregate by alpha, taking mean of gaps
        df_agg = df.groupby('alpha').agg({
            'global_accuracy': 'mean',
            'minority_accuracy': 'mean'
        }).reset_index()
        df_agg['gap'] = df_agg['global_accuracy'] - df_agg['minority_accuracy']
        
        plt.plot(df_agg['alpha'], df_agg['gap'], marker='o', label='Mean Gap (All ε)', linewidth=2)
        plt.xlabel('Alpha (Heterogeneity)')
        plt.ylabel('Accuracy Gap (Global - Minority)')
        plt.title('Accuracy Gap vs. Heterogeneity (α)')
    else:
        for eps in sorted(epsilon_values):
            subset = df[df['epsilon'] == eps]
            if subset.empty:
                continue
            subset_agg = subset.groupby('alpha').agg({
                'global_accuracy': 'mean',
                'minority_accuracy': 'mean'
            }).reset_index()
            subset_agg['gap'] = subset_agg['global_accuracy'] - subset_agg['minority_accuracy']
            
            plt.plot(subset_agg['alpha'], subset_agg['gap'], marker='o', label=f'ε={eps}', linewidth=2)
        
        plt.xlabel('Alpha (Heterogeneity)')
        plt.ylabel('Accuracy Gap (Global - Minority)')
        plt.title('Accuracy Gap vs. Heterogeneity (α) by Privacy Budget')
        plt.legend()

    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Saved accuracy gap vs alpha plot to {output_path}")


def plot_accuracy_vs_epsilon(
    df: pd.DataFrame,
    output_path: Path,
    alpha_values: Optional[List[float]] = None
) -> None:
    """
    Plot accuracy vs. Epsilon.
    
    Args:
        df: DataFrame containing 'alpha', 'epsilon', 'global_accuracy', 'minority_accuracy'.
        output_path: Path to save the plot.
        alpha_values: Optional list of alpha values to plot separately.
    """
    _ensure_output_dir(output_path)
    
    plt.figure(figsize=(10, 6))
    
    if alpha_values is None:
        # Aggregate by epsilon
        df_agg = df.groupby('epsilon').agg({
            'global_accuracy': 'mean',
            'minority_accuracy': 'mean'
        }).reset_index()
        
        plt.plot(df_agg['epsilon'], df_agg['global_accuracy'], marker='s', label='Global Accuracy', linewidth=2)
        plt.plot(df_agg['epsilon'], df_agg['minority_accuracy'], marker='d', label='Minority Accuracy', linewidth=2)
        
        plt.xlabel('Privacy Budget (ε)')
        plt.ylabel('Accuracy')
        plt.title('Accuracy vs. Privacy Budget')
    else:
        for alpha in sorted(alpha_values):
            subset = df[df['alpha'] == alpha]
            if subset.empty:
                continue
            subset_agg = subset.groupby('epsilon').agg({
                'global_accuracy': 'mean',
                'minority_accuracy': 'mean'
            }).reset_index()
            
            plt.plot(subset_agg['epsilon'], subset_agg['global_accuracy'], marker='s', label=f'Global (α={alpha})', linewidth=2)
            plt.plot(subset_agg['epsilon'], subset_agg['minority_accuracy'], marker='d', label=f'Minority (α={alpha})', linewidth=2, linestyle='--')
        
        plt.xlabel('Privacy Budget (ε)')
        plt.ylabel('Accuracy')
        plt.title('Accuracy vs. Privacy Budget by Heterogeneity')
        plt.legend()

    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Saved accuracy vs epsilon plot to {output_path}")


def plot_minority_degradation_overlay(
    df: pd.DataFrame,
    output_path: Path,
    alpha: Optional[float] = None,
    epsilon: Optional[float] = None
) -> None:
    """
    Generate an overlay plot showing minority-client degradation curves against 
    global accuracy curves. This addresses Constitution Principle VII.
    
    If alpha is specified, plots Global vs Minority for that alpha across epsilon.
    If epsilon is specified, plots Global vs Minority for that epsilon across alpha.
    If neither, plots aggregated trends.
    
    Args:
        df: DataFrame with 'alpha', 'epsilon', 'global_accuracy', 'minority_accuracy'.
        output_path: Path to save the plot.
        alpha: Optional specific alpha to focus on.
        epsilon: Optional specific epsilon to focus on.
    """
    _ensure_output_dir(output_path)
    
    plt.figure(figsize=(12, 7))
    
    if alpha is not None and epsilon is not None:
        # Single point - not useful for a curve, warn and return
        logger.warning("Both alpha and epsilon specified. Need a sweep to plot a curve.")
        return
        
    if alpha is not None:
        # Sweep over epsilon for fixed alpha
        subset = df[df['alpha'] == alpha]
        if subset.empty:
            logger.warning(f"No data found for alpha={alpha}")
            return
        
        agg = subset.groupby('epsilon').agg({
            'global_accuracy': 'mean',
            'minority_accuracy': 'mean'
        }).reset_index()
        
        plt.plot(agg['epsilon'], agg['global_accuracy'], marker='o', label='Global Accuracy', linewidth=2.5, color='#1f77b4')
        plt.plot(agg['epsilon'], agg['minority_accuracy'], marker='s', label='Minority Accuracy', linewidth=2.5, color='#d62728')
        
        plt.xlabel('Privacy Budget (ε)', fontsize=12)
        plt.ylabel('Accuracy', fontsize=12)
        plt.title(f'Accuracy Degradation: Global vs Minority (α={alpha})', fontsize=14)
        plt.legend(fontsize=11)
        
    elif epsilon is not None:
        # Sweep over alpha for fixed epsilon
        subset = df[df['epsilon'] == epsilon]
        if subset.empty:
            logger.warning(f"No data found for epsilon={epsilon}")
            return
        
        agg = subset.groupby('alpha').agg({
            'global_accuracy': 'mean',
            'minority_accuracy': 'mean'
        }).reset_index()
        
        plt.plot(agg['alpha'], agg['global_accuracy'], marker='o', label='Global Accuracy', linewidth=2.5, color='#1f77b4')
        plt.plot(agg['alpha'], agg['minority_accuracy'], marker='s', label='Minority Accuracy', linewidth=2.5, color='#d62728')
        
        plt.xlabel('Heterogeneity (α)', fontsize=12)
        plt.ylabel('Accuracy', fontsize=12)
        plt.title(f'Accuracy Degradation: Global vs Minority (ε={epsilon})', fontsize=14)
        plt.legend(fontsize=11)
        
    else:
        # Aggregate over all, or group by the variable with more variance
        # Default: Aggregate by epsilon
        agg = df.groupby('epsilon').agg({
            'global_accuracy': 'mean',
            'minority_accuracy': 'mean'
        }).reset_index()
        
        plt.plot(agg['epsilon'], agg['global_accuracy'], marker='o', label='Global Accuracy (Mean)', linewidth=2.5, color='#1f77b4')
        plt.plot(agg['epsilon'], agg['minority_accuracy'], marker='s', label='Minority Accuracy (Mean)', linewidth=2.5, color='#d62728')
        
        plt.xlabel('Privacy Budget (ε)', fontsize=12)
        plt.ylabel('Accuracy', fontsize=12)
        plt.title('Accuracy Degradation: Global vs Minority (Aggregated)', fontsize=14)
        plt.legend(fontsize=11)

    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved minority degradation overlay plot to {output_path}")


def generate_all_plots(
    input_csv_path: Path,
    output_dir: Path,
    alpha_values: Optional[List[float]] = None,
    epsilon_values: Optional[List[float]] = None
) -> Dict[str, Path]:
    """
    Main entry point to generate all required plots from the results CSV.
    
    Args:
        input_csv_path: Path to the results CSV (e.g., results/summary.csv).
        output_dir: Directory to save generated plots.
        alpha_values: Optional list of specific alphas to focus on.
        epsilon_values: Optional list of specific epsilons to focus on.
        
    Returns:
        Dictionary mapping plot names to their file paths.
    """
    logger.info(f"Loading metrics from {input_csv_path}")
    if not input_csv_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv_path}")
        
    df = pd.read_csv(input_csv_path)
    
    # Ensure required columns exist
    required_cols = ['alpha', 'epsilon', 'global_accuracy', 'minority_accuracy']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in CSV: {missing}")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_files = {}
    
    # 1. Accuracy Gap vs Alpha
    gap_path = output_dir / "accuracy_gap_vs_alpha.png"
    plot_accuracy_gap_vs_alpha(df, gap_path, epsilon_values)
    generated_files['gap_vs_alpha'] = gap_path
    
    # 2. Accuracy vs Epsilon
    acc_eps_path = output_dir / "accuracy_vs_epsilon.png"
    plot_accuracy_vs_epsilon(df, acc_eps_path, alpha_values)
    generated_files['acc_vs_epsilon'] = acc_eps_path
    
    # 3. Overlay Plot (Constitution Principle VII)
    # Generate for each alpha if available, or just one aggregated
    if alpha_values:
        for a in alpha_values:
            overlay_path = output_dir / f"minority_degradation_alpha_{a}.png"
            plot_minority_degradation_overlay(df, overlay_path, alpha=a)
            generated_files[f'overlay_alpha_{a}'] = overlay_path
    else:
        # Default: Aggregate
        overlay_path = output_dir / "minority_degradation_overlay.png"
        plot_minority_degradation_overlay(df, overlay_path)
        generated_files['overlay_aggregated'] = overlay_path
        
    logger.info(f"Successfully generated {len(generated_files)} plots in {output_dir}")
    return generated_files
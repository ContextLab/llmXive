import os
import logging
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from utils import setup_logger, get_seeded_rng
from analysis import load_metrics_and_behavioral_data, run_permutation_test, calculate_permutation_p_value, compute_spearman

def generate_permutation_report(
    output_path: str,
    n_permutations: int = 1000,
    seed: int = 42,
    metric_name: str = "transition_count",
    behavior_name: str = "DSST_score"
) -> None:
    """
    Generate a visual report (PDF/PNG) of the permutation test.
    Visualizes the null distribution histogram and highlights the observed statistic.
    Satisfies SC-005.
    
    Args:
        output_path: Path to save the report (e.g., 'data/results/permutation_report.pdf')
        n_permutations: Number of permutations to run
        seed: Random seed for reproducibility
        metric_name: Name of the metric column
        behavior_name: Name of the behavior column
    """
    logger = setup_logger("analysis")
    logger.info(f"Generating permutation test report for {metric_name} vs {behavior_name}")
    
    # Load real data
    metrics_df, behavioral_df = load_metrics_and_behavioral_data()
    
    if metrics_df is None or behavioral_df is None:
        logger.error("Failed to load data for permutation report. Cannot generate plot.")
        raise FileNotFoundError("Required data files not found. Ensure T020 and T025b have run.")
    
    # Merge data
    merged_df = pd.merge(metrics_df, behavioral_df, on='subject_id', how='inner')
    
    if len(merged_df) < 2:
        logger.error("Insufficient subjects for correlation analysis after merge.")
        raise ValueError("Not enough valid subjects to compute correlation.")
    
    x = merged_df[metric_name].values
    y = merged_df[behavior_name].values
    
    # Compute observed statistic
    obs_coef, obs_pval = compute_spearman(x, y)
    logger.info(f"Observed Spearman coefficient: {obs_coef:.4f}, p-value: {obs_pval:.4f}")
    
    # Run permutation test
    null_dist = run_permutation_test(x, y, n_permutations=n_permutations, seed=seed)
    perm_pval = calculate_permutation_p_value(obs_coef, null_dist)
    logger.info(f"Permutation p-value: {perm_pval:.4f}")
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot histogram of null distribution
    ax.hist(null_dist, bins=30, density=True, alpha=0.6, color='skyblue', 
            edgecolor='black', label='Null Distribution')
    
    # Plot observed statistic as a vertical line
    ax.axvline(obs_coef, color='red', linestyle='--', linewidth=2, 
               label=f'Observed: {obs_coef:.3f}')
    
    # Shade the tails (extreme values)
    # Calculate the range for the tail shading based on observed value
    if obs_coef >= 0:
        ax.axhline(0, color='black', linewidth=0.5)
        # Shade right tail
        x_vals = np.linspace(obs_coef, np.max(null_dist), 100)
        # Simple approximation for shading: just mark the region
        ax.axvspan(obs_coef, np.max(null_dist), color='red', alpha=0.1)
    else:
        ax.axhline(0, color='black', linewidth=0.5)
        # Shade left tail
        ax.axvspan(np.min(null_dist), obs_coef, color='red', alpha=0.1)
    
    ax.set_xlabel('Correlation Coefficient (Spearman r)', fontsize=12)
    ax.set_ylabel('Density', fontsize=12)
    ax.set_title(f'Permutation Test: {metric_name} vs {behavior_name}\n'
                 f'Observed r = {obs_coef:.3f}, Perm p = {perm_pval:.3f}', fontsize=14)
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save as PDF and PNG
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    logger.info(f"Report saved to {output_path}")
    
    # Also save a PNG version if PDF was requested, or vice versa
    if output_path.endswith('.pdf'):
        png_path = str(output_path).replace('.pdf', '.png')
        plt.savefig(png_path, dpi=300)
        logger.info(f"PNG version saved to {png_path}")
    elif output_path.endswith('.png'):
        pdf_path = str(output_path).replace('.png', '.pdf')
        plt.savefig(pdf_path, dpi=300)
        logger.info(f"PDF version saved to {pdf_path}")
        
    plt.close(fig)

def main():
    """Entry point for generating the permutation test report."""
    logger = setup_logger("analysis")
    
    # Default output path as per task requirements
    output_path = "data/results/permutation_test_report.pdf"
    
    try:
        generate_permutation_report(output_path)
        logger.info("Permutation report generation completed successfully.")
    except Exception as e:
        logger.error(f"Failed to generate permutation report: {e}")
        raise

if __name__ == "__main__":
    main()
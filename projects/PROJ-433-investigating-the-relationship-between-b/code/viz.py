import os
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np
import matplotlib.pyplot as plt

from utils import setup_logger, get_seeded_rng
from analysis import load_metrics_and_behavioral_data, compute_spearman, apply_bonferroni, compute_cohens_r, handle_extreme_p_values

def generate_scatter_plot(
    x_data: np.ndarray,
    y_data: np.ndarray,
    x_label: str,
    y_label: str,
    title: str,
    output_path: Path,
    coef: float,
    p_val: float,
    adj_p: float,
    effect_size: float,
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Generate a scatter plot with trendline, confidence interval, and statistical annotations.
    
    Args:
        x_data: Independent variable data (e.g., transition_count)
        y_data: Dependent variable data (e.g., DSST_score)
        x_label: Label for x-axis
        y_label: Label for y-axis
        title: Plot title
        output_path: Path where the PNG file will be saved
        coef: Spearman correlation coefficient
        p_val: Raw p-value
        adj_p: Bonferroni-adjusted p-value
        effect_size: Cohen's r effect size
        logger: Optional logger instance
    """
    if logger is None:
        logger = setup_logger("viz")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Set up the figure
    fig, ax = plt.subplots(figsize=(10, 7))
    
    # Scatter plot
    ax.scatter(x_data, y_data, alpha=0.6, edgecolors='w', linewidth=0.5, s=80)
    
    # Calculate and plot trendline
    # Using linear regression for the trendline visualization
    slope, intercept = np.polyfit(x_data, y_data, 1)
    x_line = np.linspace(x_data.min(), x_data.max(), 100)
    y_line = slope * x_line + intercept
    ax.plot(x_line, y_line, 'r-', linewidth=2, label=f'Trendline (r={coef:.3f})')
    
    # Calculate confidence interval for the trendline
    # Using bootstrap for confidence interval
    rng = get_seeded_rng(42)
    n_boot = 1000
    boot_slopes = []
    boot_intercepts = []
    
    for _ in range(n_boot):
        indices = rng.choice(len(x_data), size=len(x_data), replace=True)
        x_boot = x_data[indices]
        y_boot = y_data[indices]
        b_slope, b_intercept = np.polyfit(x_boot, y_boot, 1)
        boot_slopes.append(b_slope)
        boot_intercepts.append(b_intercept)
    
    # Calculate confidence bands
    y_lower = slope * x_line + intercept + np.percentile(
        [bs * x_line + bi - y_line for bs, bi in zip(boot_slopes, boot_intercepts)], 
        2.5, axis=0
    )
    y_upper = slope * x_line + intercept + np.percentile(
        [bs * x_line + bi - y_line for bs, bi in zip(boot_slopes, boot_intercepts)], 
        97.5, axis=0
    )
    
    ax.fill_between(x_line, y_lower, y_upper, color='red', alpha=0.2, label='95% CI')
    
    # Labels and title
    ax.set_xlabel(x_label, fontsize=12)
    ax.set_ylabel(y_label, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Statistical annotations
    annotation_text = (
        f"ρ = {coef:.3f}\n"
        f"p = {p_val:.4f}\n"
        f"adj. p = {adj_p:.4f}\n"
        f"r = {effect_size:.3f}"
    )
    
    # Position annotation in the upper right corner
    ax.text(
        0.98, 0.98, annotation_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment='top',
        horizontalalignment='right',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )
    
    # Adjust layout and save
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    logger.info(f"Scatter plot saved to {output_path}")

def main():
    """
    Main function to generate scatter plots for all metric-behavior pairs.
    Loads aggregated statistics and generates corresponding plots.
    """
    logger = setup_logger("viz")
    logger.info("Starting scatter plot generation")
    
    # Load aggregated statistics from analysis
    # Expected file: data/analysis_results.tsv
    stats_path = Path("data/analysis_results.tsv")
    if not stats_path.exists():
        logger.error(f"Statistics file not found: {stats_path}. Run analysis.py first.")
        return
    
    # Load metrics and behavioral data to get actual values for plotting
    # This function should return subject-level data for plotting
    try:
        # Assuming load_metrics_and_behavioral_data returns a list of dicts with subject data
        # or we need to load from the metrics JSON files and behavioral data directly
        # For this implementation, we'll load the raw data needed for plotting
        data = load_metrics_and_behavioral_data()
        
        if not data:
            logger.warning("No data available for plotting")
            return
        
        # Extract arrays for plotting (assuming single metric-behavior pair for now)
        # In a more complex scenario, we'd iterate over multiple pairs
        x_data = np.array([d['transition_count'] for d in data if d['transition_count'] is not None])
        y_data = np.array([d['DSST_score'] for d in data if d['DSST_score'] is not None])
        
        # Filter to matching subjects
        min_len = min(len(x_data), len(y_data))
        x_data = x_data[:min_len]
        y_data = y_data[:min_len]
        
        if len(x_data) == 0:
            logger.warning("No valid data points for plotting")
            return
        
        # Compute statistics for annotation
        coef, p_val = compute_spearman(x_data, y_data)
        adj_p = apply_bonferroni(p_val, 1)  # Assuming 1 comparison for now
        effect_size = compute_cohens_r(coef)
        adj_p = handle_extreme_p_values(adj_p)
        
        # Define output path
        output_dir = Path("data/results")
        output_path = output_dir / "plot_transition_count_DSST_score.png"
        
        # Generate plot
        generate_scatter_plot(
            x_data=x_data,
            y_data=y_data,
            x_label="Network Reconfigurability (Transition Count)",
            y_label="DSST Score (Subjective Time Perception)",
            title="Relationship between Brain Network Dynamics and Subjective Time",
            output_path=output_path,
            coef=coef,
            p_val=p_val,
            adj_p=adj_p,
            effect_size=effect_size,
            logger=logger
        )
        
        logger.info("Scatter plot generation completed successfully")
        
    except Exception as e:
        logger.error(f"Error generating scatter plot: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
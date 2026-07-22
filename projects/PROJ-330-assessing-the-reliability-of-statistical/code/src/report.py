"""
Reporting module for the reliability assessment pipeline.

This module handles the visualization of analysis results, specifically
generating Bland-Altman plots to compare parametric vs. empirical p-values
derived from the stratified block permutation null modeling.
"""

import os
import logging
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Union

# Ensure non-interactive backend for headless execution
matplotlib.use('Agg')

from src.config import ensure_directories, PROJECT_ROOT
from src.metrics import generate_bland_altman_plot

logger = logging.getLogger(__name__)

# Output directory for reports and figures
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

def generate_bland_altman_report(
    parametric_pvalues: Union[pd.Series, np.ndarray, list],
    empirical_pvalues: Union[pd.Series, np.ndarray, list],
    output_filename: str = "bland_altman_pvalues.png",
    title: Optional[str] = None
) -> Path:
    """
    Generate a Bland-Altman plot comparing parametric and empirical p-values
    and save it to the artifacts directory.
    
    This visualization is critical for User Story 2 to assess the reliability
    of the Fixed-Dispersion Wald Perturbation strategy against the parametric
    null model.
    
    Args:
        parametric_pvalues: Array-like of parametric p-values (from DESeq2/edgeR).
        empirical_pvalues: Array-like of empirical p-values (from permutation).
        output_filename: Name of the output file (saved in artifacts/).
        title: Optional title for the plot. Defaults to 'Bland-Altman: Parametric vs Empirical P-values'.
        
    Returns:
        Path: The absolute path to the saved figure file.
        
    Raises:
        ValueError: If input arrays are empty or have mismatched lengths.
        FileNotFoundError: If required data files are missing (handled by caller).
    """
    # Convert inputs to numpy arrays for calculation
    p_param = np.asarray(parametric_pvalues, dtype=float)
    p_emp = np.asarray(empirical_pvalues, dtype=float)
    
    if len(p_param) == 0 or len(p_emp) == 0:
        raise ValueError("Input p-value arrays cannot be empty.")
        
    if len(p_param) != len(p_emp):
        raise ValueError(
            f"Input arrays must have the same length. "
            f"Got parametric={len(p_param)}, empirical={len(p_emp)}."
        )
    
    # Filter out NaNs and Infs which can occur with extreme p-values
    valid_mask = ~(np.isnan(p_param) | np.isnan(p_emp) | 
                   np.isinf(p_param) | np.isinf(p_emp))
    p_param = p_param[valid_mask]
    p_emp = p_emp[valid_mask]
    
    if len(p_param) == 0:
        raise ValueError("No valid p-value pairs found after filtering NaN/Inf.")
    
    # Use the metrics module to calculate the Bland-Altman statistics
    # This function returns (mean_diff, std_diff, loa_lower, loa_upper)
    # and we rely on it for the statistical basis, then plot manually for control
    mean_diff, std_diff, loa_lower, loa_upper = generate_bland_altman_plot(
        p_param, p_emp, return_stats_only=True
    )
    
    # Calculate differences and averages
    # Bland-Altman typically plots (Method1 - Method2) vs Average(Method1, Method2)
    # Here: Difference = Parametric - Empirical
    diff = p_param - p_emp
    avg = (p_param + p_emp) / 2.0
    
    # Setup the figure
    ensure_directories()
    output_path = ARTIFACTS_DIR / output_filename
    
    plt.figure(figsize=(10, 7))
    
    # Scatter plot of differences vs averages
    plt.scatter(avg, diff, alpha=0.5, s=15, c='steelblue', edgecolors='w', linewidth=0.5)
    
    # Mean difference line
    plt.axhline(mean_diff, color='darkred', linestyle='--', linewidth=2, label=f'Mean Diff: {mean_diff:.4f}')
    
    # Limits of Agreement (LoA) lines
    plt.axhline(loa_lower, color='darkgreen', linestyle=':', linewidth=1.5, label=f'LoA Lower: {loa_lower:.4f}')
    plt.axhline(loa_upper, color='darkgreen', linestyle=':', linewidth=1.5, label=f'LoA Upper: {loa_upper:.4f}')
    
    # Zero line for reference (perfect agreement)
    plt.axhline(0, color='gray', linestyle='-', linewidth=1, alpha=0.7)
    
    # Labels and Title
    xlabel = "Average of Parametric and Empirical P-values"
    ylabel = "Difference (Parametric - Empirical)"
    plot_title = title if title else "Bland-Altman Plot: Parametric vs. Empirical P-values"
    
    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.title(plot_title, fontsize=14)
    
    # Add grid
    plt.grid(True, which='both', linestyle='--', alpha=0.6)
    
    # Legend
    plt.legend(loc='best', fontsize=10)
    
    # Adjust layout to prevent clipping
    plt.tight_layout()
    
    # Save the figure
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Bland-Altman plot saved to: {output_path}")
    
    return output_path

def generate_stability_report(
    stability_metrics: Dict,
    output_filename: str = "stability_summary.txt"
) -> Path:
    """
    Generate a text summary report of stability metrics.
    
    Args:
        stability_metrics: Dictionary containing stability correlation metrics.
        output_filename: Name of the output file.
        
    Returns:
        Path: The absolute path to the saved report file.
    """
    ensure_directories()
    output_path = ARTIFACTS_DIR / output_filename
    
    with open(output_path, 'w') as f:
        f.write("Stability Analysis Summary Report\n")
        f.write("=" * 40 + "\n\n")
        
        for key, value in stability_metrics.items():
            if isinstance(value, float):
                f.write(f"{key}: {value:.6f}\n")
            else:
                f.write(f"{key}: {value}\n")
        
        f.write("\n" + "=" * 40 + "\n")
        f.write("Report generated by code/src/report.py\n")
    
    logger.info(f"Stability summary report saved to: {output_path}")
    return output_path

def main():
    """
    Main entry point for the report module.
    
    This function is intended to be called by the main orchestration script
    to generate visualizations after the permutation analysis is complete.
    
    It expects to find the necessary data files in the data/ directory
    or receives data directly from the metrics module.
    """
    logger.info("Report module main() called.")
    # This is typically called by main.py after T024/T025 have run
    # Example usage:
    # parametric = pd.read_csv('data/parametric_pvalues.csv')['pvalue']
    # empirical = pd.read_csv('data/empirical_pvalues.csv')['pvalue']
    # generate_bland_altman_report(parametric, empirical)
    
    logger.info("Report generation logic ready.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

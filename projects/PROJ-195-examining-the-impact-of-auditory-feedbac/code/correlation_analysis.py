import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

from utils import setup_logging

def load_roi_betas(betas_path: Path) -> Dict[str, float]:
    """
    Load auditory cortex beta values from T028 output.
    Expects a CSV with columns: 'subject_id', 'beta_value'.
    """
    if not betas_path.exists():
        raise FileNotFoundError(f"ROI betas file not found: {betas_path}")
    
    df = pd.read_csv(betas_path)
    if 'subject_id' not in df.columns or 'beta_value' not in df.columns:
        raise ValueError(f"Invalid CSV schema in {betas_path}. Expected 'subject_id' and 'beta_value' columns.")
    
    return dict(zip(df['subject_id'].astype(str), df['beta_value'].astype(float)))

def load_learning_rate_slopes(slopes_path: Path) -> Dict[str, float]:
    """
    Load learning rate slopes from T032 output.
    Expects a CSV with columns: 'subject_id', 'slope'.
    """
    if not slopes_path.exists():
        raise FileNotFoundError(f"Learning rate slopes file not found: {slopes_path}")
    
    df = pd.read_csv(slopes_path)
    if 'subject_id' not in df.columns or 'slope' not in df.columns:
        raise ValueError(f"Invalid CSV schema in {slopes_path}. Expected 'subject_id' and 'slope' columns.")
    
    return dict(zip(df['subject_id'].astype(str), df['slope'].astype(float)))

def calculate_pearson_correlation(betas: Dict[str, float], slopes: Dict[str, float]) -> Tuple[float, float, List[str]]:
    """
    Calculate Pearson correlation between auditory cortex activation (betas)
    and learning rate proxy (slopes).
    
    Returns:
        r: Pearson correlation coefficient
        p_value: Two-tailed p-value
        common_subjects: List of subject IDs found in both datasets
    """
    # Find common subjects
    common_subjects = sorted(list(set(betas.keys()) & set(slopes.keys())))
    
    if len(common_subjects) < 3:
        raise ValueError(
            f"Insufficient common subjects for correlation analysis. "
            f"Found {len(common_subjects)} common subjects. Need at least 3."
        )
    
    # Extract aligned arrays
    beta_values = np.array([betas[s] for s in common_subjects])
    slope_values = np.array([slopes[s] for s in common_subjects])
    
    # Calculate Pearson correlation
    r, p_value = stats.pearsonr(beta_values, slope_values)
    
    logging.info(f"Pearson correlation calculated: r={r:.4f}, p={p_value:.4f} (n={len(common_subjects)})")
    
    return r, p_value, common_subjects

def generate_scatter_plot(
    betas: Dict[str, float], 
    slopes: Dict[str, float], 
    output_path: Path, 
    r: float, 
    p_value: float
) -> None:
    """
    Generate a scatter plot of Auditory Cortex Activation vs. Learning Rate Slope.
    Saves the plot to output_path.
    """
    common_subjects = sorted(list(set(betas.keys()) & set(slopes.keys())))
    
    beta_values = np.array([betas[s] for s in common_subjects])
    slope_values = np.array([slopes[s] for s in common_subjects])
    
    plt.figure(figsize=(10, 8))
    
    # Scatter plot with regression line
    sns.regplot(x=beta_values, y=slope_values, scatter_kws={'s': 80, 'alpha': 0.7}, line_kws={'color': 'red'})
    
    plt.title(f'Auditory Cortex Activation vs. Learning Rate Slope\nPearson r = {r:.3f}, p = {p_value:.3f}', fontsize=14)
    plt.xlabel('Auditory Cortex Beta Value (Mean Activation)', fontsize=12)
    plt.ylabel('Learning Rate Slope (ms/trial)', fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logging.info(f"Scatter plot saved to {output_path}")

def main():
    """
    Main entry point for T033: Calculate Pearson correlation between
    auditory cortex activation and learning rate proxy.
    """
    logger = setup_logging("correlation_analysis", Path("data/processed/correlation_analysis.log"))
    logging.info("Starting T033: Pearson Correlation Analysis")
    
    # Define paths based on project structure
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data" / "processed"
    
    roi_betas_path = data_dir / "roi_betas.csv"
    learning_rate_slopes_path = data_dir / "learning_rate_slopes.csv"
    output_csv_path = data_dir / "correlation_results.csv"
    output_plot_path = project_root / "figures" / "correlation_scatter.png"
    
    # Load data
    try:
        logging.info(f"Loading ROI betas from {roi_betas_path}")
        betas = load_roi_betas(roi_betas_path)
        logging.info(f"Loaded {len(betas)} beta values")
        
        logging.info(f"Loading learning rate slopes from {learning_rate_slopes_path}")
        slopes = load_learning_rate_slopes(learning_rate_slopes_path)
        logging.info(f"Loaded {len(slopes)} slope values")
    except FileNotFoundError as e:
        logging.error(str(e))
        sys.exit(1)
    
    # Calculate correlation
    try:
        r, p_value, common_subjects = calculate_pearson_correlation(betas, slopes)
    except ValueError as e:
        logging.error(str(e))
        sys.exit(1)
    
    # Generate plot
    generate_scatter_plot(betas, slopes, output_plot_path, r, p_value)
    
    # Save results to CSV
    results_df = pd.DataFrame({
        'metric': ['pearson_r', 'p_value', 'n_subjects'],
        'value': [r, p_value, len(common_subjects)]
    })
    results_df.to_csv(output_csv_path, index=False)
    
    logging.info(f"Correlation results saved to {output_csv_path}")
    logging.info(f"Results: r={r:.4f}, p={p_value:.4f}, n={len(common_subjects)}")
    
    logging.info("T033 completed successfully")

if __name__ == "__main__":
    main()

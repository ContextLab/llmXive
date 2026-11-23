"""
Visualization module for generating plots and sensitivity reports.
Implements T028, T029, T030a, T030b.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Import from local modules
from config import get_path
from utils.logging import get_logger, log_exception

logger = get_logger("visualize")

def load_main_effects() -> pd.DataFrame:
    """Load main effects results."""
    path = get_path("results_main_effects")
    if not path.exists():
        raise FileNotFoundError(f"Main effects file not found: {path}")
    return pd.read_parquet(path)

def load_interaction_effects() -> pd.DataFrame:
    """Load interaction effects results."""
    path = get_path("results_interaction_effects")
    if not path.exists():
        raise FileNotFoundError(f"Interaction effects file not found: {path}")
    return pd.read_parquet(path)

def generate_manhattan_plot(df: pd.DataFrame, output_path: Path):
    """
    Generate a Manhattan-style plot for taxon-cognitive associations.
    T028
    """
    logger.info(f"Generating Manhattan plot: {output_path}")
    
    # Ensure columns exist
    if 'taxon' not in df.columns or 'adj_p' not in df.columns or 'beta' not in df.columns:
        raise ValueError("DataFrame must contain 'taxon', 'adj_p', and 'beta' columns")

    # Prepare data
    df_plot = df.copy()
    df_plot['neg_log_p'] = -np.log10(df_plot['adj_p'].replace(0, 1e-300)) # Avoid log(0)
    
    # Sort by chromosome/position if available, or just by index
    # For microbiome, we might not have chromosomes, so we order by taxon name or index
    df_plot = df_plot.sort_values('neg_log_p', ascending=False)
    df_plot['position'] = range(len(df_plot))

    # Plot
    plt.figure(figsize=(14, 7))
    sns.scatterplot(
        x='position',
        y='neg_log_p',
        hue='beta',
        data=df_plot,
        palette='coolwarm',
        alpha=0.7,
        edgecolor='k'
    )
    
    # Add threshold line
    plt.axhline(y=-np.log10(0.05), color='r', linestyle='--', label='p < 0.05')
    
    plt.title('Manhattan Plot: Taxon-Cognitive Associations')
    plt.xlabel('Taxon Index')
    plt.ylabel('-log10(Adjusted P-value)')
    plt.legend()
    plt.tight_layout()
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    
    logger.info(f"Manhattan plot saved to {output_path}")

def generate_threshold_sweep_report(df: pd.DataFrame, output_path: Path):
    """
    Generate threshold sweep sensitivity analysis.
    T029
    """
    logger.info(f"Generating threshold sweep report: {output_path}")
    
    thresholds = [0.001, 0.01, 0.05, 0.1, 0.2]
    report = {}
    
    for thresh in thresholds:
        count = (df['adj_p'] < thresh).sum()
        report[str(thresh)] = int(count)
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Threshold sweep report saved to {output_path}")

def generate_interaction_comparison_report(interaction_df: pd.DataFrame, main_df: pd.DataFrame, output_path: Path):
    """
    Compare interaction significance to primary effects.
    T030a, T030b
    """
    logger.info(f"Generating interaction comparison report: {output_path}")
    
    # Merge on taxon if possible, or just compare counts
    # Assuming 'taxon' column exists in both
    common_taxa = set(interaction_df['taxon']).intersection(set(main_df['taxon']))
    
    interaction_sig = interaction_df[interaction_df['adj_p'] < 0.05]['taxon'].tolist()
    main_sig = main_df[main_df['adj_p'] < 0.05]['taxon'].tolist()
    
    report = {
        "total_taxa_analyzed": len(common_taxa),
        "interaction_significant_count": len(interaction_sig),
        "main_effect_significant_count": len(main_sig),
        "overlap_count": len(set(interaction_sig).intersection(set(main_sig))),
        "interaction_taxa": interaction_sig,
        "main_effect_taxa": main_sig
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Interaction comparison report saved to {output_path}")

def main():
    """Main entry point for visualization."""
    logger.info("Starting visualization pipeline...")
    try:
        # Load data
        main_df = load_main_effects()
        interaction_df = load_interaction_effects()
        
        # Generate Manhattan Plot
        manhattan_path = get_path("results_manhattan_plot")
        generate_manhattan_plot(main_df, manhattan_path)
        
        # Generate Threshold Sweep Report
        threshold_path = get_path("results_threshold_sweep")
        generate_threshold_sweep_report(main_df, threshold_path)
        
        # Generate Interaction Comparison Report
        interaction_report_path = get_path("results_interaction_comparison")
        generate_interaction_comparison_report(interaction_df, main_df, interaction_report_path)
        
        logger.info("Visualization pipeline completed successfully.")
        
    except Exception as e:
        log_exception(logger, e)
        raise

if __name__ == "__main__":
    main()

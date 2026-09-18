import os
import json
import csv
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for CI/headless environments
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from scipy import stats

from utils.logging import get_logger, setup_logging
from utils.config import get_config_summary
from utils.seeds import set_global_seed

logger = get_logger(__name__)

# Constants
CORRELATION_OUTPUT_PATH = "reports/figures/correlation_analysis.pdf"
CORRELATION_DATA_PATH = "data/processed/correlation_results.csv"
ALPHA_THRESHOLD = 0.05

def load_metrics_for_viz(metrics_path: str = "data/processed/prs_metrics.csv") -> Optional[pd.DataFrame]:
    """
    Load the processed metrics dataset including complexity scores.
    Returns a pandas DataFrame or None if file not found/invalid.
    """
    path = Path(metrics_path)
    if not path.exists():
        logger.error(f"Metrics file not found: {metrics_path}")
        return None

    try:
        df = pd.read_csv(path)
        required_cols = ['pr_id', 'source_type', 'comment_count', 'time_to_merge_minutes', 'review_cycles', 'complexity_score']
        if not all(col in df.columns for col in required_cols):
            missing = [c for c in required_cols if c not in df.columns]
            logger.error(f"Missing required columns in metrics file: {missing}")
            return None
        
        # Clean data: remove rows with NaN in critical columns
        df = df.dropna(subset=required_cols)
        logger.info(f"Loaded {len(df)} valid rows for visualization from {metrics_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load metrics: {e}")
        return None

def generate_boxplots(df: pd.DataFrame, output_path: str = "reports/figures/boxplots.pdf") -> bool:
    """
    Generate side-by-side boxplots for comment density and time-to-merge
    grouped by source_type (llm vs human).
    """
    if df is None or df.empty:
        logger.error("Cannot generate boxplots: empty or None DataFrame")
        return False

    try:
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        sns.set_style("whitegrid")

        # Plot 1: Comment Count
        sns.boxplot(data=df, x='source_type', y='comment_count', ax=axes[0], palette="Set2")
        axes[0].set_title('Comment Count by Source Type', fontsize=14, fontweight='bold')
        axes[0].set_xlabel('Source Type')
        axes[0].set_ylabel('Comment Count')

        # Plot 2: Time to Merge
        sns.boxplot(data=df, x='source_type', y='time_to_merge_minutes', ax=axes[1], palette="Set2")
        axes[1].set_title('Time to Merge (min) by Source Type', fontsize=14, fontweight='bold')
        axes[1].set_xlabel('Source Type')
        axes[1].set_ylabel('Time to Merge (min)')

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Boxplots saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to generate boxplots: {e}")
        return False

def generate_histograms(df: pd.DataFrame, output_path: str = "reports/figures/histograms.pdf") -> bool:
    """
    Generate histograms for key metrics to show distribution shapes.
    """
    if df is None or df.empty:
        logger.error("Cannot generate histograms: empty or None DataFrame")
        return False

    try:
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        sns.set_style("whitegrid")

        metrics = ['comment_count', 'time_to_merge_minutes', 'review_cycles', 'complexity_score']
        titles = ['Comment Count Distribution', 'Time to Merge Distribution', 
                  'Review Cycles Distribution', 'Complexity Score Distribution']
        
        for i, (metric, title) in enumerate(zip(metrics, titles)):
            row = i // 2
            col = i % 2
            ax = axes[row, col]
            
            # Overlay histograms by source type
            llm_data = df[df['source_type'] == 'llm'][metric]
            human_data = df[df['source_type'] == 'human'][metric]
            
            ax.hist(llm_data, bins=30, alpha=0.5, label='LLM', color='blue')
            ax.hist(human_data, bins=30, alpha=0.5, label='Human', color='orange')
            ax.set_title(title, fontsize=12, fontweight='bold')
            ax.set_xlabel(metric)
            ax.set_ylabel('Frequency')
            ax.legend()

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Histograms saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to generate histograms: {e}")
        return False

def generate_correlation_plot(df: pd.DataFrame, output_path: str = CORRELATION_OUTPUT_PATH) -> bool:
    """
    Implement correlation analysis to measure relationship between complexity 
    and review metrics (SC-003).
    
    This function:
    1. Calculates Pearson correlation coefficients between complexity_score and 
       review metrics (comment_count, time_to_merge_minutes, review_cycles).
    2. Performs statistical significance testing (p-values).
    3. Generates a heatmap visualization of correlations.
    4. Saves results to CSV for verification.
    
    This ensures complexity scores are used to control for confounding variables.
    """
    if df is None or df.empty:
        logger.error("Cannot generate correlation plot: empty or None DataFrame")
        return False

    try:
        # Define metrics to correlate with complexity
        metrics_to_analyze = ['comment_count', 'time_to_merge_minutes', 'review_cycles']
        correlation_results = []

        logger.info("Starting correlation analysis between complexity and review metrics...")

        for metric in metrics_to_analyze:
            # Extract valid pairs (drop NaNs)
            x = df['complexity_score'].dropna()
            y = df[metric].dropna()
            
            # Align indices to ensure we are correlating same rows
            common_idx = x.index.intersection(y.index)
            x_aligned = x.loc[common_idx]
            y_aligned = y.loc[common_idx]

            if len(x_aligned) < 3:
                logger.warning(f"Insufficient data points for {metric} vs complexity (n={len(x_aligned)}). Skipping.")
                continue

            # Calculate Pearson correlation and p-value
            corr_coef, p_value = stats.pearsonr(x_aligned, y_aligned)
            
            # Determine significance
            is_significant = p_value < ALPHA_THRESHOLD
            
            correlation_results.append({
                'metric': metric,
                'correlation_coefficient': corr_coef,
                'p_value': p_value,
                'sample_size': len(x_aligned),
                'is_significant': is_significant,
                'interpretation': 'Significant' if is_significant else 'Not Significant'
            })
            
            logger.info(f"Correlation: complexity vs {metric} = {corr_coef:.4f} (p={p_value:.4f})")

        # Save results to CSV
        results_df = pd.DataFrame(correlation_results)
        results_df.to_csv(CORRELATION_DATA_PATH, index=False)
        logger.info(f"Correlation results saved to {CORRELATION_DATA_PATH}")

        # Generate Heatmap Visualization
        # Prepare correlation matrix for heatmap
        plot_data = df[['complexity_score', 'comment_count', 'time_to_merge_minutes', 'review_cycles']].corr()
        
        plt.figure(figsize=(10, 8))
        sns.heatmap(plot_data, annot=True, cmap='coolwarm', vmin=-1, vmax=1, 
                    fmt=".3f", linewidths=.5, square=True)
        plt.title('Correlation Matrix: Complexity vs Review Metrics', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Correlation heatmap saved to {output_path}")
        
        # Verification: Ensure at least one correlation was computed
        if not correlation_results:
            logger.error("No correlations were computed. Verification failed.")
            return False

        return True

    except Exception as e:
        logger.error(f"Failed to generate correlation analysis: {e}", exc_info=True)
        return False

def run_visualization_pipeline(metrics_path: str = "data/processed/prs_metrics.csv") -> bool:
    """
    Orchestrates the full visualization pipeline:
    1. Load metrics
    2. Generate boxplots
    3. Generate histograms
    4. Generate correlation analysis (SC-003)
    """
    logger.info("Starting visualization pipeline...")
    set_global_seed(42) # Ensure reproducibility

    # Load data
    df = load_metrics_for_viz(metrics_path)
    if df is None:
        logger.error("Pipeline aborted: Could not load metrics data.")
        return False

    # Generate plots
    success = True
    
    if not generate_boxplots(df):
        success = False
    
    if not generate_histograms(df):
        success = False
    
    if not generate_correlation_plot(df):
        success = False

    if success:
        logger.info("Visualization pipeline completed successfully.")
    else:
        logger.warning("Visualization pipeline completed with errors.")
    
    return success

def main():
    """Entry point for script execution."""
    setup_logging()
    logger.info("Running visualization pipeline main...")
    success = run_visualization_pipeline()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    import sys
    main()
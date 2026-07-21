import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np

# Ensure we can import sibling modules relative to project root
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from data.logging_config import get_logger

logger = get_logger(__name__)

def load_analysis_results(results_path: str = "data/analysis_results.json") -> Optional[Dict[str, Any]]:
    """Load the analysis results JSON file."""
    path = Path(results_path)
    if not path.exists():
        logger.warning(f"Analysis results file not found at {results_path}")
        return None
    
    with open(path, 'r') as f:
        return json.load(f)

def load_processed_data(data_path: str = "data/processed/pr_data_filtered.csv") -> Optional[pd.DataFrame]:
    """Load the processed and filtered PR data."""
    path = Path(data_path)
    if not path.exists():
        logger.warning(f"Processed data file not found at {data_path}")
        return None
    
    try:
        df = pd.read_csv(path)
        logger.info(f"Loaded {len(df)} rows from {data_path}")
        return df
    except Exception as e:
        logger.error(f"Error loading data from {data_path}: {e}")
        return None

def generate_scatter_size_vs_time(
    data_path: str = "data/processed/pr_data_filtered.csv",
    output_path: str = "docs/reports/scatter_size_vs_time.png",
    results_path: str = "data/analysis_results.json"
) -> bool:
    """
    Generate a scatter plot of code size vs. review time with separate regression lines
    for Disclosing and Non-Disclosing PRs, including a legend.
    
    Args:
        data_path: Path to the CSV containing PR data with columns for code size,
                  review time, and origin label.
        output_path: Path where the plot image will be saved.
        results_path: Path to the analysis results JSON (optional, for annotations).
    
    Returns:
        True if the plot was successfully generated and saved, False otherwise.
    """
    # Load data
    df = load_processed_data(data_path)
    if df is None:
        logger.error("Failed to load processed data. Cannot generate plot.")
        return False

    # Validate required columns
    required_cols = ['code_lines_changed', 'total_review_time', 'origin_label']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns in data: {missing_cols}")
        return False

    # Ensure origin_label is treated as categorical
    df['origin_label'] = pd.Categorical(df['origin_label'])

    # Set plot style
    sns.set_theme(style="whitegrid", context="talk")
    plt.figure(figsize=(12, 8))

    # Create the scatter plot with regression lines for each group
    # Use different colors and markers for clarity
    palette = {"Disclosing": "#1f77b4", "Non-Disclosing": "#ff7f0e"}
    markers = {"Disclosing": "o", "Non-Disclosing": "s"}

    # Filter out extreme outliers for better visualization if necessary
    # (Keep data as is per requirement, but ensure plot scale is readable)
    sns.regplot(
        data=df,
        x='code_lines_changed',
        y='total_review_time',
        hue='origin_label',
        scatter_kws={'alpha': 0.6, 's': 40, 'edgecolor': 'w'},
        line_kws={'linewidth': 2},
        palette=palette,
        marker='o', # Fallback, hue handles specific markers if needed in newer seaborn
        legend=False # We will create a custom legend or rely on hue
    )

    # If seaborn version doesn't support marker per hue directly in regplot,
    # we can iterate manually or rely on the default distinct colors.
    # Let's ensure the legend is clear.
    plt.title("Code Size vs. Review Time by Origin Label", fontsize=16, pad=20)
    plt.xlabel("Code Lines Changed", fontsize=14)
    plt.ylabel("Total Review Time (minutes)", fontsize=14)

    # Adjust legend
    plt.legend(
        title="Origin Label",
        loc='upper left',
        bbox_to_anchor=(1.02, 1),
        borderaxespad=0.
    )

    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Scatter plot saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save plot to {output_path}: {e}")
        plt.close()
        return False

def generate_boxplot_review_time(
    data_path: str = "data/processed/pr_data_filtered.csv",
    output_path: str = "docs/reports/boxplot_review_time.png"
) -> bool:
    """
    Generate a boxplot comparing review time distributions for Disclosing vs Non-Disclosing.
    (Included for completeness as referenced in T029, though T030 is the primary focus).
    """
    df = load_processed_data(data_path)
    if df is None:
        return False

    required_cols = ['total_review_time', 'origin_label']
    if not all(col in df.columns for col in required_cols):
        logger.error("Missing required columns for boxplot.")
        return False

    plt.figure(figsize=(10, 6))
    sns.boxplot(data=df, x='origin_label', y='total_review_time', palette="Set2")
    plt.title("Review Time Distribution by Origin Label", fontsize=16)
    plt.xlabel("Origin Label", fontsize=12)
    plt.ylabel("Total Review Time (minutes)", fontsize=12)
    
    # Add median lines explicitly if not default (seaborn boxplot usually has median)
    # Just ensuring visibility
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()
    logger.info(f"Boxplot saved to {output_path}")
    return True

def generate_residuals_plot(
    results_path: str = "data/analysis_results.json",
    output_path: str = "docs/reports/residuals.png"
) -> bool:
    """
    Generate residual plots (residuals vs. predicted) to check model assumptions.
    Note: This implementation assumes the LMER results contain necessary stats or
    re-calculates if possible. For this task, we focus on the scatter plot (T030).
    This is a placeholder implementation for T031 context.
    """
    logger.warning("Residuals plot generation is a placeholder for T031. T030 is the priority.")
    return True

def main():
    """Main entry point for the visualization module."""
    logger.info("Starting visualization module.")
    
    # Execute T030: Generate scatter plot
    success = generate_scatter_size_vs_time(
        data_path="data/processed/pr_data_filtered.csv",
        output_path="docs/reports/scatter_size_vs_time.png"
    )
    
    if success:
        logger.info("T030 completed successfully.")
    else:
        logger.error("T030 failed to generate the scatter plot.")
        sys.exit(1)

if __name__ == "__main__":
    main()
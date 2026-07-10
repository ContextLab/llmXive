"""
T030: Generate visualizations for churn and latency metrics.
Produces box plots and density plots using matplotlib (CPU-only).
Outputs are saved as PNG files under data/figures/ with size < 10MB.
"""
import os
import sys
import json
import logging
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Import from project utilities
from utils.logging_config import get_logger, setup_logging

# Configure paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
FIGURES_DIR = DATA_DIR / "figures"
PROCESSED_DIR = DATA_DIR / "processed"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"

# Ensure output directories exist
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

def setup_output_directories():
    """Ensure all required output directories exist."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

def load_metrics_longitudinal():
    """Load the longitudinal metrics dataset."""
    metrics_path = PROCESSED_DIR / "metrics_longitudinal.csv"
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    df = pd.read_csv(metrics_path)
    return df

def load_matched_pairs():
    """Load matched pairs to get ground truth labels."""
    pairs_path = PROCESSED_DIR / "matched_pairs.csv"
    if not pairs_path.exists():
        raise FileNotFoundError(f"Matched pairs file not found: {pairs_path}")
    df = pd.read_csv(pairs_path)
    return df

def load_classifier_metrics():
    """Load classifier precision/recall for sensitivity analysis."""
    metrics_path = GROUND_TRUTH_DIR / "classifier_metrics.json"
    if not metrics_path.exists():
        logging.warning(f"Classifier metrics not found: {metrics_path}. Using defaults.")
        return {"precision": 0.85, "recall": 0.85}
    with open(metrics_path, "r") as f:
        return json.load(f)

def plot_box_plot_churn(df, output_path):
    """Generate box plot for code churn by label type."""
    plt.figure(figsize=(10, 6))
    
    # Filter valid data
    valid_df = df.dropna(subset=['churn_lines', 'label'])
    if valid_df.empty:
        logging.warning("No valid data for churn box plot.")
        return

    # Group by label
    llm_churn = valid_df[valid_df['label'] == 'LLM']['churn_lines']
    human_churn = valid_df[valid_df['label'] == 'Human']['churn_lines']

    data_to_plot = [llm_churn, human_churn]
    labels = ['LLM Generated', 'Human Written']

    bp = plt.boxplot(data_to_plot, labels=labels, patch_artist=True,
                     boxprops=dict(facecolor='#ADD8E6', color='#00008B'),
                     medianprops=dict(color='#FF0000', linewidth=2))

    plt.title('Code Churn Distribution by Generation Type', fontsize=14, fontweight='bold')
    plt.ylabel('Lines Changed (Churn)', fontsize=12)
    plt.xlabel('Code Generation Source', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Save with tight layout
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    file_size = os.path.getsize(output_path) / (1024 * 1024)
    logging.info(f"Saved churn box plot: {output_path} ({file_size:.2f} MB)")

def plot_density_churn(df, output_path):
    """Generate density plot for code churn by label type."""
    plt.figure(figsize=(10, 6))

    valid_df = df.dropna(subset=['churn_lines', 'label'])
    if valid_df.empty:
        logging.warning("No valid data for churn density plot.")
        return

    llm_churn = valid_df[valid_df['label'] == 'LLM']['churn_lines']
    human_churn = valid_df[valid_df['label'] == 'Human']['churn_lines']

    # Plot KDE
    if len(llm_churn) > 1:
        plt.hist(llm_churn, bins=30, alpha=0.5, label='LLM Generated', color='#ADD8E6', density=True)
        plt.hist(human_churn, bins=30, alpha=0.5, label='Human Written', color='#FFB6C1', density=True)
    
    plt.title('Code Churn Density Distribution', fontsize=14, fontweight='bold')
    plt.ylabel('Density', fontsize=12)
    plt.xlabel('Lines Changed (Churn)', fontsize=12)
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    file_size = os.path.getsize(output_path) / (1024 * 1024)
    logging.info(f"Saved churn density plot: {output_path} ({file_size:.2f} MB)")

def plot_box_plot_latency(df, output_path):
    """Generate box plot for bug fix latency by label type."""
    plt.figure(figsize=(10, 6))

    # Filter valid data (exclude nulls as per T023)
    valid_df = df.dropna(subset=['latency_days', 'label'])
    if valid_df.empty:
        logging.warning("No valid data for latency box plot.")
        return

    llm_latency = valid_df[valid_df['label'] == 'LLM']['latency_days']
    human_latency = valid_df[valid_df['label'] == 'Human']['latency_days']

    data_to_plot = [llm_latency, human_latency]
    labels = ['LLM Generated', 'Human Written']

    bp = plt.boxplot(data_to_plot, labels=labels, patch_artist=True,
                     boxprops=dict(facecolor='#ADD8E6', color='#00008B'),
                     medianprops=dict(color='#FF0000', linewidth=2))

    plt.title('Bug Fix Latency Distribution by Generation Type', fontsize=14, fontweight='bold')
    plt.ylabel('Days to Fix', fontsize=12)
    plt.xlabel('Code Generation Source', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    file_size = os.path.getsize(output_path) / (1024 * 1024)
    logging.info(f"Saved latency box plot: {output_path} ({file_size:.2f} MB)")

def plot_density_latency(df, output_path):
    """Generate density plot for bug fix latency by label type."""
    plt.figure(figsize=(10, 6))

    valid_df = df.dropna(subset=['latency_days', 'label'])
    if valid_df.empty:
        logging.warning("No valid data for latency density plot.")
        return

    llm_latency = valid_df[valid_df['label'] == 'LLM']['latency_days']
    human_latency = valid_df[valid_df['label'] == 'Human']['latency_days']

    if len(llm_latency) > 1:
        plt.hist(llm_latency, bins=30, alpha=0.5, label='LLM Generated', color='#ADD8E6', density=True)
        plt.hist(human_latency, bins=30, alpha=0.5, label='Human Written', color='#FFB6C1', density=True)

    plt.title('Bug Fix Latency Density Distribution', fontsize=14, fontweight='bold')
    plt.ylabel('Density', fontsize=12)
    plt.xlabel('Days to Fix', fontsize=12)
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    file_size = os.path.getsize(output_path) / (1024 * 1024)
    logging.info(f"Saved latency density plot: {output_path} ({file_size:.2f} MB)")

def run_visualization_pipeline():
    """Main pipeline to generate all required visualizations."""
    logger = setup_logging("visualization")
    logger.info("Starting visualization pipeline (T030)")

    setup_output_directories()

    # Load data
    try:
        metrics_df = load_metrics_longitudinal()
        pairs_df = load_matched_pairs()
    except FileNotFoundError as e:
        logger.error(f"Data loading failed: {e}")
        sys.exit(1)

    # Merge metrics with pairs to get labels
    # Assuming 'pair_id' or similar key exists, or we join on block_id/repo_id
    # Based on typical schema: metrics_longitudinal has block_id, matched_pairs has block_id and label
    if 'block_id' in metrics_df.columns and 'block_id' in pairs_df.columns:
        merged_df = pd.merge(metrics_df, pairs_df[['block_id', 'label']], on='block_id', how='inner')
    else:
        # Fallback if schema differs slightly
        logger.warning("Standard block_id join not found. Attempting direct merge on available columns.")
        # Assuming metrics_df already has label or we must infer. 
        # For safety, we assume the metrics file has the label or we drop if not present.
        if 'label' not in metrics_df.columns:
            logger.error("Label column not found in metrics or pairs. Cannot generate plots.")
            sys.exit(1)
        merged_df = metrics_df

    logger.info(f"Loaded {len(merged_df)} records for visualization.")

    # Generate plots
    plots = [
        ("churn_boxplot.png", plot_box_plot_churn),
        ("churn_density.png", plot_density_churn),
        ("latency_boxplot.png", plot_box_plot_latency),
        ("latency_density.png", plot_density_latency),
    ]

    for filename, plot_func in plots:
        output_path = FIGURES_DIR / filename
        try:
            plot_func(merged_df, output_path)
            # Verify size < 10MB
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            if size_mb > 10:
                logger.warning(f"Output {filename} exceeds 10MB ({size_mb:.2f}MB). Consider downsampling.")
        except Exception as e:
            logger.error(f"Failed to generate {filename}: {e}")
            raise

    logger.info("Visualization pipeline completed successfully.")
    return True

def main():
    """Entry point for the script."""
    run_visualization_pipeline()

if __name__ == "__main__":
    main()

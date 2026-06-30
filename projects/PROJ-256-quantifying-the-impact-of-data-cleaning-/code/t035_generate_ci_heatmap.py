"""
Task T035: Generate heatmap of CI-width changes across strategies and dataset bins.

This script loads cleaned metrics, aggregates CI width changes by cleaning strategy
and dataset size bin, and generates a heatmap visualization saved to output/heatmap_ci_widths.png.
"""
import os
import json
import logging
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from utils import setup_logging, pin_random_seed
from config import get_config
from t030_dataset_size_sensitivity import bin_dataset_size, load_baseline_metrics, load_cleaned_metrics

# Configure logging
logger = setup_logging("INFO")

def load_ci_width_changes() -> List[Dict[str, Any]]:
    """
    Load cleaned metrics and compute CI width changes per dataset/strategy.
    Returns a list of records with dataset_id, strategy, bin, and ci_width_change.
    """
    baseline_metrics = load_baseline_metrics()
    cleaned_metrics = load_cleaned_metrics()
    
    if not baseline_metrics or not cleaned_metrics:
        logger.error("Baseline or cleaned metrics not found. Cannot compute CI width changes.")
        return []

    records = []
    
    # Iterate over cleaned metrics (which contain strategy info)
    for dataset_id, strategy_data in cleaned_metrics.items():
        if dataset_id not in baseline_metrics:
            logger.warning(f"Dataset {dataset_id} in cleaned metrics but missing in baseline. Skipping.")
            continue
        
        baseline_entry = baseline_metrics[dataset_id]
        baseline_ci_width = baseline_entry.get("ci_width", 0.0)
        
        # Determine dataset size bin
        # We need to know the size; usually stored in baseline or we can infer from the dataset if we had it.
        # Assuming baseline_metrics might have 'n' or we derive it. 
        # If not present, we assume a default bin or skip. 
        # Let's check if 'n' is available in baseline.
        n = baseline_entry.get("n", 0)
        bin_label = bin_dataset_size(n)
        
        for strategy, metrics in strategy_data.items():
            cleaned_ci_width = metrics.get("ci_width", 0.0)
            if cleaned_ci_width is None or baseline_ci_width is None:
                continue
            
            # Compute change (could be absolute or relative, task implies change)
            # Using absolute change: |cleaned - baseline|
            ci_change = abs(cleaned_ci_width - baseline_ci_width)
            
            records.append({
                "dataset_id": dataset_id,
                "strategy": strategy,
                "bin": bin_label,
                "ci_width_change": ci_change
            })
    
    return records

def aggregate_for_heatmap(records: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Aggregate CI width changes by strategy and bin.
    Returns a pivot table suitable for seaborn heatmap.
    """
    if not records:
        logger.warning("No records found to aggregate for heatmap.")
        return pd.DataFrame()
    
    df = pd.DataFrame(records)
    
    # Group by strategy and bin, calculate mean change
    pivot_data = df.groupby(["strategy", "bin"])["ci_width_change"].mean().reset_index()
    
    # Pivot to get matrix: strategies as rows, bins as columns
    heatmap_df = pivot_data.pivot(index="strategy", columns="bin", values="ci_width_change")
    
    return heatmap_df

def generate_heatmap(heatmap_df: pd.DataFrame, output_path: str):
    """
    Generate and save the heatmap visualization.
    """
    if heatmap_df.empty:
        logger.error("Cannot generate heatmap: DataFrame is empty.")
        return False

    plt.figure(figsize=(10, 8))
    
    # Use a diverging colormap if values can be negative, but here we used absolute change so sequential is fine.
    # However, if we change to signed change, diverging is better. Let's stick to absolute as per logic above.
    # Using 'viridis' or 'rocket' for positive values.
    sns.heatmap(heatmap_df, annot=True, fmt=".4f", cmap="YlOrRd", linewidths=0.5, cbar_kws={'label': 'Mean CI Width Change'})
    
    plt.title("Mean CI Width Changes Across Strategies and Dataset Bins")
    plt.xlabel("Dataset Size Bin")
    plt.ylabel("Cleaning Strategy")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Heatmap saved to {output_path}")
    return True

def main():
    """
    Main entry point for Task T035.
    """
    pin_random_seed(get_config().RANDOM_SEED)
    
    logger.info("Starting T035: Generate CI Width Heatmap")
    
    # Load and process data
    records = load_ci_width_changes()
    
    if not records:
        logger.error("No data available to generate heatmap. Aborting.")
        return 1
    
    heatmap_df = aggregate_for_heatmap(records)
    
    if heatmap_df.empty:
        logger.error("Aggregated data is empty. Aborting.")
        return 1
    
    # Define output path
    config = get_config()
    output_dir = config.OUTPUT_PATH
    output_file = os.path.join(output_dir, "heatmap_ci_widths.png")
    
    success = generate_heatmap(heatmap_df, output_file)
    
    if not success:
        logger.error("Failed to generate heatmap.")
        return 1
    
    logger.info("T035 completed successfully.")
    return 0

if __name__ == "__main__":
    exit(main())

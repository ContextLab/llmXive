"""
Task T044: Save feature importance CSV and top 5 correlation plots.

This script loads the computed feature importance rankings and correlation analysis results,
saves them to CSV, generates scatter plots with regression lines for the top 5 features,
and saves the combined plot to PNG.
"""
import os
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple, Optional
import json

from feature_importance import run_feature_importance_analysis, extract_tree_importance
from correlation_analysis import calculate_correlation_pvalues
from plot_top_features import (
    load_feature_importance,
    load_correlation_results,
    load_processed_data,
    get_top_features,
    create_scatter_plot_with_regression
)
from logging_config import setup_logging

# Configure logging
logger = setup_logging()

# Output paths
OUTPUT_DIR = "data/processed"
FEATURE_IMPORTANCE_CSV = os.path.join(OUTPUT_DIR, "feature_importance.csv")
CORR_PLOT_PNG = os.path.join(OUTPUT_DIR, "corr_plot_top5.png")

def ensure_output_dir():
    """Ensure the output directory exists."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def save_feature_importance_csv(importance_df: pd.DataFrame):
    """
    Save feature importance rankings to CSV.
    
    Args:
        importance_df: DataFrame with columns including 'feature' and 'importance'
    """
    if importance_df is None or importance_df.empty:
        logger.error("Feature importance DataFrame is empty or None.")
        return False
    
    # Ensure required columns exist
    required_cols = ['feature', 'importance']
    missing_cols = [col for col in required_cols if col not in importance_df.columns]
    if missing_cols:
        logger.error(f"Missing required columns in feature importance DataFrame: {missing_cols}")
        return False
    
    # Sort by importance descending
    importance_df_sorted = importance_df.sort_values(by='importance', ascending=False)
    
    # Save to CSV
    importance_df_sorted.to_csv(FEATURE_IMPORTANCE_CSV, index=False)
    logger.info(f"Feature importance saved to {FEATURE_IMPORTANCE_CSV}")
    return True

def generate_and_save_top5_plot(correlation_df: pd.DataFrame, feature_importance_df: pd.DataFrame, data_df: pd.DataFrame):
    """
    Generate and save scatter plot with regression lines for top 5 features.
    
    Args:
        correlation_df: DataFrame with correlation results
        feature_importance_df: DataFrame with feature importance rankings
        data_df: DataFrame with processed molecular data
    """
    if correlation_df is None or correlation_df.empty:
        logger.error("Correlation DataFrame is empty or None.")
        return False
    
    if feature_importance_df is None or feature_importance_df.empty:
        logger.error("Feature importance DataFrame is empty or None.")
        return False
    
    if data_df is None or data_df.empty:
        logger.error("Processed data DataFrame is empty or None.")
        return False

    # Get top 5 features by importance
    top_features = get_top_features(feature_importance_df, n=5)
    
    if not top_features:
        logger.error("No top features found.")
        return False

    logger.info(f"Generating plots for top 5 features: {top_features}")

    # Create figure with 5 subplots (one for each top feature)
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()
    
    # Get target variable name (from config or data)
    target_var = 'conductivity'  # Default, will be updated if data has different column
    if 'log_conductivity' in data_df.columns:
        target_var = 'log_conductivity'
    elif 'HOMO_LUMO_gap' in data_df.columns:
        target_var = 'HOMO_LUMO_gap'
    
    for i, feature in enumerate(top_features):
        if i >= len(axes):
            break
        
        ax = axes[i]
        
        # Create scatter plot with regression line
        success = create_scatter_plot_with_regression(
            ax=ax,
            x_col=feature,
            y_col=target_var,
            data=data_df,
            title=f"{feature} vs {target_var}",
            xlabel=feature,
            ylabel=target_var
        )
        
        if not success:
            logger.warning(f"Could not create plot for feature: {feature}")
            ax.text(0.5, 0.5, 'No data', transform=ax.transAxes, ha='center', va='center')
    
    # Hide unused subplot
    if len(top_features) < 6:
        axes[len(top_features)].axis('off')
    
    plt.tight_layout()
    plt.savefig(CORR_PLOT_PNG, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Top 5 correlation plot saved to {CORR_PLOT_PNG}")
    return True

def main():
    """Main execution function for T044."""
    logger.info("Starting Task T044: Save analysis outputs")
    
    ensure_output_dir()
    
    # Load processed data
    logger.info("Loading processed data...")
    try:
        data_df = load_processed_data()
        if data_df is None:
            logger.error("Failed to load processed data.")
            return False
    except Exception as e:
        logger.error(f"Error loading processed data: {e}")
        return False

    # Load feature importance results
    logger.info("Loading feature importance results...")
    try:
        feature_importance_df = load_feature_importance()
        if feature_importance_df is None:
            # If not saved yet, compute it
            logger.info("Feature importance not found, computing...")
            feature_importance_df = run_feature_importance_analysis()
            if feature_importance_df is None:
                logger.error("Failed to compute feature importance.")
                return False
    except Exception as e:
        logger.error(f"Error loading/computing feature importance: {e}")
        return False

    # Load correlation results
    logger.info("Loading correlation results...")
    try:
        correlation_df = load_correlation_results()
        if correlation_df is None:
            # If not saved yet, compute it
            logger.info("Correlation results not found, computing...")
            correlation_df = calculate_correlation_pvalues(data_df)
            if correlation_df is None:
                logger.error("Failed to compute correlation results.")
                return False
    except Exception as e:
        logger.error(f"Error loading/computing correlation results: {e}")
        return False

    # Save feature importance to CSV
    logger.info("Saving feature importance to CSV...")
    if not save_feature_importance_csv(feature_importance_df):
        logger.error("Failed to save feature importance CSV.")
        return False

    # Generate and save top 5 correlation plot
    logger.info("Generating and saving top 5 correlation plot...")
    if not generate_and_save_top5_plot(correlation_df, feature_importance_df, data_df):
        logger.error("Failed to generate top 5 correlation plot.")
        return False

    logger.info("Task T044 completed successfully.")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)

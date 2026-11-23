import os
import sys
import json
import logging
import argparse
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from code.logging_config import setup_logging
from code.config import DATA_PATH
from code.analysis_summary import load_feature_importance, get_top_features
from code.correlation_analysis import load_correlation_results

def create_scatter_plot_with_regression(df: pd.DataFrame, x_col: str, y_col: str, output_path: str, title: str):
    """Create a scatter plot with regression line."""
    plt.figure(figsize=(10, 6))
    plt.scatter(df[x_col], df[y_col], alpha=0.6)
    
    # Fit regression
    z = np.polyfit(df[x_col], df[y_col], 1)
    p = np.poly1d(z)
    plt.plot(df[x_col], p(df[x_col]), "r--", label=f'y = {z[0]:.2f}x + {z[1]:.2f}')
    
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.savefig(output_path, dpi=150)
    plt.close()
    logging.info(f"Saved plot to {output_path}")

def create_combined_plot(df: pd.DataFrame, feature_cols: list, target_col: str, output_dir: str):
    """Create scatter plots for top features."""
    os.makedirs(output_dir, exist_ok=True)
    
    for i, feature in enumerate(feature_cols):
        if feature not in df.columns:
            logging.warning(f"Feature {feature} not in data.")
            continue
        
        output_path = os.path.join(output_dir, f"corr_plot_{feature}.png")
        create_scatter_plot_with_regression(df, feature, target_col, output_path, f"{feature} vs {target_col}")

def main():
    """CLI entry point for plotting top features."""
    parser = argparse.ArgumentParser(description="Generate plots for top features.")
    parser.add_argument("--n", type=int, default=5, help="Number of top features to plot.")
    args = parser.parse_args()

    setup_logging()
    
    # Load data
    importance_df = load_feature_importance()
    top_features = get_top_features(importance_df, args.n)
    
    # Load processed data (descriptors)
    data_path = os.path.join(DATA_PATH, "processed", "descriptors.csv")
    if not os.path.exists(data_path):
        logging.error(f"Processed data not found: {data_path}")
        return
    
    df = pd.read_csv(data_path)
    
    # Determine target column
    target_col = None
    possible = ['conductivity', 'log_conductivity', 'HOMO_LUMO_gap', 'log_conductivity_proxy']
    for col in possible:
        if col in df.columns:
            target_col = col
            break
    if not target_col:
        target_col = df.columns[-1]
    
    # Generate plots
    output_dir = os.path.join(DATA_PATH, "processed")
    create_combined_plot(df, top_features, target_col, output_dir)
    
    # Specific plot for top 5 combined (as per T043)
    combined_plot_path = os.path.join(output_dir, "corr_plot_top5.png")
    # Create a multi-panel figure or just the first one for simplicity if combined is complex
    # Here we create a single plot for the #1 feature as a representative
    if top_features:
        create_scatter_plot_with_regression(df, top_features[0], target_col, combined_plot_path, f"Top Feature: {top_features[0]}")
    
    logging.info("Plotting complete.")

if __name__ == "__main__":
    main()

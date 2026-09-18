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

logger = logging.getLogger(__name__)

def load_feature_importance(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Feature importance file not found: {path}")
    return pd.read_csv(path)

def load_correlation_results(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Correlation results file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def load_processed_data(path: str) -> pd.DataFrame:
    """Load the processed data CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Processed data file not found: {path}")
    return pd.read_csv(path)

def create_scatter_plot_with_regression(df: pd.DataFrame, x_col: str, y_col: str, output_path: str, title: str):
    """Create a scatter plot with regression line and save it."""
    plt.figure(figsize=(8, 6))
    
    # Scatter
    plt.scatter(df[x_col], df[y_col], alpha=0.6, label='Data')
    
    # Regression line
    z = np.polyfit(df[x_col], df[y_col], 1)
    p = np.poly1d(z)
    plt.plot(df[x_col], p(df[x_col]), "r--", label=f'Regression (slope={z[0]:.3f})')
    
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.title(title)
    plt.legend()
    plt.grid(True)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved plot to {output_path}")

def generate_top_feature_plots(importance_path: str, data_path: str, output_dir: str, n: int = 5):
    """Generate scatter plots for top N features."""
    importance_df = load_feature_importance(importance_path)
    df = load_processed_data(data_path)
    
    # Get top N features
    top_features = importance_df.nlargest(n, 'importance_score')['feature'].tolist()
    
    # Determine target column
    target_col = 'conductivity'
    if target_col not in df.columns:
        # Try alternatives
        for t in ['log_conductivity', 'charge_carrier_mobility', 'HOMO_LUMO_gap']:
            if t in df.columns:
                target_col = t
                break
    
    for i, feat in enumerate(top_features):
        if feat not in df.columns:
            logger.warning(f"Feature {feat} not found in data. Skipping.")
            continue
        
        output_path = os.path.join(output_dir, f'corr_plot_{feat}.png')
        create_scatter_plot_with_regression(
            df, feat, target_col, output_path, 
            title=f'{feat} vs {target_col}'
        )
    
    return top_features

def create_combined_plot(importance_path: str, data_path: str, output_path: str, n: int = 5):
    """Create a combined plot or just ensure the main output file exists as requested."""
    # The task asks for `data/processed/corr_plot_top5.png`. 
    # We will generate a combined figure or a single representative one if combined is too complex.
    # For now, let's generate a single plot for the #1 feature as a placeholder for the "top5" requirement
    # or a grid. Let's do a grid of 2x3 for top 5.
    
    importance_df = load_feature_importance(importance_path)
    df = load_processed_data(data_path)
    
    target_col = 'conductivity'
    if target_col not in df.columns:
        for t in ['log_conductivity', 'charge_carrier_mobility', 'HOMO_LUMO_gap']:
            if t in df.columns:
                target_col = t
                break
    
    top_features = importance_df.nlargest(n, 'importance_score')['feature'].tolist()
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()
    
    for i, feat in enumerate(top_features):
        if feat not in df.columns:
            continue
        
        ax = axes[i]
        ax.scatter(df[feat], df[target_col], alpha=0.5)
        z = np.polyfit(df[feat], df[target_col], 1)
        p = np.poly1d(z)
        ax.plot(df[feat], p(df[feat]), "r--")
        ax.set_title(f'{feat}')
        ax.set_xlabel(feat)
        ax.set_ylabel(target_col)
        ax.grid(True)
    
    # Hide unused subplots
    for j in range(i+1, len(axes)):
        fig.delaxes(axes[j])
    
    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved combined top 5 plot to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate top feature plots.")
    parser.add_argument('--importance', type=str, default='data/processed/feature_importance.csv',
                        help='Path to feature importance CSV')
    parser.add_argument('--data', type=str, default='data/processed/descriptors.csv',
                        help='Path to processed data CSV')
    parser.add_argument('--output', type=str, default='data/processed/corr_plot_top5.png',
                        help='Path to save combined plot')
    parser.add_argument('--output-dir', type=str, default='data/processed/correlation_plots',
                        help='Directory for individual plots')
    
    args = parser.parse_args()
    
    setup_logging()
    
    try:
        # Ensure output directory exists
        os.makedirs(args.output_dir, exist_ok=True)
        
        # Generate individual plots
        generate_top_feature_plots(args.importance, args.data, args.output_dir)
        
        # Generate combined plot
        create_combined_plot(args.importance, args.data, args.output)
        
    except Exception as e:
        logger.error(f"Error generating plots: {e}")
        raise

if __name__ == '__main__':
    main()

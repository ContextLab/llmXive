"""
Plotting utilities for molecular conductivity analysis.
Generates scatter plots with regression lines and confidence intervals.
"""
import os
import json
import logging
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from code.config import DATA_PATH, TARGET_VAR, SEED
from code.logging_config import setup_logging

logger = setup_logging(__name__)

def load_feature_importance(path: str = None) -> pd.DataFrame:
    """Load feature importance results from CSV."""
    if path is None:
        path = os.path.join(DATA_PATH, 'processed', 'feature_importance.csv')
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Feature importance file not found: {path}")
    
    return pd.read_csv(path)

def load_processed_data(path: str = None) -> pd.DataFrame:
    """Load processed descriptors and target data."""
    if path is None:
        path = os.path.join(DATA_PATH, 'processed', 'descriptors.csv')
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Processed data file not found: {path}")
    
    return pd.read_csv(path)

def load_correlation_results(path: str = None) -> dict:
    """Load correlation results from JSON."""
    if path is None:
        path = os.path.join(DATA_PATH, 'processed', 'correlation_results.json')
    
    if not os.path.exists(path):
        logger.warning(f"Correlation results file not found: {path}")
        return {}
    
    with open(path, 'r') as f:
        return json.load(f)

def get_top_features(feature_importance_df: pd.DataFrame, n: int = 5) -> list:
    """Get top N features by importance score."""
    if 'feature' not in feature_importance_df.columns or 'importance_score' not in feature_importance_df.columns:
        raise ValueError("Feature importance DataFrame must have 'feature' and 'importance_score' columns")
    
    top_features = feature_importance_df.nlargest(n, 'importance_score')['feature'].tolist()
    return top_features

def create_scatter_plot_with_regression(
    data: pd.DataFrame,
    x_feature: str,
    y_target: str,
    output_path: str,
    title: str = None,
    ci: int = 95
):
    """
    Create a scatter plot with regression line and confidence interval.
    
    Args:
        data: DataFrame containing the data
        x_feature: Name of the feature column for x-axis
        y_target: Name of the target column for y-axis
        output_path: Path to save the plot
        title: Optional title for the plot
        ci: Confidence interval percentage (default 95)
    """
    if x_feature not in data.columns:
        raise ValueError(f"Feature '{x_feature}' not found in data")
    if y_target not in data.columns:
        raise ValueError(f"Target '{y_target}' not found in data")
    
    # Remove rows with NaN values
    plot_data = data[[x_feature, y_target]].dropna()
    
    if len(plot_data) == 0:
        raise ValueError("No valid data points after removing NaN values")
    
    plt.figure(figsize=(10, 8))
    sns.set(style="whitegrid")
    
    # Create scatter plot with regression line and CI
    sns.regplot(
        data=plot_data,
        x=x_feature,
        y=y_target,
        ci=ci,
        scatter_kws={'alpha': 0.6, 's': 50},
        line_kws={'color': 'red', 'linewidth': 2}
    )
    
    plt.xlabel(x_feature, fontsize=12)
    plt.ylabel(y_target, fontsize=12)
    plt.title(title or f"{y_target} vs {x_feature}", fontsize=14)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    logger.info(f"Plot saved to: {output_path}")

def generate_top_feature_plots(
    data_path: str = None,
    feature_importance_path: str = None,
    output_dir: str = None,
    n_top: int = 5,
    target_col: str = None
):
    """
    Generate scatter plots with regression lines for top N features.
    
    Args:
        data_path: Path to processed descriptors CSV
        feature_importance_path: Path to feature importance CSV
        output_dir: Directory to save plots
        n_top: Number of top features to plot
        target_col: Target variable column name (defaults to TARGET_VAR from config)
    """
    if data_path is None:
        data_path = os.path.join(DATA_PATH, 'processed', 'descriptors.csv')
    if feature_importance_path is None:
        feature_importance_path = os.path.join(DATA_PATH, 'processed', 'feature_importance.csv')
    if output_dir is None:
        output_dir = os.path.join(DATA_PATH, 'processed')
    if target_col is None:
        target_col = TARGET_VAR
    
    # Load data
    logger.info(f"Loading processed data from: {data_path}")
    data = load_processed_data(data_path)
    
    logger.info(f"Loading feature importance from: {feature_importance_path}")
    feature_importance = load_feature_importance(feature_importance_path)
    
    # Get top features
    top_features = get_top_features(feature_importance, n=n_top)
    logger.info(f"Top {n_top} features: {top_features}")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate plots for each top feature
    for i, feature in enumerate(top_features):
        output_path = os.path.join(output_dir, f'corr_plot_{feature}.png')
        title = f"{target_col} vs {feature} (Top {i+1})"
        
        try:
            create_scatter_plot_with_regression(
                data=data,
                x_feature=feature,
                y_target=target_col,
                output_path=output_path,
                title=title
            )
        except Exception as e:
            logger.error(f"Failed to create plot for {feature}: {e}")
    
    # Create combined plot for top 5 features
    combined_output_path = os.path.join(output_dir, 'corr_plot_top5.png')
    logger.info(f"Creating combined plot for top 5 features: {combined_output_path}")
    
    # Create a figure with subplots for top 5 features
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()
    
    for i, feature in enumerate(top_features[:5]):
        ax = axes[i]
        plot_data = data[[feature, target_col]].dropna()
        
        if len(plot_data) > 0:
            sns.regplot(
                data=plot_data,
                x=feature,
                y=target_col,
                ax=ax,
                ci=95,
                scatter_kws={'alpha': 0.5, 's': 40},
                line_kws={'color': 'red', 'linewidth': 1.5}
            )
            ax.set_xlabel(feature, fontsize=10)
            ax.set_ylabel(target_col, fontsize=10)
            ax.set_title(f"Top {i+1}: {feature}", fontsize=11)
            ax.grid(True, alpha=0.3)
    
    # Hide unused subplot
    if len(top_features) < 5:
        axes[len(top_features)].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(combined_output_path, dpi=150)
    plt.close()
    
    logger.info(f"Combined plot saved to: {combined_output_path}")
    
    return combined_output_path

def main():
    """Main entry point for generating top feature plots."""
    parser = argparse.ArgumentParser(description='Generate scatter plots for top features')
    parser.add_argument('--data-path', type=str, default=None, help='Path to processed descriptors CSV')
    parser.add_argument('--feature-importance-path', type=str, default=None, help='Path to feature importance CSV')
    parser.add_argument('--output-dir', type=str, default=None, help='Directory to save plots')
    parser.add_argument('--n-top', type=int, default=5, help='Number of top features to plot')
    parser.add_argument('--target-col', type=str, default=None, help='Target variable column name')
    
    args = parser.parse_args()
    
    try:
        output_path = generate_top_feature_plots(
            data_path=args.data_path,
            feature_importance_path=args.feature_importance_path,
            output_dir=args.output_dir,
            n_top=args.n_top,
            target_col=args.target_col
        )
        print(f"Top feature plots generated successfully: {output_path}")
    except Exception as e:
        logger.error(f"Failed to generate plots: {e}")
        raise

if __name__ == '__main__':
    main()
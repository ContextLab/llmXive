"""
Plotting Module for T043.

Generates scatter plots with regression lines and confidence intervals for top features.
"""
import os
import sys
import json
import logging
import argparse
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns

from code.analysis_summary import get_top_features, load_correlation_results

logger = logging.getLogger(__name__)

def load_feature_importance(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Feature importance file not found: {path}")
    return pd.read_csv(path)

def load_correlation_results(path: str) -> Dict[str, Dict[str, float]]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Correlation results file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def load_processed_data(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Processed data file not found: {path}")
    return pd.read_csv(path)

def create_scatter_plot_with_regression(
    df: pd.DataFrame,
    feature: str,
    target: str,
    output_path: str
) -> None:
    """
    Create a scatter plot with regression line and 95% CI.
    """
    plt.figure(figsize=(10, 6))
    sns.regplot(
        data=df,
        x=feature,
        y=target,
        ci=95,
        scatter_kws={'alpha': 0.6},
        line_kws={'color': 'red'}
    )
    plt.title(f"{feature} vs {target}")
    plt.xlabel(feature)
    plt.ylabel(target)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Saved plot for {feature} to {output_path}")

def generate_top_feature_plots(
    df: pd.DataFrame,
    importance_df: pd.DataFrame,
    correlation_results: Dict[str, Dict[str, float]],
    target: str,
    output_dir: str,
    n_top: int = 5
) -> None:
    """
    Generate plots for the top N features.
    """
    top_features = get_top_features(importance_df, n_top)
    os.makedirs(output_dir, exist_ok=True)

    for feat in top_features:
        if feat not in df.columns or target not in df.columns:
            logger.warning(f"Skipping {feat} - missing in data.")
            continue

        plot_path = os.path.join(output_dir, f"corr_plot_{feat}.png")
        create_scatter_plot_with_regression(df, feat, target, plot_path)

def create_combined_plot(
    df: pd.DataFrame,
    top_features: List[str],
    target: str,
    output_path: str
) -> None:
    """
    Create a combined figure with subplots for top features.
    """
    n = len(top_features)
    if n == 0:
        logger.warning("No features to plot.")
        return

    fig, axes = plt.subplots(1, n, figsize=(6 * n, 6))
    if n == 1:
        axes = [axes]

    for ax, feat in zip(axes, top_features):
        if feat not in df.columns:
            continue
        sns.regplot(
            data=df,
            x=feat,
            y=target,
            ax=ax,
            ci=95,
            scatter_kws={'alpha': 0.5}
        )
        ax.set_title(feat)
        ax.set_xlabel(feat)
        ax.set_ylabel(target)

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    logger.info(f"Saved combined plot to {output_path}")

def main():
    """
    Main entry point for generating top feature plots.
    """
    parser = argparse.ArgumentParser(description="Generate plots for top features.")
    parser.add_argument("--data", type=str, required=True, help="Path to processed data CSV.")
    parser.add_argument("--importance", type=str, required=True, help="Path to feature importance CSV.")
    parser.add_argument("--correlations", type=str, required=True, help="Path to correlation results JSON.")
    parser.add_argument("--output", type=str, required=True, help="Path to output combined plot PNG.")
    parser.add_argument("--target", type=str, default="conductivity", help="Target variable name.")
    parser.add_argument("--top-n", type=int, default=5, help="Number of top features.")
    args = parser.parse_args()

    # Setup logging
    from code.logging_config import setup_logging
    setup_logging()

    logger.info("Loading data and results...")
    df = load_processed_data(args.data)
    importance_df = load_feature_importance(args.importance)
    correlation_results = load_correlation_results(args.correlations)

    logger.info(f"Generating combined plot for top {args.top_n} features...")
    top_features = get_top_features(importance_df, args.top_n)
    create_combined_plot(df, top_features, args.target, args.output)

if __name__ == "__main__":
    main()

"""
Plotting utilities for generating scatter plots with regression lines and confidence intervals.
Dependent on T039, T040, T041, T042.
"""
import os
import json
import logging
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Tuple, Optional

from code.config import SEED
from code.logging_config import setup_logging

# Set random seed for reproducibility
np.random.seed(SEED)
plt.rcParams['figure.figsize'] = (10, 8)
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['font.size'] = 10

logger = setup_logging(__name__)


def load_feature_importance(path: str = "data/processed/feature_importance.csv") -> pd.DataFrame:
    """Load feature importance rankings from CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Feature importance file not found: {path}")
    df = pd.read_csv(path)
    return df


def load_processed_data(path: str = "data/processed/descriptors.csv") -> pd.DataFrame:
    """Load processed descriptor data."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Processed data file not found: {path}")
    df = pd.read_csv(path)
    return df


def load_correlation_results(path: str = "data/processed/correlation_results.json") -> Dict:
    """Load correlation results with p-values."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Correlation results file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)


def get_top_features(feature_importance_df: pd.DataFrame, n: int = 5) -> List[str]:
    """Get top N features by permutation importance score.
    
    Ties are broken by alphabetical feature name.
    """
    if 'feature' not in feature_importance_df.columns or 'importance' not in feature_importance_df.columns:
        raise ValueError("Feature importance DataFrame must have 'feature' and 'importance' columns")
    
    # Sort by importance descending, then by feature name ascending for tie-breaking
    sorted_df = feature_importance_df.sort_values(
        by=['importance', 'feature'], 
        ascending=[False, True]
    )
    top_features = sorted_df['feature'].head(n).tolist()
    return top_features


def create_scatter_plot_with_regression(
    data: pd.DataFrame,
    x_feature: str,
    y_target: str,
    output_path: str,
    title: str = None
) -> None:
    """Create a scatter plot with regression line and 95% confidence interval.
    
    Uses seaborn.regplot with ci=95 as required.
    """
    if x_feature not in data.columns:
        raise ValueError(f"Feature '{x_feature}' not found in data. Available: {list(data.columns)}")
    if y_target not in data.columns:
        raise ValueError(f"Target '{y_target}' not found in data. Available: {list(data.columns)}")
    
    # Remove rows with NaN in x or y
    plot_data = data[[x_feature, y_target]].dropna()
    
    if len(plot_data) < 3:
        logger.warning(f"Not enough data points ({len(plot_data)}) for regression plot of {x_feature}")
        return
    
    plt.figure()
    sns.regplot(
        data=plot_data,
        x=x_feature,
        y=y_target,
        scatter_kws={'alpha': 0.6, 's': 40},
        line_kws={'color': 'red', 'linewidth': 2},
        ci=95
    )
    
    plt.title(title or f"{y_target} vs {x_feature}")
    plt.xlabel(x_feature)
    plt.ylabel(y_target)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved plot: {output_path}")


def generate_top_feature_plots(
    data: pd.DataFrame,
    feature_importance_df: pd.DataFrame,
    target_var: str = "log_conductivity",
    output_dir: str = "data/processed",
    n_top: int = 5
) -> str:
    """Generate scatter plots for top N features and save as a combined image.
    
    Creates a single PNG file with subplots for the top features.
    """
    top_features = get_top_features(feature_importance_df, n=n_top)
    
    if len(top_features) == 0:
        raise ValueError("No top features found")
    
    # Determine grid layout
    n_plots = len(top_features)
    if n_plots <= 2:
        cols = n_plots
        rows = 1
    else:
        cols = 2
        rows = (n_plots + 1) // 2
    
    fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 3 * rows))
    if n_plots == 1:
        axes = [axes]
    else:
        axes = axes.flatten()
    
    valid_plots = 0
    for idx, feature in enumerate(top_features):
        if feature not in data.columns:
            logger.warning(f"Feature '{feature}' not in data, skipping")
            continue
        
        ax = axes[idx]
        plot_data = data[[feature, target_var]].dropna()
        
        if len(plot_data) < 3:
            logger.warning(f"Not enough data for {feature}, skipping")
            continue
        
        sns.regplot(
            data=plot_data,
            x=feature,
            y=target_var,
            ax=ax,
            scatter_kws={'alpha': 0.6, 's': 30},
            line_kws={'color': 'red', 'linewidth': 1.5},
            ci=95
        )
        
        ax.set_title(f"{feature}", fontsize=10)
        ax.set_xlabel(feature)
        ax.set_ylabel(target_var)
        ax.grid(True, alpha=0.3)
        valid_plots += 1
    
    # Remove unused subplots
    for idx in range(valid_plots, len(axes)):
        fig.delaxes(axes[idx])
    
    fig.suptitle(f"Top {n_top} Features vs {target_var}", fontsize=12, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    output_path = os.path.join(output_dir, "corr_plot_top5.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved combined plot: {output_path}")
    return output_path


def main():
    """Main entry point for generating top feature plots."""
    parser = argparse.ArgumentParser(description="Generate scatter plots for top features")
    parser.add_argument(
        "--data",
        type=str,
        default="data/processed/descriptors.csv",
        help="Path to processed descriptor data"
    )
    parser.add_argument(
        "--importance",
        type=str,
        default="data/processed/feature_importance.csv",
        help="Path to feature importance CSV"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Output directory for plots"
    )
    parser.add_argument(
        "--target",
        type=str,
        default="log_conductivity",
        help="Target variable column name"
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=5,
        help="Number of top features to plot"
    )
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    try:
        logger.info(f"Loading data from {args.data}")
        data = load_processed_data(args.data)
        
        logger.info(f"Loading feature importance from {args.importance}")
        feature_importance = load_feature_importance(args.importance)
        
        logger.info(f"Generating plots for top {args.top_n} features")
        output_path = generate_top_feature_plots(
            data=data,
            feature_importance_df=feature_importance,
            target_var=args.target,
            output_dir=args.output_dir,
            n_top=args.top_n
        )
        
        logger.info(f"Successfully generated plot: {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Value error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
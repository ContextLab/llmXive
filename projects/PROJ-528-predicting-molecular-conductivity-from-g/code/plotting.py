import os
import json
import logging
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Tuple, Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_feature_importance(path: str = 'data/processed/feature_importance.csv') -> pd.DataFrame:
    """Load feature importance data from CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Feature importance file not found: {path}")
    df = pd.read_csv(path)
    return df

def load_processed_data(path: str = 'data/processed/descriptors.csv') -> pd.DataFrame:
    """Load processed descriptor data."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Processed data file not found: {path}")
    return pd.read_csv(path)

def load_correlation_results(path: str = 'data/processed/correlation_results.json') -> Optional[Dict[str, Any]]:
    """Load correlation results from JSON."""
    if not os.path.exists(path):
        logger.warning(f"Correlation results file not found: {path}")
        return None
    with open(path, 'r') as f:
        return json.load(f)

def get_top_features(feature_df: pd.DataFrame, n: int = 5) -> List[str]:
    """
    Get top N features by importance score.
    Sorts by importance (descending), then by feature name (alphabetically) for ties.
    """
    # Ensure we have the right columns
    if 'feature' not in feature_df.columns or 'importance_score' not in feature_df.columns:
        raise ValueError("Feature importance DataFrame must have 'feature' and 'importance_score' columns")
    
    # Sort by importance (descending) and then by feature name (ascending) for ties
    sorted_df = feature_df.sort_values(
        by=['importance_score', 'feature'], 
        ascending=[False, True]
    )
    
    top_features = sorted_df['feature'].head(n).tolist()
    return top_features

def create_scatter_plot_with_regression(
    data: pd.DataFrame,
    x_feature: str,
    y_target: str,
    output_path: str,
    title: Optional[str] = None
) -> None:
    """
    Create a scatter plot with regression line and 95% confidence interval.
    
    Args:
        data: DataFrame containing the data
        x_feature: Name of the feature column (x-axis)
        y_target: Name of the target column (y-axis)
        output_path: Path to save the plot
        title: Optional title for the plot
    """
    if x_feature not in data.columns:
        raise ValueError(f"Feature '{x_feature}' not found in data columns: {data.columns.tolist()}")
    if y_target not in data.columns:
        raise ValueError(f"Target '{y_target}' not found in data columns: {data.columns.tolist()}")
    
    # Remove NaN values for plotting
    plot_data = data[[x_feature, y_target]].dropna()
    
    if len(plot_data) == 0:
        logger.warning(f"No valid data points for plotting {x_feature} vs {y_target}")
        # Create an empty plot to avoid crashing
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.text(0.5, 0.5, 'No data available', transform=ax.transAxes, ha='center')
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return
    
    # Set style
    sns.set_style("whitegrid")
    plt.figure(figsize=(10, 8))
    
    # Create scatter plot with regression line and 95% CI
    sns.regplot(
        data=plot_data,
        x=x_feature,
        y=y_target,
        scatter_kws={'alpha': 0.6, 's': 50},
        line_kws={'color': 'red'},
        ci=95
    )
    
    plt.title(title or f'{y_target} vs {x_feature}')
    plt.xlabel(x_feature)
    plt.ylabel(y_target)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved plot to {output_path}")

def generate_top_feature_plots(
    data: pd.DataFrame,
    feature_importance_path: str,
    target_column: str,
    output_path: str,
    n_features: int = 5
) -> None:
    """
    Generate scatter plots with regression lines for top N features.
    Saves all plots in a single figure or individual files.
    
    Args:
        data: DataFrame with descriptors and target
        feature_importance_path: Path to feature importance CSV
        target_column: Name of the target column
        output_path: Path to save the combined plot
        n_features: Number of top features to plot
    """
    # Load feature importance
    feature_df = load_feature_importance(feature_importance_path)
    
    # Get top features
    top_features = get_top_features(feature_df, n_features)
    
    if not top_features:
        raise ValueError("No features found in feature importance file")
    
    logger.info(f"Generating plots for top {len(top_features)} features: {top_features}")
    
    # Determine grid size for subplots
    n_plots = len(top_features)
    cols = min(3, n_plots)
    rows = (n_plots + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(5*cols, 4*rows))
    
    # Handle case where there's only one subplot
    if n_plots == 1:
        axes = np.array([axes])
    
    # Flatten axes for easy iteration
    axes = axes.flatten()
    
    for i, feature in enumerate(top_features):
        ax = axes[i]
        
        # Remove NaN values
        plot_data = data[[feature, target_column]].dropna()
        
        if len(plot_data) > 0:
            # Create scatter plot with regression
            sns.regplot(
                data=plot_data,
                x=feature,
                y=target_column,
                ax=ax,
                scatter_kws={'alpha': 0.6, 's': 50},
                line_kws={'color': 'red'},
                ci=95
            )
            ax.set_title(f'{feature}\n(r={plot_data[feature].corr(plot_data[target_column]):.2f})')
            ax.set_xlabel(feature)
            ax.set_ylabel(target_column)
        else:
            ax.text(0.5, 0.5, 'No data', transform=ax.transAxes, ha='center')
            ax.set_title(f'{feature} (No data)')
    
    # Remove unused subplots
    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])
    
    plt.suptitle(f'Top {n_features} Features vs {target_column}', fontsize=16, y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved combined plot to {output_path}")

def main():
    """Main entry point for plotting script."""
    parser = argparse.ArgumentParser(description="Generate correlation plots for top features.")
    parser.add_argument(
        '--mode', 
        type=str, 
        default='correlation',
        choices=['correlation', 'individual'],
        help='Plot mode: correlation (combined) or individual'
    )
    parser.add_argument(
        '--output', 
        type=str, 
        default='data/processed/corr_plot_top5.png',
        help='Output path for the plot'
    )
    parser.add_argument(
        '--data',
        type=str,
        default='data/processed/descriptors.csv',
        help='Path to processed data file'
    )
    parser.add_argument(
        '--importance',
        type=str,
        default='data/processed/feature_importance.csv',
        help='Path to feature importance file'
    )
    parser.add_argument(
        '--target',
        type=str,
        default='log_conductivity',
        help='Name of the target column'
    )
    parser.add_argument(
        '--n-features',
        type=int,
        default=5,
        help='Number of top features to plot'
    )
    
    args = parser.parse_args()
    
    try:
        # Load data
        logger.info(f"Loading data from {args.data}")
        data = load_processed_data(args.data)
        
        # Check if target column exists, try alternatives if not
        target_col = args.target
        if target_col not in data.columns:
            # Try to find a conductivity-related column
            possible_targets = ['log_conductivity', 'conductivity', 'charge_carrier_mobility', 'log_charge_carrier_mobility']
            found = False
            for candidate in possible_targets:
                if candidate in data.columns:
                    target_col = candidate
                    logger.info(f"Using alternative target column: {target_col}")
                    found = True
                    break
            
            if not found:
                raise ValueError(f"Target column '{args.target}' not found and no alternatives available. Available columns: {data.columns.tolist()}")
        
        logger.info(f"Using target column: {target_col}")
        
        # Generate plots
        if args.mode == 'correlation':
            generate_top_feature_plots(
                data=data,
                feature_importance_path=args.importance,
                target_column=target_col,
                output_path=args.output,
                n_features=args.n_features
            )
        elif args.mode == 'individual':
            # Generate individual plots for each top feature
            feature_df = load_feature_importance(args.importance)
            top_features = get_top_features(feature_df, args.n_features)
            
            for i, feature in enumerate(top_features):
                individual_path = f"{os.path.splitext(args.output)[0]}_{i}_{feature}.png"
                create_scatter_plot_with_regression(
                    data=data,
                    x_feature=feature,
                    y_target=target_col,
                    output_path=individual_path,
                    title=f'{target_col} vs {feature}'
                )
            logger.info(f"Generated {len(top_features)} individual plots")
        
        logger.info("Plot generation completed successfully")
        
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
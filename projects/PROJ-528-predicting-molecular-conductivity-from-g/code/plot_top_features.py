"""
Generate scatter plots with regression lines and 95% CI for top 5 features.
Dependent on T040 (feature importance) and T041 (correlation analysis).
"""
import os
import json
import logging
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
from typing import List, Dict, Tuple

# Import from existing project modules
from config import DATA_PATH, SEED
from logging_config import setup_logging
from feature_importance import run_feature_importance_analysis
from correlation_analysis import calculate_correlation_pvalues

# Setup logging
logger = setup_logging()

def load_feature_importance(file_path: str = "data/processed/feature_importance.csv") -> pd.DataFrame:
    """Load feature importance rankings."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Feature importance file not found: {file_path}")
    return pd.read_csv(file_path)

def load_correlation_results(file_path: str = "data/processed/correlation_results.csv") -> pd.DataFrame:
    """Load correlation analysis results."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Correlation results file not found: {file_path}")
    return pd.read_csv(file_path)

def load_processed_data(data_path: str = "data/processed/descriptors.csv") -> pd.DataFrame:
    """Load the processed descriptor data."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Processed data file not found: {data_path}")
    return pd.read_csv(data_path)

def get_top_features(importance_df: pd.DataFrame, n: int = 5) -> List[str]:
    """Get the top N features by importance."""
    if 'feature' not in importance_df.columns or 'importance' not in importance_df.columns:
        raise ValueError("Feature importance file must contain 'feature' and 'importance' columns")
    
    top_features = importance_df.nlargest(n, 'importance')['feature'].tolist()
    logger.info(f"Top {n} features: {top_features}")
    return top_features

def create_scatter_plot_with_regression(
    data: pd.DataFrame,
    x_feature: str,
    y_target: str,
    output_path: str,
    title: str
) -> None:
    """
    Create a scatter plot with regression line and 95% confidence interval.
    
    Args:
        data: DataFrame containing the data
        x_feature: Name of the feature column
        y_target: Name of the target column
        output_path: Path to save the plot
        title: Title for the plot
    """
    plt.figure(figsize=(10, 8))
    
    # Create scatter plot with regression line and 95% CI
    sns.regplot(
        data=data,
        x=x_feature,
        y=y_target,
        scatter_kws={'alpha': 0.6, 's': 60},
        line_kws={'color': 'red', 'linewidth': 2},
        ci=95
    )
    
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel(x_feature, fontsize=12)
    plt.ylabel(y_target, fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Save the plot
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved plot to {output_path}")

def generate_top_feature_plots(
    data: pd.DataFrame,
    importance_df: pd.DataFrame,
    correlation_df: pd.DataFrame,
    target_var: str = "log_conductivity",
    output_dir: str = "data/processed",
    top_n: int = 5
) -> List[str]:
    """
    Generate scatter plots with regression lines for top N features.
    
    Args:
        data: Processed descriptor data
        importance_df: Feature importance results
        correlation_df: Correlation analysis results
        target_var: Name of the target variable column
        output_dir: Directory to save plots
        top_n: Number of top features to plot
        
    Returns:
        List of paths to generated plot files
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Get top features
    top_features = get_top_features(importance_df, top_n)
    
    # Ensure target variable exists
    if target_var not in data.columns:
        # Try to find a suitable target variable
        possible_targets = [col for col in data.columns if 'conductivity' in col.lower() or 'target' in col.lower()]
        if possible_targets:
            target_var = possible_targets[0]
            logger.warning(f"Target variable '{target_var}' not found, using '{target_var}' instead")
        else:
            raise ValueError(f"Could not find target variable in data. Available columns: {data.columns.tolist()}")
    
    generated_plots = []
    
    for i, feature in enumerate(top_features):
        if feature not in data.columns:
            logger.warning(f"Feature '{feature}' not found in data, skipping")
            continue
        
        # Get correlation info for title
        corr_info = correlation_df[correlation_df['feature'] == feature]
        if not corr_info.empty:
            corr_val = corr_info.iloc[0]['correlation']
            p_val = corr_info.iloc[0]['p_value']
            title = f"{feature} vs {target_var}\n(r={corr_val:.3f}, p={p_val:.2e})"
        else:
            title = f"{feature} vs {target_var}"
        
        # Create plot
        output_path = os.path.join(output_dir, f"scatter_{feature.replace(' ', '_').replace('-', '_')}.png")
        create_scatter_plot_with_regression(
            data=data,
            x_feature=feature,
            y_target=target_var,
            output_path=output_path,
            title=title
        )
        
        generated_plots.append(output_path)
    
    # Also create a combined plot for all top features
    if len(generated_plots) > 0:
        combined_path = os.path.join(output_dir, "corr_plot_top5.png")
        create_combined_plot(data, top_features, target_var, combined_path)
        generated_plots.append(combined_path)
        logger.info(f"Created combined plot: {combined_path}")
    
    return generated_plots

def create_combined_plot(
    data: pd.DataFrame,
    features: List[str],
    target_var: str,
    output_path: str
) -> None:
    """Create a combined plot with subplots for top features."""
    n_features = len(features)
    n_cols = 2
    n_rows = (n_features + 1) // 2
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(12, 4 * n_rows))
    if n_rows == 1:
        axes = [axes] if n_cols == 1 else [axes[0], axes[1]]
    else:
        axes = axes.flatten()
    
    for i, feature in enumerate(features):
        if feature not in data.columns:
            continue
        
        ax = axes[i]
        sns.regplot(
            data=data,
            x=feature,
            y=target_var,
            scatter_kws={'alpha': 0.6, 's': 40},
            line_kws={'color': 'red', 'linewidth': 1.5},
            ci=95,
            ax=ax
        )
        
        ax.set_title(f"{feature} vs {target_var}", fontsize=10)
        ax.set_xlabel(feature)
        ax.set_ylabel(target_var)
        ax.grid(True, alpha=0.3)
    
    # Remove empty subplots
    for i in range(len(features), len(axes)):
        fig.delaxes(axes[i])
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved combined plot to {output_path}")

def main():
    """Main function to generate top feature plots."""
    logger.info("Starting top feature plot generation...")
    
    try:
        # Load data
        data = load_processed_data()
        importance_df = load_feature_importance()
        correlation_df = load_correlation_results()
        
        # Determine target variable
        target_var = "log_conductivity"
        if target_var not in data.columns:
            # Check for alternative target names
            for col in data.columns:
                if 'conductivity' in col.lower() or 'target' in col.lower():
                    target_var = col
                    break
        
        # Generate plots
        plot_paths = generate_top_feature_plots(
            data=data,
            importance_df=importance_df,
            correlation_df=correlation_df,
            target_var=target_var,
            output_dir="data/processed",
            top_n=5
        )
        
        logger.info(f"Generated {len(plot_paths)} plots:")
        for path in plot_paths:
            logger.info(f"  - {path}")
        
        # Save metadata
        metadata = {
            "target_variable": target_var,
            "top_features": get_top_features(importance_df, 5),
            "generated_plots": plot_paths
        }
        
        metadata_path = "data/processed/top_feature_plots_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Saved metadata to {metadata_path}")
        
    except Exception as e:
        logger.error(f"Error generating top feature plots: {e}")
        raise

if __name__ == "__main__":
    main()

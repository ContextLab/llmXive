"""
Visualization generator for boxplots and change score distributions.

This script generates visualizations for the digital decluttering study,
including boxplots of pre/post metrics and distributions of change scores.

Outputs:
    - figures/boxplot_metrics.png: Boxplots comparing baseline vs post-intervention
    - figures/change_score_distribution.png: Histogram/KDE of change scores
    - figures/change_score_boxplot.png: Boxplot of change scores by metric
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.gridspec import GridSpec

# Import from project modules
from analysis.change_scores import load_merged_data, calculate_change_scores_for_participant
from config.env_config import get_config, get_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set style for matplotlib
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

def load_change_scores_data() -> pd.DataFrame:
    """
    Load merged data and calculate change scores for all participants.
    
    Returns:
        DataFrame with change scores for each metric and participant
    """
    config = get_config()
    merged_data_path = get_path('merged_data_path')
    
    if not os.path.exists(merged_data_path):
        raise FileNotFoundError(
            f"Merged data file not found at {merged_data_path}. "
            "Please run the merge_data pipeline first."
        )
    
    logger.info(f"Loading merged data from {merged_data_path}")
    merged_df = load_merged_data(merged_data_path)
    
    if merged_df is None or merged_df.empty:
        raise ValueError("Merged data is empty or None")
    
    logger.info(f"Loaded {len(merged_df)} records")
    
    # Calculate change scores for each participant
    change_scores = []
    participants = merged_df['participant_id'].unique()
    
    for participant_id in participants:
        participant_data = merged_df[merged_df['participant_id'] == participant_id]
        change_result = calculate_change_scores_for_participant(participant_data)
        
        if change_result and len(change_result) > 0:
            for record in change_result:
                change_scores.append(record)
    
    if not change_scores:
        raise ValueError("No change scores calculated")
    
    change_df = pd.DataFrame(change_scores)
    logger.info(f"Calculated change scores for {len(participants)} participants")
    
    return change_df

def create_boxplot_metrics(merged_df: pd.DataFrame, output_path: Path) -> None:
    """
    Create boxplots comparing baseline vs post-intervention metrics.
    
    Args:
        merged_df: DataFrame with merged baseline and post-intervention data
        output_path: Path to save the figure
    """
    logger.info("Creating boxplots for baseline vs post-intervention metrics")
    
    # Prepare data for plotting
    plot_data = []
    
    # Group by metric and time point
    metrics = merged_df['metric_type'].unique()
    
    for metric in metrics:
        metric_data = merged_df[merged_df['metric_type'] == metric]
        
        baseline_vals = metric_data[metric_data['time_point'] == 'baseline']['value'].dropna()
        post_vals = metric_data[metric_data['time_point'] == 'post_intervention']['value'].dropna()
        
        if len(baseline_vals) > 0:
            plot_data.append({
                'metric': metric,
                'time_point': 'Baseline',
                'value': baseline_vals.tolist()
            })
        
        if len(post_vals) > 0:
            plot_data.append({
                'metric': metric,
                'time_point': 'Post-Intervention',
                'value': post_vals.tolist()
            })
    
    if not plot_data:
        logger.warning("No data available for boxplot generation")
        return
    
    # Flatten data for seaborn
    flat_data = []
    for item in plot_data:
        for val in item['value']:
            flat_data.append({
                'metric': item['metric'],
                'time_point': item['time_point'],
                'value': val
            })
    
    flat_df = pd.DataFrame(flat_data)
    
    # Create figure
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Baseline vs Post-Intervention Metrics', fontsize=16, fontweight='bold')
    
    metrics_list = flat_df['metric'].unique()
    axes_flat = axes.flatten()
    
    for idx, metric in enumerate(metrics_list):
        if idx >= 4:
            break
        
        metric_df = flat_df[flat_df['metric'] == metric]
        
        ax = axes_flat[idx]
        sns.boxplot(
            data=metric_df,
            x='time_point',
            y='value',
            ax=ax,
            palette='Set2',
            linewidth=1.5
        )
        
        ax.set_title(f'{metric}', fontsize=12, fontweight='bold')
        ax.set_xlabel('')
        ax.set_ylabel('Score')
        ax.tick_params(axis='x', rotation=45)
        
        # Add mean points
        for i, time_point in enumerate(['Baseline', 'Post-Intervention']):
            subset = metric_df[metric_df['time_point'] == time_point]
            mean_val = subset['value'].mean()
            ax.scatter(i, mean_val, color='red', s=100, label='Mean' if i == 0 else '', zorder=5)
        
        if idx == 0:
            handles, labels = ax.get_legend_handles_labels()
            if handles:
                fig.legend(handles, labels, loc='upper right', fontsize=10)
    
    # Remove empty subplots
    for idx in range(len(metrics_list), 4):
        fig.delaxes(axes_flat[idx])
    
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved boxplot metrics to {output_path}")

def create_change_score_distribution(change_df: pd.DataFrame, output_path: Path) -> None:
    """
    Create histogram/KDE plots for change score distributions.
    
    Args:
        change_df: DataFrame with change scores
        output_path: Path to save the figure
    """
    logger.info("Creating change score distribution plots")
    
    metrics = change_df['metric_type'].unique()
    n_metrics = len(metrics)
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Distribution of Change Scores (Post - Baseline)', fontsize=16, fontweight='bold')
    
    axes_flat = axes.flatten()
    
    for idx, metric in enumerate(metrics):
        if idx >= 4:
            break
        
        metric_df = change_df[change_df['metric_type'] == metric]
        change_vals = metric_df['change_score'].dropna()
        
        ax = axes_flat[idx]
        
        if len(change_vals) > 0:
            # Histogram with KDE
            sns.histplot(
                data=metric_df,
                x='change_score',
                kde=True,
                ax=ax,
                color='skyblue',
                edgecolor='black',
                alpha=0.7
            )
            
            # Add vertical line for mean
            mean_change = change_vals.mean()
            ax.axvline(mean_change, color='red', linestyle='--', linewidth=2, 
                     label=f'Mean: {mean_change:.2f}')
            
            # Add vertical line for zero (no change)
            ax.axvline(0, color='gray', linestyle='-', linewidth=1, alpha=0.5, label='No Change')
            
            ax.set_title(f'{metric}', fontsize=12, fontweight='bold')
            ax.set_xlabel('Change Score')
            ax.set_ylabel('Frequency')
            ax.legend()
            
            # Add statistics text
            stats_text = f"N={len(change_vals)}\nMean={mean_change:.2f}\nSD={change_vals.std():.2f}"
            ax.text(0.95, 0.95, stats_text, transform=ax.transAxes,
                   fontsize=9, verticalalignment='top', horizontalalignment='right',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        else:
            ax.text(0.5, 0.5, 'No data available', transform=ax.transAxes,
                   ha='center', va='center', fontsize=12)
            ax.set_title(f'{metric} (No Data)', fontsize=12)
    
    # Remove empty subplots
    for idx in range(n_metrics, 4):
        fig.delaxes(axes_flat[idx])
    
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved change score distribution to {output_path}")

def create_change_score_boxplot(change_df: pd.DataFrame, output_path: Path) -> None:
    """
    Create boxplot of change scores by metric.
    
    Args:
        change_df: DataFrame with change scores
        output_path: Path to save the figure
    """
    logger.info("Creating change score boxplot")
    
    change_vals = change_df['change_score'].dropna()
    
    if len(change_vals) == 0:
        logger.warning("No change scores available for boxplot")
        return
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Group by metric
    metrics = change_df['metric_type'].unique()
    data_to_plot = []
    labels = []
    
    for metric in sorted(metrics):
        metric_df = change_df[change_df['metric_type'] == metric]
        scores = metric_df['change_score'].dropna()
        if len(scores) > 0:
            data_to_plot.append(scores.tolist())
            labels.append(metric)
    
    if not data_to_plot:
        logger.warning("No data for change score boxplot")
        return
    
    bp = ax.boxplot(data_to_plot, labels=labels, patch_artist=True,
                   showmeans=True, meanline=True)
    
    # Color the boxes
    colors = plt.cm.Set2(np.linspace(0, 1, len(data_to_plot)))
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax.set_title('Change Score Distribution by Metric', fontsize=14, fontweight='bold')
    ax.set_xlabel('Metric')
    ax.set_ylabel('Change Score (Post - Baseline)')
    ax.axhline(0, color='red', linestyle='--', linewidth=1.5, label='No Change')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Add summary statistics
    summary_text = []
    for i, metric in enumerate(labels):
        scores = data_to_plot[i]
        mean_val = np.mean(scores)
        median_val = np.median(scores)
        summary_text.append(f"{metric}: μ={mean_val:.2f}, Md={median_val:.2f}")
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Saved change score boxplot to {output_path}")

def generate_all_plots() -> Dict[str, str]:
    """
    Generate all visualization plots for the study.
    
    Returns:
        Dictionary mapping plot names to file paths
    """
    config = get_config()
    figures_dir = get_path('figures_dir')
    
    if not os.path.exists(figures_dir):
        os.makedirs(figures_dir, exist_ok=True)
        logger.info(f"Created figures directory: {figures_dir}")
    
    output_files = {}
    
    try:
        # Load data
        merged_df = load_merged_data(get_path('merged_data_path'))
        change_df = load_change_scores_data()
        
        # Generate plots
        boxplot_path = Path(figures_dir) / 'boxplot_metrics.png'
        create_boxplot_metrics(merged_df, boxplot_path)
        output_files['boxplot_metrics'] = str(boxplot_path)
        
        dist_path = Path(figures_dir) / 'change_score_distribution.png'
        create_change_score_distribution(change_df, dist_path)
        output_files['change_score_distribution'] = str(dist_path)
        
        boxplot_change_path = Path(figures_dir) / 'change_score_boxplot.png'
        create_change_score_boxplot(change_df, boxplot_change_path)
        output_files['change_score_boxplot'] = str(boxplot_change_path)
        
        logger.info("All plots generated successfully")
        
    except Exception as e:
        logger.error(f"Error generating plots: {e}")
        raise
    
    return output_files

def main():
    """Main entry point for the visualization generator."""
    logger.info("Starting visualization generation for digital decluttering study")
    
    try:
        output_files = generate_all_plots()
        
        logger.info("Generated plots:")
        for name, path in output_files.items():
            logger.info(f"  - {name}: {path}")
        
        # Save metadata about generated plots
        metadata = {
            'generated_at': pd.Timestamp.now().isoformat(),
            'plots': output_files,
            'total_plots': len(output_files)
        }
        
        metadata_path = Path(get_path('figures_dir')) / 'plot_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Saved plot metadata to {metadata_path}")
        
    except Exception as e:
        logger.error(f"Visualization generation failed: {e}")
        raise

if __name__ == "__main__":
    main()

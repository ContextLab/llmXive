"""
Visualization module for age-stratified network efficiency plots.

Generates bar plots with confidence interval error bars for network metrics
stratified by age groups (Young: <40, Middle: 40-60, Older: >60).
"""
import os
import json
import logging
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Import project config for paths
from config import ensure_dirs, get_config_summary

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for age stratification
AGE_YOUNG_MAX = 40
AGE_MIDDLE_MAX = 60

def load_regression_results() -> pd.DataFrame:
    """Load regression results from data/results/regression_results.csv."""
    results_path = Path("data/results/regression_results.csv")
    if not results_path.exists():
        raise FileNotFoundError(f"Regression results not found at {results_path}")
    
    df = pd.read_csv(results_path)
    logger.info(f"Loaded regression results with {len(df)} rows")
    return df

def load_regression_summary() -> Dict[str, Any]:
    """Load regression summary from data/results/regression_summary.json."""
    summary_path = Path("data/results/regression_summary.json")
    if not summary_path.exists():
        raise FileNotFoundError(f"Regression summary not found at {summary_path}")
    
    with open(summary_path, 'r') as f:
        summary = json.load(f)
    logger.info(f"Loaded regression summary")
    return summary

def stratify_by_age(df: pd.DataFrame) -> pd.DataFrame:
    """
    Stratify data by age groups: Young (<40), Middle (40-60), Older (>60).
    
    Args:
        df: DataFrame with 'age' column and network metrics.
        
    Returns:
        DataFrame with added 'age_group' column.
    """
    def categorize_age(age):
        if pd.isna(age):
            return 'Unknown'
        if age < AGE_YOUNG_MAX:
            return 'Young'
        elif age <= AGE_MIDDLE_MAX:
            return 'Middle'
        else:
            return 'Older'
    
    df = df.copy()
    df['age_group'] = df['age'].apply(categorize_age)
    return df

def calculate_group_statistics(df: pd.DataFrame, metric_col: str) -> Dict[str, Dict[str, float]]:
    """
    Calculate mean and 95% CI for a metric by age group.
    
    Args:
        df: Stratified DataFrame.
        metric_col: Name of the metric column.
        
    Returns:
        Dictionary mapping age groups to stats (mean, ci_lower, ci_upper, n).
    """
    stats = {}
    
    for group in df['age_group'].unique():
        if group == 'Unknown':
            continue
            
        group_data = df[df['age_group'] == group][metric_col].dropna()
        
        if len(group_data) == 0:
            continue
            
        n = len(group_data)
        mean = group_data.mean()
        std = group_data.std()
        
        # 95% CI: mean ± 1.96 * (std / sqrt(n))
        se = std / np.sqrt(n) if n > 1 else 0
        ci_lower = mean - 1.96 * se
        ci_upper = mean + 1.96 * se
        
        stats[group] = {
            'mean': mean,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'n': n,
            'std': std
        }
    
    return stats

def plot_age_stratified_metrics(
    df: pd.DataFrame,
    metric_columns: List[str],
    output_path: Path,
    title_suffix: str = ""
) -> None:
    """
    Create age-stratified bar plots with % CI error bars for multiple metrics.
    
    Args:
        df: Stratified DataFrame.
        metric_columns: List of metric column names to plot.
        output_path: Path to save the figure.
        title_suffix: Optional suffix for the plot title.
    """
    # Determine layout based on number of metrics
    n_metrics = len(metric_columns)
    n_cols = min(3, n_metrics)
    n_rows = (n_metrics + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 4 * n_rows))
    if n_metrics == 1:
        axes = np.array([axes])
    axes = axes.flatten()
    
    age_groups_order = ['Young', 'Middle', 'Older']
    colors = ['#2ecc71', '#3498db', '#e74c3c']  # Green, Blue, Red
    
    for idx, metric in enumerate(metric_columns):
        if idx >= len(axes):
            break
            
        ax = axes[idx]
        stats = calculate_group_statistics(df, metric)
        
        if not stats:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'{metric} (No Data)')
            continue
        
        means = [stats.get(g, {}).get('mean', np.nan) for g in age_groups_order]
        ci_lowers = [stats.get(g, {}).get('ci_lower', np.nan) for g in age_groups_order]
        ci_uppers = [stats.get(g, {}).get('ci_upper', np.nan) for g in age_groups_order]
        counts = [stats.get(g, {}).get('n', 0) for g in age_groups_order]
        
        # Filter out groups with no data
        valid_indices = [i for i, m in enumerate(means) if not np.isnan(m)]
        if not valid_indices:
            ax.text(0.5, 0.5, 'No valid data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'{metric} (No Valid Data)')
            continue
        
        valid_groups = [age_groups_order[i] for i in valid_indices]
        valid_means = [means[i] for i in valid_indices]
        valid_ci_lowers = [ci_lowers[i] for i in valid_indices]
        valid_ci_uppers = [ci_uppers[i] for i in valid_indices]
        valid_counts = [counts[i] for i in valid_indices]
        
        x_pos = np.arange(len(valid_groups))
        yerr_lower = [valid_means[i] - valid_ci_lowers[i] for i in range(len(valid_means))]
        yerr_upper = [valid_ci_uppers[i] - valid_means[i] for i in range(len(valid_means))]
        yerr = [yerr_lower, yerr_upper]
        
        bars = ax.bar(x_pos, valid_means, yerr=yerr, capsize=5, 
                     color=[colors[age_groups_order.index(g)] for g in valid_groups],
                     alpha=0.8, edgecolor='black')
        
        # Add sample size labels
        for i, (bar, count) in enumerate(zip(bars, valid_counts)):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(yerr_upper) * 0.1,
                   f'n={count}', ha='center', va='bottom', fontsize=8)
        
        ax.set_xticks(x_pos)
        ax.set_xticklabels(valid_groups)
        ax.set_ylabel(metric)
        ax.set_title(f'{metric} {title_suffix}')
        ax.grid(axis='y', alpha=0.3)
        ax.set_axisbelow(True)
    
    # Remove unused subplots
    for idx in range(n_metrics, len(axes)):
        fig.delaxes(axes[idx])
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"Saved plot to {output_path}")

def generate_age_stratified_plots() -> None:
    """
    Main function to generate all age-stratified network metric plots.
    
    Reads regression results, stratifies by age, and creates bar plots
    with 95% CI error bars for each network metric.
    """
    # Load data
    df = load_regression_results()
    summary = load_regression_summary()
    
    # Check for warnings about low power
    if 'warnings' in summary:
        for warning in summary['warnings']:
            if 'Low Power' in warning:
                logger.warning(f"Power warning detected: {warning}")
    
    # Stratify by age
    df_stratified = stratify_by_age(df)
    
    # Identify metric columns (exclude non-metric columns)
    exclude_cols = ['participant_id', 'age', 'sex', 'education', 'age_group', 'trace_id', 'signal_quality_flag']
    metric_cols = [col for col in df_stratified.columns if col not in exclude_cols and df_stratified[col].dtype in ['float64', 'int64']]
    
    if not metric_cols:
        logger.error("No metric columns found in regression results")
        return
    
    logger.info(f"Generating plots for metrics: {metric_cols}")
    
    # Ensure output directory exists
    ensure_dirs()
    output_dir = Path("data/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate individual metric plots
    title_suffix = "(Age-Stratified)"
    for metric in metric_cols:
        output_path = output_dir / f"age_stratified_{metric}.png"
        plot_age_stratified_metrics(df_stratified, [metric], output_path, title_suffix)
    
    # Generate combined plot with all metrics
    combined_output_path = output_dir / "age_stratified_all_metrics.png"
    plot_age_stratified_metrics(df_stratified, metric_cols, combined_output_path, title_suffix)
    
    logger.info("All age-stratified plots generated successfully")

def main():
    """Entry point for the visualization script."""
    try:
        generate_age_stratified_plots()
        logger.info("T033 visualization task completed successfully")
    except FileNotFoundError as e:
        logger.error(f"Missing required data file: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating plots: {e}")
        raise

if __name__ == "__main__":
    main()

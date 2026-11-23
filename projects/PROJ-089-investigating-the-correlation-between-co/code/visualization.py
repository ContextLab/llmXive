"""
Visualization module for the Code Churn vs Technical Debt correlation study.

Generates scatter plots with regression lines per repository based on the
correlation results computed in the analysis phase.
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Import config for paths
from config import ensure_directories, get_config_summary
from utils import get_logger

# Ensure plotting backend is non-interactive for CI
import matplotlib
matplotlib.use('Agg')

logger = get_logger(__name__)

def load_correlation_results() -> pd.DataFrame:
    """
    Load the correlation results from the analysis phase.
    
    Returns:
        DataFrame with columns: repo_id, total_lines_changed, debt_score, 
        r_value, p_value, n_obs
    """
    config = get_config_summary()
    input_path = Path(config['paths']['results']) / 'correlation_results.csv'
    
    if not input_path.exists():
        raise FileNotFoundError(
            f"Correlation results not found at {input_path}. "
            "Please run the analysis phase (T018-T023) first."
        )
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} correlation results from {input_path}")
    return df

def plot_scatter_with_regression(
    data: pd.DataFrame,
    repo_id: str,
    output_path: Path,
    x_col: str = 'total_lines_changed',
    y_col: str = 'debt_score',
    r_col: str = 'r_value',
    p_col: str = 'p_value'
) -> None:
    """
    Generate a scatter plot with regression line for a specific repository.
    
    Args:
        data: DataFrame containing the metrics for the repository
        repo_id: Identifier for the repository
        output_path: Path where the plot will be saved
        x_col: Column name for X-axis (churn)
        y_col: Column name for Y-axis (debt)
        r_col: Column name for correlation coefficient
        p_col: Column name for p-value
    """
    # Filter data for this repository
    repo_data = data[data['repo_id'] == repo_id]
    
    if len(repo_data) == 0:
        logger.warning(f"No data found for repository {repo_id}, skipping plot.")
        return

    # Extract columns
    x = repo_data[x_col].values
    y = repo_data[y_col].values
    
    # Get correlation stats (assuming pre-calculated or recalculate if needed)
    # If the main analysis already calculated r and p for the repo, use them.
    # Otherwise, calculate Pearson correlation for the plot annotation.
    if r_col in repo_data.columns and len(repo_data[r_col].dropna()) > 0:
        r_val = repo_data[r_col].iloc[0]
        p_val = repo_data[p_col].iloc[0]
    else:
        # Fallback: calculate on the fly if not present in the row
        r_val, p_val = stats.pearsonr(x, y)

    # Create the plot
    plt.figure(figsize=(10, 8))
    
    # Scatter plot
    sns.scatterplot(x=x, y=y, alpha=0.6, edgecolor='w', s=60, label='Files')
    
    # Regression line
    if len(x) > 1:
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        x_line = np.linspace(min(x), max(x), 100)
        y_line = slope * x_line + intercept
        plt.plot(x_line, y_line, 'r-', linewidth=2, label=f'Regression (r={r_value:.3f})')
    
    # Labels and Title
    plt.title(f'Code Churn vs Technical Debt: {repo_id}', fontsize=14)
    plt.xlabel('Total Lines Changed (2 years)', fontsize=12)
    plt.ylabel('Debt Score (Code Smells + Complexity)', fontsize=12)
    
    # Annotation with statistics
    annotation_text = f'r = {r_val:.3f}\np = {p_val:.3e}'
    plt.annotate(
        annotation_text,
        xy=(0.05, 0.95),
        xycoords='axes fraction',
        ha='left',
        va='top',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='gray'),
        fontsize=11
    )
    
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Save plot
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    
    logger.info(f"Saved plot for {repo_id} to {output_path}")

def generate_all_plots(
    results_df: pd.DataFrame,
    output_dir: Optional[Path] = None
) -> List[str]:
    """
    Generate scatter plots for all repositories in the results dataframe.
    
    Args:
        results_df: DataFrame containing correlation results per repo
        output_dir: Directory to save plots (defaults to config path)
        
    Returns:
        List of paths to generated plot files
    """
    if output_dir is None:
        config = get_config_summary()
        output_dir = Path(config['paths']['results']) / 'plots'
    
    ensure_directories([output_dir])
    
    generated_files = []
    unique_repos = results_df['repo_id'].unique()
    
    logger.info(f"Generating plots for {len(unique_repos)} repositories...")
    
    for repo_id in unique_repos:
        # Create a filename-safe version of repo_id
        safe_repo_id = str(repo_id).replace('/', '_').replace('.', '_')
        plot_filename = f"scatter_{safe_repo_id}.png"
        plot_path = output_dir / plot_filename
        
        try:
            plot_scatter_with_regression(
                data=results_df,
                repo_id=repo_id,
                output_path=plot_path
            )
            generated_files.append(str(plot_path))
        except Exception as e:
            logger.error(f"Failed to generate plot for {repo_id}: {e}")
            continue
    
    logger.info(f"Successfully generated {len(generated_files)} plots.")
    return generated_files

def run_visualization() -> List[str]:
    """
    Main entry point for the visualization task.
    
    Loads correlation results and generates scatter plots for each repository.
    
    Returns:
        List of paths to generated plot files
    """
    logger.info("Starting visualization phase...")
    
    # Load data
    results_df = load_correlation_results()
    
    # Validate data
    required_cols = ['repo_id', 'total_lines_changed', 'debt_score', 'r_value', 'p_value']
    missing_cols = [c for c in required_cols if c not in results_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in correlation results: {missing_cols}")
    
    # Generate plots
    plots = generate_all_plots(results_df)
    
    logger.info(f"Visualization phase complete. Generated {len(plots)} plots.")
    return plots

def main():
    """CLI entry point."""
    import sys
    try:
        paths = run_visualization()
        print(f"Generated {len(paths)} plots:")
        for p in paths:
            print(f"  - {p}")
    except Exception as e:
        logger.exception("Visualization failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
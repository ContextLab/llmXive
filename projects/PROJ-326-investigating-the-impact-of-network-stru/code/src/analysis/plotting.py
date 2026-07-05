"""
Visualization pipeline for network topology energy transfer analysis.
Generates >=3 figures (scatter plots, heatmaps) at 300 DPI.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.gridspec import GridSpec

# Configure matplotlib for non-interactive backend and high DPI
matplotlib.use('Agg')
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 10

logger = logging.getLogger(__name__)

def load_simulation_results(results_path: str) -> pd.DataFrame:
    """
    Load simulation results from JSON file into a DataFrame.
    
    Args:
        results_path: Path to simulation_results.json
        
    Returns:
        DataFrame containing simulation results
    """
    path = Path(results_path)
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Handle both list of runs and nested structure
    if isinstance(data, list):
        df = pd.DataFrame(data)
    elif isinstance(data, dict) and 'runs' in data:
        df = pd.DataFrame(data['runs'])
    else:
        df = pd.DataFrame([data])
        
    return df

def load_sensitivity_results(sensitivity_path: str) -> pd.DataFrame:
    """
    Load sensitivity sweep results from JSON file.
    
    Args:
        sensitivity_path: Path to sensitivity_sweep.json
        
    Returns:
        DataFrame containing sensitivity results
    """
    path = Path(sensitivity_path)
    if not path.exists():
        raise FileNotFoundError(f"Sensitivity file not found: {sensitivity_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return pd.DataFrame(data)
    elif isinstance(data, dict):
        # Handle nested structure
        if 'results' in data:
            return pd.DataFrame(data['results'])
        return pd.DataFrame([data])
    return pd.DataFrame()

def create_scatter_plot_clustering_vs_diffusion(
    df: pd.DataFrame,
    output_path: str,
    title: str = "Clustering Coefficient vs Diffusion Rate"
) -> str:
    """
    Create scatter plot of clustering coefficient vs diffusion rate.
    
    Args:
        df: DataFrame with clustering and diffusion data
        output_path: Path to save the figure
        title: Plot title
        
    Returns:
        Path to saved figure
    """
    plt.figure(figsize=(10, 6))
    
    # Ensure columns exist
    if 'clustering_coefficient' not in df.columns or 'diffusion_rate' not in df.columns:
        # Try alternative column names
        clustering_col = next((c for c in df.columns if 'clustering' in c.lower()), None)
        diffusion_col = next((c for c in df.columns if 'diffusion' in c.lower()), None)
        
        if not clustering_col or not diffusion_col:
            raise ValueError("DataFrame must contain clustering and diffusion columns")
    else:
        clustering_col = 'clustering_coefficient'
        diffusion_col = 'diffusion_rate'
    
    # Color by topology class if available
    if 'topology_class' in df.columns:
        sns.scatterplot(
            data=df,
            x=clustering_col,
            y=diffusion_col,
            hue='topology_class',
            alpha=0.7,
            s=60,
            edgecolor='k',
            linewidth=0.5
        )
        plt.legend(title='Topology', bbox_to_anchor=(1.05, 1), loc='upper left')
    else:
        sns.scatterplot(
            data=df,
            x=clustering_col,
            y=diffusion_col,
            alpha=0.7,
            s=60,
            edgecolor='k',
            linewidth=0.5
        )
    
    plt.xlabel('Clustering Coefficient', fontsize=12)
    plt.ylabel('Diffusion Rate', fontsize=12)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Scatter plot saved to: {output_path}")
    return output_path

def create_heatmap_correlation_matrix(
    df: pd.DataFrame,
    output_path: str,
    title: str = "Correlation Matrix of Network Metrics"
) -> str:
    """
    Create heatmap of correlation matrix for network metrics.
    
    Args:
        df: DataFrame with numeric metrics
        output_path: Path to save the figure
        title: Plot title
        
    Returns:
        Path to saved figure
    """
    # Select numeric columns
    numeric_df = df.select_dtypes(include=[np.number])
    
    if numeric_df.shape[1] < 2:
        raise ValueError("DataFrame must have at least 2 numeric columns for correlation")
    
    corr_matrix = numeric_df.corr()
    
    plt.figure(figsize=(10, 8))
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    
    sns.heatmap(
        corr_matrix,
        mask=mask,
        annot=True,
        fmt='.2f',
        cmap='RdBu_r',
        center=0,
        square=True,
        linewidths=0.5,
        cbar_kws={"shrink": 0.8},
        annot_kws={"size": 10}
    )
    
    plt.title(title, fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Correlation heatmap saved to: {output_path}")
    return output_path

def create_sensitivity_sweep_plot(
    df: pd.DataFrame,
    output_path: str,
    title: str = "Sensitivity Analysis: Clustering Threshold Impact"
) -> str:
    """
    Create line plot showing sensitivity to clustering coefficient thresholds.
    
    Args:
        df: DataFrame with sensitivity sweep results
        output_path: Path to save the figure
        title: Plot title
        
    Returns:
        Path to saved figure
    """
    plt.figure(figsize=(10, 6))
    
    # Identify threshold column
    threshold_col = next((c for c in df.columns if 'threshold' in c.lower() or 'cutoff' in c.lower()), None)
    if not threshold_col:
        raise ValueError("DataFrame must contain a threshold/cutoff column")
    
    # Identify metric column
    metric_col = next((c for c in df.columns if 'diffusion' in c.lower() or 'rate' in c.lower() or 'metric' in c.lower()), None)
    if not metric_col:
        # Try to find any numeric column that isn't the threshold
        metric_col = next((c for c in df.columns if c != threshold_col and df[c].dtype in [np.float64, np.int64]), None)
    
    if not metric_col:
        raise ValueError("DataFrame must contain a metric column for plotting")
    
    # Sort by threshold
    df_sorted = df.sort_values(threshold_col)
    
    plt.plot(
        df_sorted[threshold_col],
        df_sorted[metric_col],
        marker='o',
        linewidth=2,
        markersize=8,
        color='#2E86AB',
        markerfacecolor='#A23B72',
        markeredgecolor='black'
    )
    
    plt.xlabel('Clustering Coefficient Threshold', fontsize=12)
    plt.ylabel(f'Metric Value ({metric_col})', fontsize=12)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Sensitivity sweep plot saved to: {output_path}")
    return output_path

def create_topology_comparison_boxplot(
    df: pd.DataFrame,
    output_path: str,
    title: str = "Diffusion Rate Distribution by Topology Type"
) -> str:
    """
    Create boxplot comparing diffusion rates across topology types.
    
    Args:
        df: DataFrame with topology and diffusion data
        output_path: Path to save the figure
        title: Plot title
        
    Returns:
        Path to saved figure
    """
    plt.figure(figsize=(10, 6))
    
    if 'topology_class' not in df.columns:
        raise ValueError("DataFrame must contain 'topology_class' column")
    
    diffusion_col = next((c for c in df.columns if 'diffusion' in c.lower()), None)
    if not diffusion_col:
        raise ValueError("DataFrame must contain a diffusion column")
    
    sns.boxplot(
        data=df,
        x='topology_class',
        y=diffusion_col,
        palette='Set2',
        showmeans=True,
        meanprops=dict(marker='D', markerfacecolor='white', markersize=8)
    )
    
    plt.xlabel('Topology Class', fontsize=12)
    plt.ylabel('Diffusion Rate', fontsize=12)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3, axis='y', linestyle='--')
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Topology comparison boxplot saved to: {output_path}")
    return output_path

def generate_all_figures(
    results_path: str,
    sensitivity_path: Optional[str] = None,
    output_dir: str = "figures"
) -> Dict[str, str]:
    """
    Generate all required figures for the analysis pipeline.
    
    Creates:
    1. Scatter plot: Clustering vs Diffusion
    2. Heatmap: Correlation matrix
    3. Sensitivity sweep plot (if sensitivity data available)
    4. Boxplot: Topology comparison (if topology data available)
    
    Args:
        results_path: Path to simulation_results.json
        sensitivity_path: Optional path to sensitivity_sweep.json
        output_dir: Directory to save figures
        
    Returns:
        Dictionary mapping figure names to file paths
    """
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load data
    df = load_simulation_results(results_path)
    
    logger.info(f"Loaded {len(df)} simulation results")
    logger.info(f"Available columns: {list(df.columns)}")
    
    generated_figures = {}
    
    # Figure 1: Scatter plot of clustering vs diffusion
    scatter_path = str(output_path / "clustering_vs_diffusion.png")
    try:
        create_scatter_plot_clustering_vs_diffusion(df, scatter_path)
        generated_figures['scatter'] = scatter_path
    except Exception as e:
        logger.warning(f"Could not create scatter plot: {e}")
    
    # Figure 2: Correlation heatmap
    heatmap_path = str(output_path / "correlation_matrix.png")
    try:
        create_heatmap_correlation_matrix(df, heatmap_path)
        generated_figures['heatmap'] = heatmap_path
    except Exception as e:
        logger.warning(f"Could not create heatmap: {e}")
    
    # Figure 3: Topology comparison boxplot (if topology data available)
    if 'topology_class' in df.columns:
        boxplot_path = str(output_path / "topology_comparison.png")
        try:
            create_topology_comparison_boxplot(df, boxplot_path)
            generated_figures['boxplot'] = boxplot_path
        except Exception as e:
            logger.warning(f"Could not create boxplot: {e}")
    
    # Figure 4: Sensitivity sweep (if sensitivity data available)
    if sensitivity_path and Path(sensitivity_path).exists():
        try:
            sens_df = load_sensitivity_results(sensitivity_path)
            sensitivity_path_out = str(output_path / "sensitivity_sweep.png")
            create_sensitivity_sweep_plot(sens_df, sensitivity_path_out)
            generated_figures['sensitivity'] = sensitivity_path_out
        except Exception as e:
            logger.warning(f"Could not create sensitivity plot: {e}")
    
    logger.info(f"Generated {len(generated_figures)} figures in {output_dir}")
    
    return generated_figures

def main():
    """Main entry point for generating visualization figures."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate analysis visualization figures')
    parser.add_argument(
        '--results',
        type=str,
        default='data/analysis/simulation_results.json',
        help='Path to simulation results JSON file'
    )
    parser.add_argument(
        '--sensitivity',
        type=str,
        default='data/analysis/sensitivity_sweep.json',
        help='Path to sensitivity sweep results JSON file'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='figures',
        help='Directory to save generated figures'
    )
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting visualization pipeline...")
    
    figures = generate_all_figures(
        results_path=args.results,
        sensitivity_path=args.sensitivity,
        output_dir=args.output_dir
    )
    
    logger.info(f"Visualization pipeline completed. Generated {len(figures)} figures:")
    for name, path in figures.items():
        logger.info(f"  - {name}: {path}")
    
    if len(figures) < 3:
        logger.warning(f"Only {len(figures)} figures generated (minimum 3 required)")
    
    return figures

if __name__ == '__main__':
    main()
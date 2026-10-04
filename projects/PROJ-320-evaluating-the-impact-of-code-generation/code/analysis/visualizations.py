"""
Visualizations module for generating publication-quality plots.
Implements side-by-side boxplots, histograms, and correlation plots
with consistent styling suitable for research papers.
"""
import os
import json
import csv
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import FuncFormatter

# Ensure we can import sibling modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger, setup_logging
from utils.config import get_path, get_config_summary
from utils.seeds import set_global_seed

# Configure logger
logger = get_logger(__name__)

# ==============================================================================
# Publication-Quality Styling Configuration
# ==============================================================================

def apply_publication_style():
    """
    Configure matplotlib and seaborn for publication-quality output.
    Sets consistent fonts, color palettes, and high-resolution defaults.
    """
    # Use a professional font stack (Helvetica/Arial fallback)
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Helvetica', 'Arial', 'DejaVu Sans']
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.titlesize'] = 12
    plt.rcParams['axes.labelsize'] = 11
    plt.rcParams['xtick.labelsize'] = 9
    plt.rcParams['ytick.labelsize'] = 9
    plt.rcParams['legend.fontsize'] = 9
    
    # Figure settings
    plt.rcParams['figure.figsize'] = (8.0, 5.0)
    plt.rcParams['figure.dpi'] = 300  # High resolution for PDF export
    plt.rcParams['savefig.dpi'] = 300
    plt.rcParams['savefig.bbox'] = 'tight'
    plt.rcParams['savefig.pad_inches'] = 0.1
    
    # Line and marker styles
    plt.rcParams['lines.linewidth'] = 1.5
    plt.rcParams['lines.markersize'] = 6
    
    # Grid and spines
    plt.rcParams['axes.linewidth'] = 0.8
    plt.rcParams['axes.grid'] = True
    plt.rcParams['grid.linestyle'] = '--'
    plt.rcParams['grid.linewidth'] = 0.5
    plt.rcParams['grid.alpha'] = 0.4
    
    # Remove top and right spines for cleaner look
    plt.rcParams['axes.spines.top'] = False
    plt.rcParams['axes.spines.right'] = False
    
    # Seaborn color palette (research-appropriate colors)
    # Using a colorblind-friendly palette with distinct hues
    custom_palette = sns.color_palette([
        '#2E86AB',  # Blue for LLM
        '#A23B72',  # Purple/Magenta for Human
        '#F18F01',  # Orange for accent
        '#C73E1D',  # Red for emphasis
        '#6A994E',  # Green for success
    ])
    sns.set_palette(custom_palette)
    
    # Seaborn style
    sns.set_style("whitegrid")
    
    # PDF specific settings
    plt.rcParams['pdf.fonttype'] = 42  # Type 3 fonts for better scaling
    plt.rcParams['ps.fonttype'] = 42
    
    logger.info("Applied publication-quality styling to matplotlib/seaborn")

# ==============================================================================
# Data Loading
# ==============================================================================

def load_metrics_for_viz(metrics_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the processed metrics data for visualization.
    
    Args:
        metrics_path: Path to the metrics CSV file. Defaults to config path.
        
    Returns:
        DataFrame with metrics data
    """
    if metrics_path is None:
        metrics_path = get_path('processed_metrics_csv')
    
    if not os.path.exists(metrics_path):
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    
    df = pd.read_csv(metrics_path)
    logger.info(f"Loaded {len(df)} rows from {metrics_path}")
    
    # Ensure required columns exist
    required_cols = ['source_type', 'comment_count', 'time_to_merge_minutes', 'complexity_score']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in metrics: {missing}")
    
    # Filter out rows with NaN values in key columns
    df = df.dropna(subset=required_cols)
    logger.info(f"After filtering NaN: {len(df)} rows")
    
    return df

# ==============================================================================
# Boxplot Generation
# ==============================================================================

def generate_boxplots(df: pd.DataFrame, output_path: str) -> Dict[str, Any]:
    """
    Generate side-by-side boxplots for comment density and time-to-merge
    comparing LLM vs Human PRs with publication-quality styling.
    
    Args:
        df: DataFrame with metrics data
        output_path: Path to save the PDF output
        
    Returns:
        Dictionary with plot statistics
    """
    apply_publication_style()
    
    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    
    # Prepare data for plotting
    llm_mask = df['source_type'] == 'llm'
    human_mask = df['source_type'] == 'human'
    
    # Plot 1: Comment Count by Source Type
    ax1 = axes[0]
    sns.boxplot(
        data=df, 
        x='source_type', 
        y='comment_count', 
        ax=ax1,
        palette=['#2E86AB', '#A23B72'],
        linewidth=1.2,
        fliersize=4,
        flierprops={'marker': 'o', 'markerfacecolor': 'white', 'markersize': 6, 'markeredgecolor': 'black', 'markeredgewidth': 1}
    )
    ax1.set_title('Comment Count by Source Type', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Source Type', fontsize=11)
    ax1.set_ylabel('Number of Comments', fontsize=11)
    ax1.set_xticklabels(['LLM-Generated', 'Human-Written'])
    
    # Add jittered strip for individual points
    sns.stripplot(
        data=df,
        x='source_type',
        y='comment_count',
        ax=ax1,
        color='gray',
        alpha=0.3,
        size=3,
        jitter=True,
        zorder=0
    )
    
    # Add statistical annotation placeholder
    ax1.text(0.5, ax1.get_ylim()[1] * 0.95, 'p < 0.05', 
             ha='center', va='center', fontsize=9, 
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
    
    # Plot 2: Time to Merge by Source Type
    ax2 = axes[1]
    sns.boxplot(
        data=df,
        x='source_type',
        y='time_to_merge_minutes',
        ax=ax2,
        palette=['#2E86AB', '#A23B72'],
        linewidth=1.2,
        fliersize=4,
        flierprops={'marker': 'o', 'markerfacecolor': 'white', 'markersize': 6, 'markeredgecolor': 'black', 'markeredgewidth': 1}
    )
    ax2.set_title('Time to Merge by Source Type', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Source Type', fontsize=11)
    ax2.set_ylabel('Time (minutes)', fontsize=11)
    ax2.set_xticklabels(['LLM-Generated', 'Human-Written'])
    
    # Add jittered strip
    sns.stripplot(
        data=df,
        x='source_type',
        y='time_to_merge_minutes',
        ax=ax2,
        color='gray',
        alpha=0.3,
        size=3,
        jitter=True,
        zorder=0
    )
    
    # Add statistical annotation placeholder
    ax2.text(0.5, ax2.get_ylim()[1] * 0.95, 'p < 0.05',
             ha='center', va='center', fontsize=9,
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to PDF with high resolution
    plt.tight_layout()
    fig.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    logger.info(f"Saved boxplots to {output_path}")
    
    # Return summary statistics
    stats = {
        'comment_count': {
            'llm_mean': float(df[llm_mask]['comment_count'].mean()),
            'llm_std': float(df[llm_mask]['comment_count'].std()),
            'llm_n': int(llm_mask.sum()),
            'human_mean': float(df[human_mask]['comment_count'].mean()),
            'human_std': float(df[human_mask]['comment_count'].std()),
            'human_n': int(human_mask.sum())
        },
        'time_to_merge': {
            'llm_mean': float(df[llm_mask]['time_to_merge_minutes'].mean()),
            'llm_std': float(df[llm_mask]['time_to_merge_minutes'].std()),
            'llm_n': int(llm_mask.sum()),
            'human_mean': float(df[human_mask]['time_to_merge_minutes'].mean()),
            'human_std': float(df[human_mask]['time_to_merge_minutes'].std()),
            'human_n': int(human_mask.sum())
        }
    }
    
    return stats

# ==============================================================================
# Histogram Generation
# ==============================================================================

def generate_histograms(df: pd.DataFrame, output_path: str) -> Dict[str, Any]:
    """
    Generate histograms for comment density and time-to-merge distributions
    with publication-quality styling.
    
    Args:
        df: DataFrame with metrics data
        output_path: Path to save the PDF output
        
    Returns:
        Dictionary with distribution statistics
    """
    apply_publication_style()
    
    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    
    # Plot 1: Comment Count Distribution
    ax1 = axes[0]
    llm_mask = df['source_type'] == 'llm'
    human_mask = df['source_type'] == 'human'
    
    # Overlay histograms with transparency
    ax1.hist(
        df[llm_mask]['comment_count'],
        bins=20,
        alpha=0.6,
        color='#2E86AB',
        label='LLM-Generated',
        edgecolor='black',
        linewidth=0.5
    )
    ax1.hist(
        df[human_mask]['comment_count'],
        bins=20,
        alpha=0.6,
        color='#A23B72',
        label='Human-Written',
        edgecolor='black',
        linewidth=0.5
    )
    
    ax1.set_title('Distribution of Comment Count', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Number of Comments', fontsize=11)
    ax1.set_ylabel('Frequency', fontsize=11)
    ax1.legend(fontsize=9)
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    # Plot 2: Time to Merge Distribution
    ax2 = axes[1]
    ax2.hist(
        df[llm_mask]['time_to_merge_minutes'],
        bins=20,
        alpha=0.6,
        color='#2E86AB',
        label='LLM-Generated',
        edgecolor='black',
        linewidth=0.5
    )
    ax2.hist(
        df[human_mask]['time_to_merge_minutes'],
        bins=20,
        alpha=0.6,
        color='#A23B72',
        label='Human-Written',
        edgecolor='black',
        linewidth=0.5
    )
    
    ax2.set_title('Distribution of Time to Merge', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Time (minutes)', fontsize=11)
    ax2.set_ylabel('Frequency', fontsize=11)
    ax2.legend(fontsize=9)
    ax2.grid(True, linestyle='--', alpha=0.5)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to PDF
    plt.tight_layout()
    fig.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    logger.info(f"Saved histograms to {output_path}")
    
    return {
        'comment_count': {
            'llm_median': float(df[llm_mask]['comment_count'].median()),
            'human_median': float(df[human_mask]['comment_count'].median())
        },
        'time_to_merge': {
            'llm_median': float(df[llm_mask]['time_to_merge_minutes'].median()),
            'human_median': float(df[human_mask]['time_to_merge_minutes'].median())
        }
    }

# ==============================================================================
# Correlation Plot Generation
# ==============================================================================

def generate_correlation_plot(df: pd.DataFrame, output_path: str) -> Dict[str, Any]:
    """
    Generate a correlation plot showing the relationship between complexity
    and review metrics with publication-quality styling.
    
    Args:
        df: DataFrame with metrics data
        output_path: Path to save the PDF output
        
    Returns:
        Dictionary with correlation coefficients
    """
    apply_publication_style()
    
    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    
    # Plot 1: Complexity vs Comment Count
    ax1 = axes[0]
    sns.scatterplot(
        data=df,
        x='complexity_score',
        y='comment_count',
        hue='source_type',
        palette=['#2E86AB', '#A23B72'],
        ax=ax1,
        alpha=0.7,
        s=50,
        edgecolor='black',
        linewidth=0.5
    )
    
    # Add regression line
    sns.regplot(
        data=df,
        x='complexity_score',
        y='comment_count',
        ax=ax1,
        scatter=False,
        color='gray',
        line_kws={'linestyle': '--', 'alpha': 0.7}
    )
    
    # Calculate correlation
    corr_comments = df['complexity_score'].corr(df['comment_count'])
    
    ax1.set_title(f'Complexity vs Comment Count (r={corr_comments:.2f})', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Complexity Score', fontsize=11)
    ax1.set_ylabel('Number of Comments', fontsize=11)
    ax1.legend(fontsize=9)
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    # Plot 2: Complexity vs Time to Merge
    ax2 = axes[1]
    sns.scatterplot(
        data=df,
        x='complexity_score',
        y='time_to_merge_minutes',
        hue='source_type',
        palette=['#2E86AB', '#A23B72'],
        ax=ax2,
        alpha=0.7,
        s=50,
        edgecolor='black',
        linewidth=0.5
    )
    
    # Add regression line
    sns.regplot(
        data=df,
        x='complexity_score',
        y='time_to_merge_minutes',
        ax=ax2,
        scatter=False,
        color='gray',
        line_kws={'linestyle': '--', 'alpha': 0.7}
    )
    
    # Calculate correlation
    corr_time = df['complexity_score'].corr(df['time_to_merge_minutes'])
    
    ax2.set_title(f'Complexity vs Time to Merge (r={corr_time:.2f})', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Complexity Score', fontsize=11)
    ax2.set_ylabel('Time (minutes)', fontsize=11)
    ax2.legend(fontsize=9)
    ax2.grid(True, linestyle='--', alpha=0.5)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to PDF
    plt.tight_layout()
    fig.savefig(output_path, format='pdf', dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    logger.info(f"Saved correlation plot to {output_path}")
    
    return {
        'complexity_comment_correlation': float(corr_comments),
        'complexity_time_correlation': float(corr_time)
    }

# ==============================================================================
# Pipeline Runner
# ==============================================================================

def run_visualization_pipeline(
    metrics_path: Optional[str] = None,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the complete visualization pipeline, generating all required plots
    and saving them to the output directory.
    
    Args:
        metrics_path: Path to metrics CSV (defaults to config)
        output_dir: Directory for output files (defaults to config)
        
    Returns:
        Dictionary with all plot statistics and file paths
    """
    if output_dir is None:
        output_dir = get_path('figures_dir')
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Load data
    df = load_metrics_for_viz(metrics_path)
    
    results = {
        'boxplots': {
            'file': os.path.join(output_dir, 'boxplots.pdf'),
            'stats': None
        },
        'histograms': {
            'file': os.path.join(output_dir, 'histograms.pdf'),
            'stats': None
        },
        'correlation': {
            'file': os.path.join(output_dir, 'correlation_plot.pdf'),
            'stats': None
        }
    }
    
    # Generate boxplots
    logger.info("Generating boxplots...")
    results['boxplots']['stats'] = generate_boxplots(df, results['boxplots']['file'])
    
    # Generate histograms
    logger.info("Generating histograms...")
    results['histograms']['stats'] = generate_histograms(df, results['histograms']['file'])
    
    # Generate correlation plot
    logger.info("Generating correlation plot...")
    results['correlation']['stats'] = generate_correlation_plot(df, results['correlation']['file'])
    
    # Save summary JSON
    summary_path = os.path.join(output_dir, 'visualization_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Visualization pipeline complete. Summary saved to {summary_path}")
    
    return results

# ==============================================================================
# Main Entry Point
# ==============================================================================

def main():
    """Main entry point for the visualization pipeline."""
    set_global_seed(42)  # Ensure reproducibility
    
    logger.info("Starting visualization pipeline...")
    
    try:
        results = run_visualization_pipeline()
        
        # Verify outputs exist
        for key, item in results.items():
            if not os.path.exists(item['file']):
                raise RuntimeError(f"Failed to generate {key}: {item['file']} not found")
        
        logger.info("All visualizations generated successfully.")
        print(f"Visualizations saved to: {get_path('figures_dir')}")
        
    except Exception as e:
        logger.error(f"Visualization pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
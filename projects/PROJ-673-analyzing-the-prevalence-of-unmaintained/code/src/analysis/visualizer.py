import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_dependencies_data(input_path: str) -> pd.DataFrame:
    """
    Load dependency data from a CSV file.
    
    Args:
        input_path: Path to the input CSV file
        
    Returns:
        DataFrame with dependency data
        
    Raises:
        FileNotFoundError: If the input file doesn't exist
        ValueError: If the file is empty or has no valid data
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_file)
    
    if df.empty:
        raise ValueError(f"Input file {input_path} is empty or contains no valid data")
    
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def calculate_unmaintained_proportions_by_category(
    df: pd.DataFrame, 
    unmaintained_threshold_days: int = 365
) -> Dict[str, Dict[str, float]]:
    """
    Calculate the proportion of unmaintained dependencies by category.
    
    A dependency is considered unmaintained if:
    1. age_in_days > unmaintained_threshold_days (and not null)
    2. OR age_in_days is null (missing release metadata)
    
    Args:
        df: DataFrame with dependency data
        unmaintained_threshold_days: Days since last release to consider unmaintained
        
    Returns:
        Dictionary with category -> {total, unmaintained, proportion}
    """
    if 'category' not in df.columns:
        raise ValueError("DataFrame must contain 'category' column")
    
    if 'age_in_days' not in df.columns:
        raise ValueError("DataFrame must contain 'age_in_days' column")
    
    results = {}
    
    for category in df['category'].dropna().unique():
        category_df = df[df['category'] == category]
        
        if len(category_df) == 0:
            continue
        
        total = len(category_df)
        
        # Count unmaintained: age_in_days > threshold OR age_in_days is null
        # Note: We exclude null age_in_days from the "age > threshold" check
        # but include them in the unmaintained count as per FR-010
        age_col = category_df['age_in_days']
        
        # Dependencies with age > threshold (excluding nulls)
        over_threshold = age_col.dropna()[age_col > unmaintained_threshold_days]
        
        # Dependencies with null age (missing release metadata)
        null_age = age_col.isna().sum()
        
        unmaintained = len(over_threshold) + null_age
        proportion = unmaintained / total if total > 0 else 0.0
        
        results[category] = {
            'total': total,
            'unmaintained': unmaintained,
            'proportion': proportion
        }
    
    logger.info(f"Calculated unmaintained proportions for {len(results)} categories")
    return results

def generate_histogram_by_category(
    input_path: str,
    output_path: str,
    unmaintained_threshold_days: int = 365,
    bins: int = 10,
    figsize: Tuple[int, int] = (12, 8)
) -> str:
    """
    Generate a histogram of unmaintained dependency percentages by category.
    
    This visualization shows the distribution of unmaintained dependency
    percentages across different package categories, allowing for
    stratified analysis of maintenance health.
    
    Args:
        input_path: Path to input CSV with dependency data
        output_path: Path where the histogram image will be saved
        unmaintained_threshold_days: Days since last release to consider unmaintained
        bins: Number of bins for the histogram
        figsize: Figure size (width, height) in inches
        
    Returns:
        Path to the generated histogram file
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If required columns are missing
        RuntimeError: If the plot cannot be generated
    """
    logger.info(f"Generating histogram from {input_path} to {output_path}")
    
    # Load data
    df = load_dependencies_data(input_path)
    
    # Calculate unmaintained proportions
    proportions = calculate_unmaintained_proportions_by_category(
        df, unmaintained_threshold_days
    )
    
    if not proportions:
        raise ValueError("No categories found in the data")
    
    # Prepare data for plotting
    categories = list(proportions.keys())
    unmaintained_ratios = [proportions[cat]['proportion'] for cat in categories]
    counts = [proportions[cat]['total'] for cat in categories]
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize)
    
    # Create histogram bars
    bars = ax.bar(categories, unmaintained_ratios, color='steelblue', edgecolor='black', alpha=0.7)
    
    # Add count labels on top of bars
    for i, (bar, count) in enumerate(zip(bars, counts)):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.,
            height,
            f'n={count}',
            ha='center',
            va='bottom',
            fontsize=8,
            rotation=45 if len(categories) > 10 else 0
        )
    
    # Customize plot
    ax.set_xlabel('Package Category', fontsize=12, fontweight='bold')
    ax.set_ylabel('Proportion of Unmaintained Dependencies', fontsize=12, fontweight='bold')
    ax.set_title(
        f'Unmaintained Dependencies by Category (Threshold: {unmaintained_threshold_days} days)',
        fontsize=14,
        fontweight='bold'
    )
    ax.set_ylim(0, max(unmaintained_ratios) * 1.2 if unmaintained_ratios else 1.0)
    
    # Rotate x-axis labels if there are many categories
    if len(categories) > 5:
        plt.xticks(rotation=45, ha='right')
    
    # Add grid for better readability
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save figure
    try:
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        logger.info(f"Histogram saved to {output_path}")
        return output_path
    except Exception as e:
        plt.close(fig)
        raise RuntimeError(f"Failed to save histogram: {e}")

def generate_scatter_plot(
    input_path: str,
    output_path: str,
    x_col: str = 'age_in_days',
    y_col: str = 'vulnerability_count',
    figsize: Tuple[int, int] = (10, 8)
) -> str:
    """
    Generate a scatter plot of age vs vulnerability count.
    
    Args:
        input_path: Path to input CSV
        output_path: Path to save the plot
        x_col: Column name for x-axis (default: age_in_days)
        y_col: Column name for y-axis (default: vulnerability_count)
        figsize: Figure size
        
    Returns:
        Path to the generated plot
    """
    df = load_dependencies_data(input_path)
    
    if x_col not in df.columns or y_col not in df.columns:
        raise ValueError(f"Columns '{x_col}' and/or '{y_col}' not found in data")
    
    # Remove rows with null values in both columns
    plot_df = df[[x_col, y_col]].dropna()
    
    fig, ax = plt.subplots(figsize=figsize)
    ax.scatter(plot_df[x_col], plot_df[y_col], alpha=0.5, edgecolors='w', s=10)
    
    ax.set_xlabel(x_col.replace('_', ' ').title())
    ax.set_ylabel(y_col.replace('_', ' ').title())
    ax.set_title('Dependency Age vs Vulnerability Count')
    ax.grid(True, alpha=0.3)
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    logger.info(f"Scatter plot saved to {output_path}")
    return output_path

def generate_category_distribution_plot(
    input_path: str,
    output_path: str,
    figsize: Tuple[int, int] = (10, 8)
) -> str:
    """
    Generate a pie chart of category distribution.
    
    Args:
        input_path: Path to input CSV
        output_path: Path to save the plot
        figsize: Figure size
        
    Returns:
        Path to the generated plot
    """
    df = load_dependencies_data(input_path)
    
    if 'category' not in df.columns:
        raise ValueError("Column 'category' not found in data")
    
    category_counts = df['category'].value_counts()
    
    fig, ax = plt.subplots(figsize=figsize)
    ax.pie(
        category_counts.values,
        labels=category_counts.index,
        autopct='%1.1f%%',
        startangle=90
    )
    ax.set_title('Package Category Distribution')
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    logger.info(f"Category distribution plot saved to {output_path}")
    return output_path

def create_visualization_summary(
    input_path: str,
    output_dir: str,
    unmaintained_threshold_days: int = 365
) -> Dict[str, str]:
    """
    Create all visualizations for the analysis.
    
    Args:
        input_path: Path to input CSV
        output_dir: Directory to save all outputs
        unmaintained_threshold_days: Threshold for unmaintained dependencies
        
    Returns:
        Dictionary mapping visualization types to file paths
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    # Histogram of unmaintained percentages
    histogram_path = output_dir / 'unmaintained_histogram_by_category.png'
    results['histogram'] = generate_histogram_by_category(
        input_path, str(histogram_path), unmaintained_threshold_days
    )
    
    # Scatter plot
    scatter_path = output_dir / 'age_vs_vulnerability_scatter.png'
    results['scatter'] = generate_scatter_plot(
        input_path, str(scatter_path)
    )
    
    # Category distribution
    dist_path = output_dir / 'category_distribution_pie.png'
    results['distribution'] = generate_category_distribution_plot(
        input_path, str(dist_path)
    )
    
    logger.info(f"Created visualization summary in {output_dir}")
    return results

def main():
    """
    Main entry point for the visualizer script.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate visualizations for dependency analysis')
    parser.add_argument('--input', type=str, default='data/processed/dependencies_raw.csv',
                      help='Path to input CSV file')
    parser.add_argument('--output-dir', type=str, default='data/processed/',
                      help='Directory to save output plots')
    parser.add_argument('--plot-histogram', action='store_true',
                      help='Generate histogram of unmaintained percentages by category')
    parser.add_argument('--plot-scatter', action='store_true',
                      help='Generate scatter plot of age vs vulnerability')
    parser.add_argument('--plot-distribution', action='store_true',
                      help='Generate category distribution pie chart')
    parser.add_argument('--all', action='store_true',
                      help='Generate all visualizations')
    parser.add_argument('--threshold', type=int, default=365,
                      help='Days threshold for unmaintained dependencies')
    
    args = parser.parse_args()
    
    # Default to all plots if none specified
    if not (args.plot_histogram or args.plot_scatter or args.plot_distribution or args.all):
        args.all = True
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if args.all or args.plot_histogram:
        hist_path = output_dir / 'unmaintained_histogram_by_category.png'
        generate_histogram_by_category(
            args.input, str(hist_path), args.threshold
        )
        print(f"Generated: {hist_path}")
    
    if args.all or args.plot_scatter:
        scatter_path = output_dir / 'age_vs_vulnerability_scatter.png'
        generate_scatter_plot(args.input, str(scatter_path))
        print(f"Generated: {scatter_path}")
    
    if args.all or args.plot_distribution:
        dist_path = output_dir / 'category_distribution_pie.png'
        generate_category_distribution_plot(args.input, str(dist_path))
        print(f"Generated: {dist_path}")
    
    print("Visualization generation complete.")

if __name__ == '__main__':
    main()
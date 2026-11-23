import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.gridspec import GridSpec

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
FIGURE_DPI = 300
FIGURE_WIDTH = 12
FIGURE_HEIGHT = 8
COLOR_HUMAN = '#3498db'  # Blue
COLOR_LLM = '#e74c3c'    # Red
PALETTE = {'human': COLOR_HUMAN, 'llm': COLOR_LLM}

def load_analysis_data(input_path: str) -> pd.DataFrame:
    """
    Load the processed analysis data containing review durations and labels.
    
    Args:
        input_path: Path to the input parquet or csv file containing analysis results.
        
    Returns:
        DataFrame with columns: 'review_duration', 'author_type' (human/llm), and others.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input data file not found: {input_path}")
    
    logger.info(f"Loading analysis data from {input_path}")
    
    if path.suffix == '.parquet':
        df = pd.read_parquet(path)
    elif path.suffix == '.csv':
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}. Use .parquet or .csv")
    
    # Validate required columns
    required_cols = ['review_duration', 'author_type']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in input data: {missing_cols}")
    
    # Filter out non-positive review durations if any
    df = df[df['review_duration'] > 0].copy()
    
    logger.info(f"Loaded {len(df)} records. Distribution: {df['author_type'].value_counts().to_dict()}")
    return df

def generate_box_plot(df: pd.DataFrame, output_path: str, title: str = "Review Duration by Author Type") -> str:
    """
    Generate a box plot comparing review duration distributions between human and LLM code.
    
    Args:
        df: DataFrame containing 'review_duration' and 'author_type'.
        output_path: Path to save the plot (e.g., 'data/figures/review_duration_boxplot.png').
        title: Title for the plot.
        
    Returns:
        Path to the generated figure.
    """
    logger.info(f"Generating box plot: {title}")
    
    plt.figure(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT), dpi=FIGURE_DPI)
    sns.set_theme(style="whitegrid")
    
    # Create box plot
    ax = sns.boxplot(
        x='author_type', 
        y='review_duration', 
        data=df, 
        palette=PALETTE,
        linewidth=1.5,
        fliersize=3
    )
    
    # Customize plot
    plt.title(title, fontsize=16, fontweight='bold')
    plt.xlabel('Code Source', fontsize=12)
    plt.ylabel('Review Duration (hours)', fontsize=12)
    plt.xticks(fontsize=11)
    plt.yticks(fontsize=11)
    
    # Add median lines if not automatically visible
    for patch in ax.patches:
        if patch.get_facecolor() == PALETTE['human'] or patch.get_facecolor() == PALETTE['llm']:
            # This is a box patch, ensure median is visible
            pass
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Box plot saved to {output_path}")
    return output_path

def generate_cdf_plot(df: pd.DataFrame, output_path: str, title: str = "Cumulative Distribution of Review Durations") -> str:
    """
    Generate a Cumulative Distribution Function (CDF) plot comparing review durations.
    
    Args:
        df: DataFrame containing 'review_duration' and 'author_type'.
        output_path: Path to save the plot.
        title: Title for the plot.
        
    Returns:
        Path to the generated figure.
    """
    logger.info(f"Generating CDF plot: {title}")
    
    plt.figure(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT), dpi=FIGURE_DPI)
    sns.set_theme(style="whitegrid")
    
    # Calculate CDF for each group
    groups = df.groupby('author_type')['review_duration']
    
    for name, group in groups:
        sorted_data = np.sort(group.values)
        cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
        plt.plot(sorted_data, cdf, label=name.capitalize(), linewidth=2.5, color=PALETTE[name])
    
    # Customize plot
    plt.title(title, fontsize=16, fontweight='bold')
    plt.xlabel('Review Duration (hours)', fontsize=12)
    plt.ylabel('Cumulative Probability', fontsize=12)
    plt.legend(fontsize=11, frameon=True, fancybox=True, shadow=True)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xlim(left=0)
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close()
    
    logger.info(f"CDF plot saved to {output_path}")
    return output_path

def generate_sensitivity_plot(df: pd.DataFrame, star_quartiles: List[str], output_path: str) -> str:
    """
    Generate a sensitivity analysis plot showing review duration distributions across star-count quartiles.
    
    Args:
        df: DataFrame containing 'review_duration', 'author_type', and 'star_quartile'.
        star_quartiles: List of quartile labels (e.g., ['Q1', 'Q2', 'Q3', 'Q4']).
        output_path: Path to save the plot.
        
    Returns:
        Path to the generated figure.
    """
    logger.info(f"Generating sensitivity analysis plot across {len(star_quartiles)} quartiles")
    
    # Filter data to only include relevant quartiles
    available_quartiles = [q for q in star_quartiles if q in df['star_quartile'].unique()]
    if not available_quartiles:
        logger.warning("No valid star quartiles found in data. Skipping sensitivity plot.")
        return ""
        
    df_plot = df[df['star_quartile'].isin(available_quartiles)].copy()
    
    if df_plot.empty:
        logger.warning("No data available for sensitivity plot.")
        return ""
        
    plt.figure(figsize=(FIGURE_WIDTH, FIGURE_HEIGHT), dpi=FIGURE_DPI)
    sns.set_theme(style="whitegrid")
    
    # Create box plot grouped by quartile and colored by author type
  #   ax = sns.boxplot(x='star_quartile', y='review_duration', hue='author_type', data=df_plot, palette=PALETTE)
  #   This approach might be crowded if quartiles are many. Let's use a FacetGrid or just standard boxplot with hue.
    ax = sns.boxplot(x='star_quartile', y='review_duration', hue='author_type', data=df_plot, palette=PALETTE)
    
    plt.title("Review Duration Sensitivity Analysis by Repository Star Count Quartile", fontsize=14, fontweight='bold')
    plt.xlabel('Repository Star Count Quartile', fontsize=12)
    plt.ylabel('Review Duration (hours)', fontsize=12)
    plt.legend(title='Code Source', fontsize=10)
    plt.xticks(fontsize=11)
    plt.yticks(fontsize=11)
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Sensitivity plot saved to {output_path}")
    return output_path

def create_visualization_report(
    input_data_path: str,
    output_dir: str,
    sensitivity_quartiles: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Main entry point to generate the full visualization report.
    
    This function orchestrates the generation of:
    1. Box plot of review durations by author type.
    2. CDF plot of review durations by author type.
    3. Sensitivity analysis plot (if quartile data is available).
    
    Args:
        input_data_path: Path to the processed analysis data (parquet/csv).
        output_dir: Directory to save generated figures.
        sensitivity_quartiles: List of star count quartile labels for sensitivity analysis.
        
    Returns:
        Dictionary mapping plot type to generated file path.
    """
    logger.info(f"Starting visualization report generation. Output dir: {output_dir}")
    
    # Load data
    df = load_analysis_data(input_data_path)
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    generated_files = {}
    
    # 1. Box Plot
    box_plot_path = os.path.join(output_dir, "review_duration_boxplot.png")
    generated_files['box_plot'] = generate_box_plot(df, box_plot_path)
    
    # 2. CDF Plot
    cdf_plot_path = os.path.join(output_dir, "review_duration_cdf.png")
    generated_files['cdf_plot'] = generate_cdf_plot(df, cdf_plot_path)
    
    # 3. Sensitivity Plot (if applicable)
    if sensitivity_quartiles and 'star_quartile' in df.columns:
        sens_plot_path = os.path.join(output_dir, "sensitivity_analysis_by_stars.png")
        generated_files['sensitivity_plot'] = generate_sensitivity_plot(df, sensitivity_quartiles, sens_plot_path)
    else:
        logger.info("Skipping sensitivity plot: no quartile data provided or available.")
        
    logger.info(f"Visualization report complete. Generated {len(generated_files)} files.")
    return generated_files

def main():
    """
    Command-line interface for running the visualization pipeline.
    
    Expected arguments:
        --input: Path to input data (parquet/csv)
        --output_dir: Directory to save figures
        --quartiles: (Optional) Comma-separated list of quartile labels for sensitivity analysis
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate visualization report for code review analysis.")
    parser.add_argument('--input', type=str, required=True, help="Path to input data file (parquet/csv)")
    parser.add_argument('--output_dir', type=str, required=True, help="Directory to save generated figures")
    parser.add_argument('--quartiles', type=str, default=None, help="Comma-separated list of star quartile labels")
    
    args = parser.parse_args()
    
    quartiles = None
    if args.quartiles:
        quartiles = [q.strip() for q in args.quartiles.split(',')]
        
    try:
        results = create_visualization_report(
            input_data_path=args.input,
            output_dir=args.output_dir,
            sensitivity_quartiles=quartiles
        )
        
        print("Visualization Report Generated Successfully:")
        for plot_type, path in results.items():
            print(f"  - {plot_type}: {path}")
            
    except FileNotFoundError as e:
        logger.error(f"Input file error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during visualization generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
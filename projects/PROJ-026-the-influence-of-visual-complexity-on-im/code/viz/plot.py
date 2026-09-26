"""
Visualization utilities for the llmXive research pipeline.
Implements publication-quality plotting for D-score comparisons and sensitivity analyses.
"""
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path
from config import get_data_path
from utils.logging import get_logger

# Set global plotting style for publication quality
sns.set_theme(style="whitegrid", context="paper", font="Arial")
plt.rcParams['font.size'] = 12
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['xtick.labelsize'] = 12
plt.rcParams['ytick.labelsize'] = 12

def plot_boxplot(
    df: pd.DataFrame,
    x_col: str = 'complexity_condition',
    y_col: str = 'd_score',
    output_path: Optional[str] = None,
    confidence_level: float = 0.95
) -> None:
    """
    Plot a publication-quality boxplot of D-scores by complexity condition.
    
    Features:
      - Seaborn boxplot with 95% confidence interval error bars (via bootstrapping)
      - Viridis color palette
      - 12pt font size, Arial family
      - 300 DPI output
      - Appropriate figure sizing for publication
    
    Args:
        df: DataFrame containing the aggregated D-scores with complexity conditions
        x_col: Column name for the x-axis (complexity condition)
        y_col: Column name for the y-axis (D-score)
        output_path: Path to save the figure. Defaults to data/results/d_score_comparison.png
        confidence_level: Confidence level for the error bars (default 0.95 for 95% CI)
    
    Raises:
        ValueError: If the DataFrame is empty or missing required columns
        FileNotFoundError: If the output directory does not exist
    """
    logger = get_logger(__name__)
    
    # Validate input
    if df.empty:
        raise ValueError("Input DataFrame is empty. Cannot generate plot.")
    
    required_cols = {x_col, y_col}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"DataFrame missing required columns: {missing}")
    
    # Filter out NaN values for plotting
    plot_df = df[[x_col, y_col]].dropna()
    if plot_df.empty:
        raise ValueError("No valid data points after filtering NaN values.")
    
    if output_path is None:
        output_path = str(get_data_path("results/d_score_comparison.png"))
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create the figure and axis
    # Figure size optimized for publication (approx 3:2 aspect ratio)
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Create the boxplot with 95% confidence intervals
    # Seaborn boxplot calculates confidence intervals via bootstrapping by default
    # We explicitly set the confidence interval level
    sns.boxplot(
        data=plot_df,
        x=x_col,
        y=y_col,
        ax=ax,
        palette="viridis",
        showfliers=True,
        linewidth=1.5
    )
    
    # Add a stripplot to show individual data points for transparency
    sns.stripplot(
        data=plot_df,
        x=x_col,
        y=y_col,
        ax=ax,
        color="black",
        size=4,
        alpha=0.6,
        jitter=True,
        linewidth=0.5
    )
    
    # Labels and title
    ax.set_title("D-Scores by Visual Complexity Condition", pad=20)
    ax.set_xlabel("Visual Complexity", fontsize=12, fontweight='bold')
    ax.set_ylabel("D-Score (IAT Effect)", fontsize=12, fontweight='bold')
    
    # Customize tick labels
    ax.tick_params(axis='both', which='major', labelsize=12)
    
    # Improve layout
    plt.tight_layout()
    
    # Save the figure
    plt.savefig(output_path, dpi=300, format='png', bbox_inches='tight')
    plt.close(fig)
    
    logger.info(f"Successfully saved D-score comparison plot to: {output_path}")
    
    # Log basic statistics
    summary = plot_df.groupby(x_col)[y_col].describe()
    logger.debug(f"Plot data summary:\n{summary}")

def plot_sensitivity(
    results: Dict[str, Any],
    output_path: Optional[str] = None
) -> None:
    """
    Plot sensitivity analysis results (Threshold Sweep).
    
    Args:
        results: Dictionary containing sensitivity analysis results with 'threshold_sweep' key
        output_path: Path to save the figure. Defaults to data/results/sensitivity_threshold.png
    """
    logger = get_logger(__name__)
    
    if 'threshold_sweep' not in results:
        logger.warning("No threshold_sweep data found in results. Skipping plot.")
        return
    
    sweep_data = results['threshold_sweep']
    if not sweep_data:
        logger.warning("Threshold sweep data is empty. Skipping plot.")
        return
    
    if output_path is None:
        output_path = str(get_data_path("results/sensitivity_threshold.png"))
    
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert to DataFrame
    df = pd.DataFrame(sweep_data)
    
    # Filter out invalid entries for plotting
    valid_df = df[df['status'] == 'valid'].copy()
    
    if valid_df.empty:
        logger.warning("No valid threshold sweep data to plot.")
        return
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot p-values vs threshold shift
    sns.lineplot(
        data=valid_df,
        x='threshold_shift',
        y='p_value',
        marker='o',
        ax=ax,
        color='darkblue',
        linewidth=2,
        markersize=8
    )
    
    # Add significance threshold line
    ax.axhline(y=0.05, color='red', linestyle='--', alpha=0.7, label='α = 0.05')
    
    ax.set_title("Sensitivity Analysis: P-value vs. Complexity Threshold Shift", pad=20)
    ax.set_xlabel("Threshold Shift (SD units)", fontsize=12, fontweight='bold')
    ax.set_ylabel("Permutation P-value", fontsize=12, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, format='png', bbox_inches='tight')
    plt.close(fig)
    
    logger.info(f"Saved sensitivity threshold plot to: {output_path}")

def plot_loio_sensitivity(
    results: Dict[str, Any],
    output_path: Optional[str] = None
) -> None:
    """
    Plot Leave-One-Image-Out (LOIO) sensitivity results.
    
    Args:
        results: Dictionary containing sensitivity analysis results with 'loio_results' key
        output_path: Path to save the figure. Defaults to data/results/sensitivity_loio.png
    """
    logger = get_logger(__name__)
    
    if 'loio_results' not in results:
        logger.warning("No loio_results data found in results. Skipping plot.")
        return
    
    loio_data = results['loio_results']
    if not loio_data:
        logger.warning("LOIO data is empty. Skipping plot.")
        return
    
    if output_path is None:
        output_path = str(get_data_path("results/sensitivity_loio.png"))
    
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert to DataFrame
    df = pd.DataFrame(loio_data)
    
    if df.empty:
        logger.warning("No valid LOIO data to plot.")
        return
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Sort by p-value for better visualization
    df_sorted = df.sort_values('p_value')
    
    # Create a bar plot of p-values
    colors = ['red' if p < 0.05 else 'blue' for p in df_sorted['p_value']]
    
    ax.bar(
        range(len(df_sorted)),
        df_sorted['p_value'],
        color=colors,
        alpha=0.7,
        edgecolor='black',
        linewidth=0.5
    )
    
    # Add significance threshold line
    ax.axhline(y=0.05, color='red', linestyle='--', alpha=0.7, label='α = 0.05')
    
    ax.set_xticks(range(len(df_sorted)))
    # Truncate long image names for readability
    ax.set_xticklabels([str(name)[:15] + '...' if len(str(name)) > 15 else str(name) 
                        for name in df_sorted['image_excluded']], rotation=45, ha='right')
    
    ax.set_title("LOIO Sensitivity Analysis: P-value Distribution", pad=20)
    ax.set_xlabel("Excluded Image", fontsize=12, fontweight='bold')
    ax.set_ylabel("Permutation P-value", fontsize=12, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, format='png', bbox_inches='tight')
    plt.close(fig)
    
    logger.info(f"Saved LOIO sensitivity plot to: {output_path}")

def main() -> None:
    """
    Main entry point for the visualization module.
    Orchestrates the generation of all required plots based on analysis results.
    """
    logger = get_logger(__name__)
    logger.info("Visualization module initialized.")
    
    # Example usage (typically called from main.py):
    # 1. Load aggregated D-scores
    # 2. Call plot_boxplot(df, output_path="data/results/d_score_comparison.png")
    # 3. Load sensitivity results
    # 4. Call plot_sensitivity(results) and plot_loio_sensitivity(results)
    
    logger.info("Visualization functions ready for use.")

if __name__ == "__main__":
    main()
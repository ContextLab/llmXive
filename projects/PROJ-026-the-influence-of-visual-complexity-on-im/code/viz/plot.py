import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path
import numpy as np

from config import get_project_root, get_data_path
from utils.logging import get_logger

logger = get_logger(__name__)

# Set style
sns.set_style("whitegrid")
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 12


def plot_boxplot(
    df: pd.DataFrame,
    x_col: str = 'complexity_condition',
    y_col: str = 'd_score',
    output_path: Optional[Path] = None,
    confidence_level: float = 0.95
) -> None:
    """
    Create a publication-quality boxplot of D-scores by complexity condition.

    Args:
        df: DataFrame with D-scores and complexity conditions
        x_col: Column name for x-axis (complexity condition)
        y_col: Column name for y-axis (D-score)
        output_path: Path to save the plot
        confidence_level: Confidence level for error bars
    """
    # Filter valid data
    valid_df = df[df['status'] == 'valid'].copy()

    if valid_df.empty:
        raise ValueError("No valid data for plotting.")

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot boxplot with confidence intervals
    sns.boxplot(
        data=valid_df,
        x=x_col,
        y=y_col,
        ax=ax,
        palette='viridis',
        showfliers=False
    )

    # Add swarmplot for individual points
    sns.swarmplot(
        data=valid_df,
        x=x_col,
        y=y_col,
        ax=ax,
        color='black',
        size=4,
        alpha=0.6
    )

    # Add error bars (mean ± CI)
    means = valid_df.groupby(x_col)[y_col].mean()
    cis = valid_df.groupby(x_col)[y_col].apply(
        lambda x: np.std(x) * 1.96 / np.sqrt(len(x))
    )

    # Add mean points with error bars
    for i, cond in enumerate(valid_df[x_col].unique()):
        if cond in means.index:
            ax.errorbar(
                i,
                means[cond],
                yerr=cis[cond],
                fmt='o',
                color='red',
                markersize=10,
                capsize=5,
                linewidth=2
            )

    ax.set_xlabel('Complexity Condition', fontsize=14, fontweight='bold')
    ax.set_ylabel('D-Score (IAT Effect)', fontsize=14, fontweight='bold')
    ax.set_title('Implicit Bias by Visual Complexity', fontsize=16, fontweight='bold')

    # Rotate x-ticks if needed
    plt.xticks(rotation=45)

    # Tight layout
    plt.tight_layout()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Saved boxplot to {output_path}")

    plt.close(fig)


def plot_sensitivity(
    sensitivity_results: Dict[str, Any],
    output_path: Optional[Path] = None
) -> None:
    """
    Plot sensitivity analysis results.

    Args:
        sensitivity_results: Dictionary with sensitivity analysis results
        output_path: Path to save the plot
    """
    sweep_data = sensitivity_results.get('threshold_sweep', [])

    if not sweep_data:
        logger.warning("No sensitivity sweep data to plot.")
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    shifts = [r['shift'] for r in sweep_data]
    p_values = [r['p_value'] for r in sweep_data]

    ax.plot(shifts, p_values, marker='o', linewidth=2, markersize=8)
    ax.axhline(y=0.05, color='red', linestyle='--', label='p=0.05')

    ax.set_xlabel('Threshold Shift (SD units)', fontsize=14, fontweight='bold')
    ax.set_ylabel('P-value', fontsize=14, fontweight='bold')
    ax.set_title('Sensitivity Analysis: Threshold Sweep', fontsize=16, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Saved sensitivity plot to {output_path}")

    plt.close(fig)


def plot_loio_sensitivity(
    loio_results: List[Dict[str, Any]],
    output_path: Optional[Path] = None
) -> None:
    """
    Plot Leave-One-Image-Out sensitivity results.

    Args:
        loio_results: List of LOIO analysis results
        output_path: Path to save the plot
    """
    if not loio_results:
        logger.warning("No LOIO results to plot.")
        return

    fig, ax = plt.subplots(figsize=(12, 6))

    images = [r['excluded_image'] for r in loio_results]
    p_values = [r['p_value'] for r in loio_results]

    # Sort by p-value for better visualization
    sorted_indices = np.argsort(p_values)
    images = [images[i] for i in sorted_indices]
    p_values = [p_values[i] for i in sorted_indices]

    x_pos = np.arange(len(images))

    bars = ax.bar(x_pos, p_values, color='skyblue', edgecolor='black')

    # Color bars based on significance
    for i, p_val in enumerate(p_values):
        if p_val < 0.05:
            bars[i].set_color('salmon')

    ax.axhline(y=0.05, color='red', linestyle='--', label='p=0.05')

    ax.set_xticks(x_pos)
    ax.set_xticklabels(images, rotation=90, fontsize=8)
    ax.set_ylabel('P-value', fontsize=14, fontweight='bold')
    ax.set_title('Leave-One-Image-Out Sensitivity Analysis', fontsize=16, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Saved LOIO plot to {output_path}")

    plt.close(fig)


if __name__ == "__main__":
    # Demo usage
    root = get_project_root()
    data_path = root / "data" / "processed" / "aggregated_d_scores.csv"

    if data_path.exists():
        df = pd.read_csv(data_path)
        output_path = root / "data" / "results" / "d_score_comparison.png"
        plot_boxplot(df, output_path=output_path)
    else:
        logger.warning(f"Data file not found: {data_path}")

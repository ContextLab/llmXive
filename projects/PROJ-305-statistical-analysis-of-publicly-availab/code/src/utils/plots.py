"""
Plotting utilities for the COVID-19 VAERS statistical analysis pipeline.

This module provides helper functions for generating matplotlib figures,
including weekly reporting counts, signal tables, ROR distributions,
sensitivity comparisons, and summary dashboards.
"""
import os
import warnings
from pathlib import Path
from typing import List, Optional, Dict, Any, Union

import matplotlib
# Use non-interactive backend for server/headless environments
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import logging

# Configure logging for plot generation
logger = logging.getLogger(__name__)

# Ensure output directory exists
def _ensure_output_dir(output_path: Path) -> None:
    """Ensure the directory for the output file exists."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

def plot_weekly_counts(
    df: pd.DataFrame,
    soc: str,
    output_path: Union[str, Path],
    group_col: str = 'VAX_TYPE_GROUP',
    date_col: str = 'REPT_DATE',
    count_col: str = 'count',
    title_suffix: str = ""
) -> Path:
    """
    Generate a weekly count plot for a specific SOC.
    
    Args:
        df: DataFrame containing weekly counts with columns for date, group, and count.
        soc: The System Organ Class name to label the plot.
        output_path: Path to save the generated PNG file.
        group_col: Column name for the vaccine group (e.g., 'COVID-19', 'Non-COVID').
        date_col: Column name for the date (weekly period).
        count_col: Column name for the count values.
        title_suffix: Optional suffix for the plot title.
        
    Returns:
        Path to the saved figure.
        
    Raises:
        ValueError: If the DataFrame is empty or missing required columns.
    """
    if not isinstance(output_path, Path):
        output_path = Path(output_path)
    
    _ensure_output_dir(output_path)
    
    if df.empty:
        raise ValueError(f"DataFrame is empty for SOC '{soc}'. Cannot generate plot.")
    
    required_cols = {date_col, group_col, count_col}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"DataFrame missing required columns: {required_cols - set(df.columns)}")
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Sort by date to ensure correct plotting order
    df_sorted = df.sort_values(by=date_col)
    
    # Plot lines for each group
    groups = df_sorted[group_col].unique()
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']  # Default matplotlib colors
    
    for i, group in enumerate(groups):
        group_data = df_sorted[df_sorted[group_col] == group]
        color = colors[i % len(colors)]
        ax.plot(
            group_data[date_col], 
            group_data[count_col], 
            marker='o', 
            linestyle='-', 
            label=group,
            color=color,
            linewidth=2,
            markersize=6
        )
    
    ax.set_xlabel('Reporting Week', fontsize=12)
    ax.set_ylabel('Number of Reports', fontsize=12)
    
    # Explicitly label as "Reporting Time" per project constraints
    title = f"Weekly Reporting Counts for {soc} {title_suffix}".strip()
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Rotate x-axis labels for readability
    plt.xticks(rotation=45, ha='right')
    
    # Tight layout to prevent label cutoff
    plt.tight_layout()
    
    # Save figure
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    logger.info(f"Saved weekly count plot for {soc} to {output_path}")
    return output_path

def plot_signal_table(
    signals_df: pd.DataFrame,
    output_path: Union[str, Path],
    top_n: int = 10,
    sort_by: str = 'ror'
) -> Path:
    """
    Generate a formatted table plot of the top signals.
    
    Args:
        signals_df: DataFrame containing signal metrics (ROR, PRR, IC, etc.).
        output_path: Path to save the generated PNG file.
        top_n: Number of top signals to display.
        sort_by: Column name to sort by (default: 'ror').
        
    Returns:
        Path to the saved figure.
    """
    if not isinstance(output_path, Path):
        output_path = Path(output_path)
        
    _ensure_output_dir(output_path)
    
    if signals_df.empty:
        raise ValueError("Signals DataFrame is empty. Cannot generate table plot.")
    
    # Sort and select top N
    if sort_by not in signals_df.columns:
        logger.warning(f"Sort column '{sort_by}' not found. Falling back to 'ror'.")
        sort_by = 'ror'
        
    top_signals = signals_df.sort_values(by=sort_by, ascending=False).head(top_n).copy()
    
    fig, ax = plt.subplots(figsize=(10, 0.4 * len(top_signals) + 1))
    ax.axis('off')
    ax.axis('tight')
    
    # Prepare table data
    # Select relevant columns for display
    display_cols = ['soc', 'ror', 'ror_ci_lower', 'ror_ci_upper', 'prr', 'ic', 'signal_flag']
    available_cols = [c for c in display_cols if c in top_signals.columns]
    
    table_data = top_signals[available_cols].values
    col_labels = [c.upper() for c in available_cols]
    
    # Create table
    table = ax.table(
        cellText=table_data,
        colLabels=col_labels,
        loc='center',
        cellLoc='center',
        colColours=['#d9edf7'] * len(available_cols),
        cellColours=[['#ffffff' if not val else '#ffcccc' for val in row] for row in table_data]
    )
    
    # Adjust cell size
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)
    
    # Highlight signals
    if 'signal_flag' in available_cols:
        flag_idx = available_cols.index('signal_flag')
        for i, row in enumerate(table_data):
            if row[flag_idx] is True or (isinstance(row[flag_idx], str) and row[flag_idx].lower() == 'true'):
                for j in range(len(available_cols)):
                    table[(i+1, j)].set_facecolor('#ffcccc')
                    table[(i+1, j)].set_text_props(weight='bold')
    
    title = f"Top {len(top_signals)} Disproportionality Signals"
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    logger.info(f"Saved signal table plot to {output_path}")
    return output_path

def plot_ror_distribution(
    signals_df: pd.DataFrame,
    output_path: Union[str, Path],
    metric: str = 'ror',
    threshold: Optional[float] = None
) -> Path:
    """
    Generate a histogram of ROR (or other metric) distribution.
    
    Args:
        signals_df: DataFrame containing signal metrics.
        output_path: Path to save the generated PNG file.
        metric: Metric column to plot (default: 'ror').
        threshold: Optional vertical line to indicate a threshold.
        
    Returns:
        Path to the saved figure.
    """
    if not isinstance(output_path, Path):
        output_path = Path(output_path)
        
    _ensure_output_dir(output_path)
    
    if signals_df.empty:
        raise ValueError("Signals DataFrame is empty. Cannot generate distribution plot.")
    
    if metric not in signals_df.columns:
        raise ValueError(f"Metric column '{metric}' not found in DataFrame.")
    
    values = signals_df[metric].dropna()
    if values.empty:
        raise ValueError(f"No valid values found for metric '{metric}'.")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.hist(values, bins=30, color='#1f77b4', alpha=0.7, edgecolor='black')
    ax.set_xlabel(f'{metric.upper()} Value', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title(f'Distribution of {metric.upper()} for All SOCs', fontsize=14, fontweight='bold')
    ax.grid(True, linestyle='--', alpha=0.5)
    
    if threshold is not None:
        ax.axvline(x=threshold, color='red', linestyle='--', linewidth=2, label=f'Threshold: {threshold}')
        ax.legend()
    
    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    logger.info(f"Saved {metric} distribution plot to {output_path}")
    return output_path

def plot_sensitivity_comparison(
    sensitivity_df: pd.DataFrame,
    output_path: Union[str, Path],
    top_n: int = 5
) -> Path:
    """
    Generate a bar chart comparing metrics between baselines for top signals.
    
    Args:
        sensitivity_df: DataFrame containing sensitivity analysis results.
        output_path: Path to save the generated PNG file.
        top_n: Number of top signals to display.
        
    Returns:
        Path to the saved figure.
    """
    if not isinstance(output_path, Path):
        output_path = Path(output_path)
        
    _ensure_output_dir(output_path)
    
    if sensitivity_df.empty:
        raise ValueError("Sensitivity DataFrame is empty. Cannot generate comparison plot.")
    
    # Assume 'soc' and 'ror_delta' or similar delta columns exist
    if 'soc' not in sensitivity_df.columns:
        raise ValueError("Sensitivity DataFrame missing 'soc' column.")
        
    # Select top N by absolute delta of a primary metric (e.g., ror_delta)
    delta_col = 'ror_delta' if 'ror_delta' in sensitivity_df.columns else sensitivity_df.columns[2]
    
    top_socs = sensitivity_df.nlargest(top_n, delta_col.abs())['soc'].tolist()
    plot_df = sensitivity_df[sensitivity_df['soc'].isin(top_socs)]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Pivot for plotting if necessary, or iterate
    # Assuming long format: soc, metric_delta, baseline_type
    # If wide format, handle accordingly. Let's assume we plot ROR delta per SOC.
    
    # Simplified: Plot ROR delta for each SOC if available
    if 'ror_delta' in plot_df.columns:
        x = range(len(plot_df))
        ax.bar(x, plot_df['ror_delta'], color=['#ff7f0e' if v > 0 else '#2ca02c' for v in plot_df['ror_delta']])
        ax.set_xticks(x)
        ax.set_xticklabels(plot_df['soc'], rotation=45, ha='right')
        ax.set_ylabel('ROR Delta (Primary - Flu)')
        ax.set_title('Sensitivity Analysis: ROR Delta for Top Signals')
        ax.axhline(0, color='black', linewidth=0.8)
    else:
        # Fallback: generic plot
        ax.plot(plot_df['soc'], plot_df.iloc[:, 2], marker='o')
        ax.set_xticklabels(plot_df['soc'], rotation=45, ha='right')
        ax.set_title('Sensitivity Comparison')
    
    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    logger.info(f"Saved sensitivity comparison plot to {output_path}")
    return output_path

def create_summary_dashboard(
    signals_df: pd.DataFrame,
    weekly_plots_dir: Path,
    output_path: Union[str, Path],
    top_n: int = 5
) -> Path:
    """
    Create a summary dashboard figure combining key visualizations.
    
    Args:
        signals_df: DataFrame containing signal metrics.
        weekly_plots_dir: Directory containing weekly count plots.
        output_path: Path to save the combined dashboard PNG.
        top_n: Number of top signals to include in the dashboard.
        
    Returns:
        Path to the saved figure.
    """
    if not isinstance(output_path, Path):
        output_path = Path(output_path)
        
    _ensure_output_dir(output_path)
    
    fig = plt.figure(figsize=(20, 12))
    
    # 1. Signal Table (Top 5)
    ax1 = fig.add_subplot(2, 2, 1)
    ax1.axis('off')
    if not signals_df.empty:
        top_signals = signals_df.sort_values(by='ror', ascending=False).head(top_n)
        display_cols = ['soc', 'ror', 'prr', 'ic', 'signal_flag']
        available_cols = [c for c in display_cols if c in top_signals.columns]
        if available_cols:
            table_data = top_signals[available_cols].values
            col_labels = [c.upper() for c in available_cols]
            table = ax1.table(
                cellText=table_data,
                colLabels=col_labels,
                loc='center',
                cellLoc='center',
                colColours=['#d9edf7'] * len(available_cols)
            )
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1.1, 1.4)
            ax1.set_title('Top Signals Summary', fontsize=12, fontweight='bold', pad=10)
    
    # 2. ROR Distribution
    ax2 = fig.add_subplot(2, 2, 2)
    if not signals_df.empty and 'ror' in signals_df.columns:
        ax2.hist(signals_df['ror'].dropna(), bins=20, color='#1f77b4', alpha=0.7, edgecolor='black')
        ax2.set_xlabel('ROR Value')
        ax2.set_ylabel('Frequency')
        ax2.set_title('ROR Distribution', fontsize=12, fontweight='bold')
        ax2.grid(True, linestyle='--', alpha=0.5)
    
    # 3. Placeholder for Temporal Profile (if plots exist)
    ax3 = fig.add_subplot(2, 2, 3)
    ax3.axis('off')
    if weekly_plots_dir.exists():
        plot_files = list(weekly_plots_dir.glob('*.png'))
        if plot_files:
            # Just list the files found or show a thumbnail if possible (simplified here)
            ax3.text(0.5, 0.5, f"Found {len(plot_files)} Weekly Plots\nin {weekly_plots_dir.name}",
                     ha='center', va='center', fontsize=12, transform=ax3.transAxes)
            ax3.set_title('Temporal Profiles Available', fontsize=12, fontweight='bold')
        else:
            ax3.text(0.5, 0.5, "No Weekly Plots Found", ha='center', va='center', fontsize=12, transform=ax3.transAxes)
    else:
        ax3.text(0.5, 0.5, "Weekly Plots Directory Not Found", ha='center', va='center', fontsize=12, transform=ax3.transAxes)
    
    # 4. Signal Flag Count
    ax4 = fig.add_subplot(2, 2, 4)
    if not signals_df.empty and 'signal_flag' in signals_df.columns:
        signal_counts = signals_df['signal_flag'].value_counts()
        ax4.bar(['Signal', 'No Signal'], signal_counts.values, color=['#ff7f0e', '#2ca02c'])
        ax4.set_ylabel('Count')
        ax4.set_title('Signal Detection Summary', fontsize=12, fontweight='bold')
        for i, v in enumerate(signal_counts.values):
            ax4.text(i, v + 0.1, str(v), ha='center')
    
    plt.suptitle('COVID-19 VAERS Statistical Analysis Dashboard', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    logger.info(f"Saved summary dashboard to {output_path}")
    return output_path

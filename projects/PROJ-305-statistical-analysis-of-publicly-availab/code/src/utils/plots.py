"""
Visualization utilities for the COVID-19 VAERS statistical analysis pipeline.

This module provides helper functions for generating matplotlib figures, including:
- Weekly reporting counts for specific System Organ Classes (SOCs)
- Signal summary tables
- ROR distribution histograms
- Sensitivity analysis comparisons
- Summary dashboards
"""
import os
import warnings
from pathlib import Path
from typing import List, Optional, Dict, Any, Union

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Configure matplotlib for non-interactive backend (essential for headless servers)
matplotlib.use('Agg')

# Ensure plots directory exists
PLOTS_DIR = Path("output/temporal_profiles")
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

# Style settings for consistent visual output
plt.style.use('seaborn-v0_8-whitegrid')
FONT_SIZE = 12
TITLE_SIZE = 14
LABEL_SIZE = 11

def _ensure_dir(filepath: Path) -> None:
    """Ensure the directory for a file path exists."""
    filepath.parent.mkdir(parents=True, exist_ok=True)

def plot_weekly_counts(
    df: pd.DataFrame,
    soc_name: str,
    output_path: Optional[Path] = None,
    date_col: str = "REPT_DATE",
    count_col: str = "count"
) -> Path:
    """
    Generate a weekly count plot for a specific SOC.

    Args:
        df: DataFrame containing weekly aggregated data with 'REPT_DATE' and count columns.
        soc_name: Name of the System Organ Class for the plot title.
        output_path: Optional path to save the figure. If None, saved to output/temporal_profiles/
        date_col: Column name for dates.
        count_col: Column name for counts.

    Returns:
        Path to the saved figure file.
    """
    if df.empty:
        raise ValueError(f"Cannot plot weekly counts for {soc_name}: DataFrame is empty.")

    if output_path is None:
        # Sanitize filename
        safe_name = "".join(c for c in soc_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        output_path = PLOTS_DIR / f"weekly_counts_{safe_name}.png"
    
    _ensure_dir(output_path)

    fig, ax = plt.subplots(figsize=(12, 6))

    # Ensure date column is datetime
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df_plot = df.copy()
        df_plot[date_col] = pd.to_datetime(df_plot[date_col], errors='coerce')
        df_plot = df_plot.dropna(subset=[date_col])
        df_plot = df_plot.sort_values(by=date_col)
    else:
        df_plot = df.sort_values(by=date_col)

    ax.plot(df_plot[date_col], df_plot[count_col], marker='o', linestyle='-', color='#2c7bb6', linewidth=2, markersize=6)

    ax.set_title(f"Weekly Reporting Counts: {soc_name}", fontsize=TITLE_SIZE, fontweight='bold')
    ax.set_xlabel("Reporting Date", fontsize=LABEL_SIZE)
    ax.set_ylabel("Number of Reports", fontsize=LABEL_SIZE)
    
    # Format x-axis dates
    fig.autofmt_xdate()
    
    ax.tick_params(axis='both', which='major', labelsize=FONT_SIZE)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    return output_path

def plot_signal_table(
    signals_df: pd.DataFrame,
    output_path: Optional[Path] = None,
    metrics: List[str] = ['ror', 'prr', 'ic'],
    top_n: int = 10
) -> Path:
    """
    Generate a static image of the top N signals table.

    Args:
        signals_df: DataFrame containing signal metrics.
        output_path: Optional path to save the figure.
        metrics: List of metrics to display.
        top_n: Number of top signals to display (sorted by ROR descending).

    Returns:
        Path to the saved figure file.
    """
    if output_path is None:
        output_path = PLOTS_DIR / "top_signals_table.png"
    
    _ensure_dir(output_path)

    # Prepare data
    display_df = signals_df.copy()
    if 'ror' in display_df.columns:
        display_df = display_df.sort_values(by='ror', ascending=False)
    
    display_df = display_df.head(top_n)
    
    # Select columns
    cols_to_show = ['soc'] + [m for m in metrics if m in display_df.columns]
    if 'signal_flag' in display_df.columns:
        cols_to_show.append('signal_flag')
    
    if len(cols_to_show) > len(display_df.columns):
        # Fallback if columns missing
        cols_to_show = [c for c in cols_to_show if c in display_df.columns]

    fig, ax = plt.subplots(figsize=(14, max(6, len(display_df) * 0.5 + 2)))
    ax.axis('off')
    
    # Create table
    table = ax.table(
        cellText=display_df[cols_to_show].values,
        colLabels=cols_to_show,
        cellLoc='center',
        loc='center',
        colColours=['#d7191c'] * len(cols_to_show)
    )
    table.auto_set_font_size(False)
    table.set_fontsize(FONT_SIZE)
    table.scale(1.2, 1.5)
    
    # Style header
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold', color='white')
            cell.set_facecolor('#2c7bb6')
        elif row > 0:
            # Alternate row colors
            if row % 2 == 0:
                cell.set_facecolor('#f7f7f7')
            else:
                cell.set_facecolor('white')
            
            # Highlight signals
            if 'signal_flag' in cols_to_show:
                sig_idx = cols_to_show.index('signal_flag')
                if col == sig_idx:
                    val = display_df.iloc[row-1, sig_idx]
                    if val:
                        cell.set_facecolor('#ffff99') # Yellow highlight for signals

    ax.set_title(f"Top {top_n} Disproportionality Signals", fontsize=TITLE_SIZE, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    return output_path

def plot_ror_distribution(
    signals_df: pd.DataFrame,
    output_path: Optional[Path] = None,
    metric: str = 'ror'
) -> Path:
    """
    Generate a histogram of ROR (or other metric) distribution.

    Args:
        signals_df: DataFrame containing signal metrics.
        output_path: Optional path to save the figure.
        metric: The metric to plot (e.g., 'ror', 'prr', 'ic').

    Returns:
        Path to the saved figure file.
    """
    if metric not in signals_df.columns:
        raise ValueError(f"Metric '{metric}' not found in DataFrame columns.")
    
    if output_path is None:
        output_path = PLOTS_DIR / f"{metric}_distribution.png"
    
    _ensure_dir(output_path)

    fig, ax = plt.subplots(figsize=(10, 6))

    values = signals_df[metric].dropna()
    if len(values) == 0:
        ax.text(0.5, 0.5, 'No data available for distribution', transform=ax.transAxes, ha='center', va='center')
    else:
        ax.hist(values, bins=30, color='#2c7bb6', alpha=0.7, edgecolor='black')
        ax.set_xlabel(metric.upper(), fontsize=LABEL_SIZE)
        ax.set_ylabel('Frequency', fontsize=LABEL_SIZE)
        ax.set_title(f'Distribution of {metric.upper()} Values', fontsize=TITLE_SIZE, fontweight='bold')
        
        # Add threshold line if ROR
        if metric == 'ror':
            ax.axvline(x=2.0, color='red', linestyle='--', label='Threshold (2.0)')
            ax.legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    return output_path

def plot_sensitivity_comparison(
    sensitivity_df: pd.DataFrame,
    soc: str,
    output_path: Optional[Path] = None
) -> Path:
    """
    Plot sensitivity analysis deltas for a specific SOC.

    Args:
        sensitivity_df: DataFrame containing sensitivity analysis results.
        soc: The SOC name to plot.
        output_path: Optional path to save the figure.

    Returns:
        Path to the saved figure file.
    """
    if output_path is None:
        safe_soc = "".join(c for c in soc if c.isalnum() or c in (' ', '-', '_')).rstrip()
        output_path = PLOTS_DIR / f"sensitivity_{safe_soc}.png"
    
    _ensure_dir(output_path)

    # Filter data
    df_plot = sensitivity_df[sensitivity_df['soc'] == soc]
    
    if df_plot.empty:
        raise ValueError(f"No sensitivity data found for SOC: {soc}")

    fig, ax = plt.subplots(figsize=(10, 6))

    # Assuming columns: ror_delta, prr_delta, ic_delta
    metrics = ['ror_delta', 'prr_delta', 'ic_delta']
    available_metrics = [m for m in metrics if m in df_plot.columns]
    
    if not available_metrics:
        ax.text(0.5, 0.5, 'No delta metrics available', transform=ax.transAxes, ha='center', va='center')
    else:
        # Group by baseline type
        baselines = df_plot['baseline_type'].unique()
        x = np.arange(len(available_metrics))
        width = 0.25
        
        for i, baseline in enumerate(baselines):
            subset = df_plot[df_plot['baseline_type'] == baseline]
            values = [subset[m].values[0] if m in subset.columns else 0 for m in available_metrics]
            ax.bar(x + i * width, values, width, label=baseline)
        
        ax.set_xticks(x + width)
        ax.set_xticklabels([m.replace('_delta', '').upper() for m in available_metrics])
        ax.set_ylabel('Delta Value', fontsize=LABEL_SIZE)
        ax.set_title(f'Sensitivity Analysis: {soc}', fontsize=TITLE_SIZE, fontweight='bold')
        ax.legend()
        ax.axhline(0, color='black', linewidth=0.8)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    return output_path

def create_summary_dashboard(
    signals_df: pd.DataFrame,
    top_socs: List[str],
    temporal_data: Dict[str, pd.DataFrame],
    output_path: Optional[Path] = None
) -> Path:
    """
    Create a multi-panel summary dashboard.

    Args:
        signals_df: DataFrame with signal metrics.
        top_socs: List of top SOC names to include.
        temporal_data: Dictionary mapping SOC name to their weekly dataframes.
        output_path: Optional path to save the figure.

    Returns:
        Path to the saved figure file.
    """
    if output_path is None:
        output_path = PLOTS_DIR / "summary_dashboard.png"
    
    _ensure_dir(output_path)

    n = len(top_socs)
    if n == 0:
        # Create a warning figure
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.text(0.5, 0.5, 'No top SOCs available for dashboard', transform=ax.transAxes, ha='center', va='center', fontsize=16)
        ax.axis('off')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        return output_path

    # Grid layout: 1 row, n columns (or adjust based on count)
    cols = min(n, 4)
    rows = (n + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 3 * rows))
    if rows == 1 and cols == 1:
        axes = np.array([[axes]])
    elif rows == 1:
        axes = axes.reshape(1, -1)
    elif cols == 1:
        axes = axes.reshape(-1, 1)

    axes = axes.flatten()

    for i, soc in enumerate(top_socs):
        if i >= len(axes):
            break
        
        ax = axes[i]
        
        # Plot ROR vs PRR scatter for this SOC if possible, or just a bar chart of metrics
        # Since we only have one row per SOC in signals_df, we can't scatter.
        # Instead, plot the metrics as a bar chart
        
        row_data = signals_df[signals_df['soc'] == soc]
        if row_data.empty:
            ax.text(0.5, 0.5, f'No data for {soc}', transform=ax.transAxes, ha='center', va='center')
            continue

        metrics = ['ror', 'prr', 'ic']
        values = []
        labels = []
        
        for m in metrics:
            if m in row_data.columns:
                val = row_data[m].values[0]
                if pd.notna(val) and np.isfinite(val):
                    values.append(val)
                    labels.append(m.upper())
        
        if values:
            ax.bar(labels, values, color=['#2c7bb6', '#fca311', '#14213d'])
            ax.set_title(f"{soc}", fontsize=TITLE_SIZE)
            ax.set_ylabel("Value")
            if 'ror' in labels and values[0] > 0:
                ax.axhline(y=2.0, color='red', linestyle='--', alpha=0.5, label='ROR Thresh')
                ax.legend(fontsize=8)
        else:
            ax.text(0.5, 0.5, 'No metrics', transform=ax.transAxes, ha='center', va='center')

    # Hide unused subplots
    for j in range(i + 1, len(axes)):
        axes[j].axis('off')

    plt.suptitle("Summary Dashboard: Top Signals", fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    return output_path

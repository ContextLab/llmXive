"""
Plotting utilities for the VAERS Statistical Analysis pipeline.

Generates matplotlib figures for:
- Weekly reporting counts (temporal profiles)
- Signal tables (disproportionality metrics)
- ROR distributions
- Sensitivity analysis comparisons
- Summary dashboards
"""
import os
import warnings
from pathlib import Path
from typing import List, Optional, Dict, Any, Union

import matplotlib
# Use non-interactive backend for headless execution
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Ensure output directories exist
OUTPUT_DIR = Path("code/output/temporal_profiles")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Style configuration
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.size'] = 10
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['savefig.bbox'] = 'tight'


def plot_weekly_counts(
    df: pd.DataFrame,
    soc_code: str,
    group_col: str = 'VAX_TYPE',
    output_path: Optional[Path] = None
) -> Path:
    """
    Generate a weekly count plot for a specific SOC code.
    
    Args:
        df: Cleaned dataframe with 'REPT_DATE' and 'SOC_CODE' columns.
        soc_code: The SOC code to filter for.
        group_col: Column name for grouping (e.g., 'VAX_TYPE').
        output_path: Where to save the figure. Defaults to output/temporal_profiles/.
    
    Returns:
        Path to the saved figure.
    """
    if output_path is None:
        output_path = OUTPUT_DIR / f"weekly_counts_{soc_code}.png"
    
    # Filter data
    filtered_df = df[df['SOC_CODE'] == soc_code].copy()
    if filtered_df.empty:
        warnings.warn(f"No data found for SOC {soc_code}, creating empty plot.")
    
    # Parse dates and compute week number relative to median
    filtered_df['REPT_DATE'] = pd.to_datetime(filtered_df['REPT_DATE'], errors='coerce')
    filtered_df = filtered_df.dropna(subset=['REPT_DATE'])
    
    if filtered_df.empty:
        # Create empty plot if no valid dates
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, 'No Data Available', ha='center', va='center', transform=ax.transAxes)
        ax.set_title(f"Weekly Counts for SOC {soc_code}")
        fig.savefig(output_path)
        plt.close(fig)
        return Path(output_path)
    
    median_date = filtered_df['REPT_DATE'].median()
    filtered_df['WEEKS_RELATIVE'] = (filtered_df['REPT_DATE'] - median_date).dt.days / 7
    filtered_df['WEEK'] = filtered_df['WEEKS_RELATIVE'].round()
    
    # Aggregate by week and group
    weekly_counts = filtered_df.groupby(['WEEK', group_col]).size().unstack(fill_value=0)
    
    # Plot
    fig, ax = plt.subplots()
    weekly_counts.plot(ax=ax, marker='o', linestyle='-')
    
    ax.set_xlabel('Weeks Relative to Median Report Date')
    ax.set_ylabel('Number of Reports')
    ax.set_title(f"Weekly Reporting Counts: SOC {soc_code}\n(Label: Reporting Time, not Post-Vaccination)")
    ax.legend(title=group_col)
    
    # Add disclaimer text
    disclaimer = "Note: Temporal analysis is descriptive. 'Reporting Time' ≠ 'Post-Vaccination Time'."
    fig.text(0.5, -0.15, disclaimer, ha='center', fontsize=8, style='italic')
    
    fig.savefig(output_path)
    plt.close(fig)
    
    return Path(output_path)


def plot_signal_table(
    df: pd.DataFrame,
    metrics: List[str] = ['ROR', 'PRR', 'IC'],
    threshold: Dict[str, float] = None,
    output_path: Optional[Path] = None
) -> Path:
    """
    Generate a heatmap-style visualization of signal metrics for top SOCs.
    
    Args:
        df: DataFrame containing signal metrics (SOC_CODE, ROR, PRR, IC, etc.).
        metrics: List of metric columns to visualize.
        threshold: Dictionary mapping metric names to significance thresholds.
        output_path: Where to save the figure.
    
    Returns:
        Path to the saved figure.
    """
    if output_path is None:
        output_path = OUTPUT_DIR / "signal_table.png"
    
    if df.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, 'No Signal Data', ha='center', va='center', transform=ax.transAxes)
        fig.savefig(output_path)
        plt.close(fig)
        return Path(output_path)
    
    # Select relevant columns
    plot_data = df[['SOC_CODE'] + [m for m in metrics if m in df.columns]].copy()
    plot_data.set_index('SOC_CODE', inplace=True)
    
    # Normalize for visualization (0 to 1) if thresholds exist
    if threshold:
        for metric in metrics:
            if metric in plot_data.columns and metric in threshold:
                thresh = threshold[metric]
                # Cap at 2x threshold for visualization
                max_val = max(plot_data[metric].max(), thresh * 2)
                plot_data[metric] = plot_data[metric].clip(0, max_val) / max_val
    
    # Create heatmap
    fig, ax = plt.subplots(figsize=(10, len(plot_data) * 0.5 + 2))
    
    # Use matplotlib table directly for precise control
    table_data = plot_data.reset_index().values
    col_labels = plot_data.columns.tolist()
    row_labels = plot_data.reset_index()['SOC_CODE'].tolist()
    
    table = ax.table(
        cellText=table_data,
        colLabels=col_labels,
        rowLabels=row_labels,
        cellLoc='center',
        loc='center'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.2, 1.5)
    
    # Highlight significant signals (if thresholds provided)
    if threshold:
        for i, row in enumerate(plot_data.reset_index().itertuples(index=False)):
            for j, metric in enumerate(col_labels):
                if metric in threshold and metric != 'SOC_CODE':
                    val = getattr(row, metric, 0)
                    thresh = threshold[metric]
                    # Simple logic: if value > threshold, make cell green
                    # Adjust for normalized values if normalized
                    if metric in threshold and val > thresh:
                        table[(i+1, j+1)].set_facecolor('#d4edda')
    
    ax.set_title('Signal Detection Metrics Table')
    ax.axis('off')
    
    fig.savefig(output_path)
    plt.close(fig)
    
    return Path(output_path)


def plot_ror_distribution(
    df: pd.DataFrame,
    metric: str = 'ROR',
    output_path: Optional[Path] = None
) -> Path:
    """
    Plot the distribution of a disproportionality metric (e.g., ROR) across SOCs.
    
    Args:
        df: DataFrame with metric columns.
        metric: Column name for the metric.
        output_path: Where to save the figure.
    
    Returns:
        Path to the saved figure.
    """
    if output_path is None:
        output_path = OUTPUT_DIR / f"{metric}_distribution.png"
    
    if metric not in df.columns:
        warnings.warn(f"Metric {metric} not found in dataframe.")
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, f'Metric {metric} not found', ha='center', va='center')
        fig.savefig(output_path)
        plt.close(fig)
        return Path(output_path)
    
    values = df[metric].dropna()
    if values.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, 'No data for distribution', ha='center', va='center')
        fig.savefig(output_path)
        plt.close(fig)
        return Path(output_path)
    
    fig, ax = plt.subplots()
    ax.hist(values, bins=30, color='skyblue', edgecolor='black', alpha=0.7)
    ax.set_xlabel(metric)
    ax.set_ylabel('Frequency')
    ax.set_title(f'Distribution of {metric} Across SOCs')
    ax.axvline(x=2.0, color='red', linestyle='--', label='Threshold (2.0)')
    ax.legend()
    
    fig.savefig(output_path)
    plt.close(fig)
    
    return Path(output_path)


def plot_sensitivity_comparison(
    df_primary: pd.DataFrame,
    df_sensitivity: pd.DataFrame,
    metrics: List[str] = ['ROR', 'PRR', 'IC'],
    output_path: Optional[Path] = None
) -> Path:
    """
    Compare metrics between primary and sensitivity baselines.
    
    Args:
        df_primary: DataFrame with primary baseline metrics.
        df_sensitivity: DataFrame with sensitivity baseline metrics.
        metrics: List of metrics to compare.
        output_path: Where to save the figure.
    
    Returns:
        Path to the saved figure.
    """
    if output_path is None:
        output_path = OUTPUT_DIR / "sensitivity_comparison.png"
    
    # Merge on SOC_CODE
    if 'SOC_CODE' not in df_primary.columns or 'SOC_CODE' not in df_sensitivity.columns:
        warnings.warn("SOC_CODE column missing in one of the dataframes.")
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, 'Dataframe merge failed', ha='center', va='center')
        fig.savefig(output_path)
        plt.close(fig)
        return Path(output_path)
    
    merged = pd.merge(
        df_primary[['SOC_CODE'] + metrics],
        df_sensitivity[['SOC_CODE'] + metrics],
        on='SOC_CODE',
        suffixes=('_primary', '_sens')
    )
    
    if merged.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, 'No overlapping SOCs', ha='center', va='center')
        fig.savefig(output_path)
        plt.close(fig)
        return Path(output_path)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    x = np.arange(len(metrics))
    width = 0.35
    
    for i, metric in enumerate(metrics):
        primary_vals = merged[f'{metric}_primary'].values
        sens_vals = merged[f'{metric}_sens'].values
        
        ax.bar(x - width/2 + i*width, primary_vals, width, label=f'{metric}_Primary')
        ax.bar(x + width/2 + i*width, sens_vals, width, label=f'{metric}_Sensitivity')
    
    ax.set_ylabel('Metric Value')
    ax.set_title('Sensitivity Analysis: Primary vs. Non-COVID, Non-Flu Baseline')
    ax.set_xticks(x)
    ax.set_xticklabels(metrics)
    ax.legend()
    
    fig.savefig(output_path)
    plt.close(fig)
    
    return Path(output_path)


def create_summary_dashboard(
    df_signals: pd.DataFrame,
    df_temporal: Optional[pd.DataFrame] = None,
    output_path: Optional[Path] = None
) -> Path:
    """
    Create a multi-panel dashboard summarizing key findings.
    
    Args:
        df_signals: DataFrame with signal metrics.
        df_temporal: Optional DataFrame with temporal data.
        output_path: Where to save the figure.
    
    Returns:
        Path to the saved figure.
    """
    if output_path is None:
        output_path = OUTPUT_DIR / "summary_dashboard.png"
    
    fig = plt.figure(figsize=(15, 12))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
    
    # Panel 1: Top Signals Table (Heatmap style)
    ax1 = fig.add_subplot(gs[0, 0])
    if not df_signals.empty:
        top_signals = df_signals.sort_values('ROR', ascending=False).head(10)
        table_data = top_signals[['SOC_CODE', 'ROR', 'PRR', 'IC', 'Signal_Flag']].values
        col_labels = ['SOC', 'ROR', 'PRR', 'IC', 'Signal']
        row_labels = [f"Top {i+1}" for i in range(len(table_data))]
        
        table = ax1.table(
            cellText=table_data,
            colLabels=col_labels,
            rowLabels=row_labels,
            cellLoc='center',
            loc='center'
        )
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1.1, 1.4)
        
        # Color code signals
        for i, row in enumerate(top_signals.itertuples(index=False)):
            if hasattr(row, 'Signal_Flag') and row.Signal_Flag == True:
                for j in range(1, 5): # Skip SOC column
                    table[(i+1, j)].set_facecolor('#d4edda')
    
    ax1.axis('off')
    ax1.set_title('Top 10 Candidate Signals (Sorted by ROR)', pad=20)
    
    # Panel 2: ROR Distribution
    ax2 = fig.add_subplot(gs[0, 1])
    if 'ROR' in df_signals.columns:
        ror_vals = df_signals['ROR'].dropna()
        ax2.hist(ror_vals, bins=30, color='lightcoral', edgecolor='black', alpha=0.7)
        ax2.axvline(x=2.0, color='red', linestyle='--', label='Threshold (2.0)')
        ax2.set_xlabel('ROR')
        ax2.set_ylabel('Frequency')
        ax2.set_title('Distribution of Reporting Odds Ratios')
        ax2.legend()
    
    # Panel 3: IC Distribution
    ax3 = fig.add_subplot(gs[1, 0])
    if 'IC' in df_signals.columns:
        ic_vals = df_signals['IC'].dropna()
        ax3.hist(ic_vals, bins=30, color='lightgreen', edgecolor='black', alpha=0.7)
        ax3.axvline(x=0.0, color='red', linestyle='--', label='Threshold (0.0)')
        ax3.set_xlabel('Information Component')
        ax3.set_ylabel('Frequency')
        ax3.set_title('Distribution of Information Components')
        ax3.legend()
    
    # Panel 4: Signal Count Summary
    ax4 = fig.add_subplot(gs[1, 1])
    if not df_signals.empty:
        signal_counts = df_signals['Signal_Flag'].value_counts()
        labels = ['Signal', 'No Signal']
        sizes = [signal_counts.get(True, 0), signal_counts.get(False, 0)]
        colors = ['#d4edda', '#f8d7da']
        ax4.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
        ax4.set_title('Signal Detection Summary')
    
    plt.suptitle('VAERS Statistical Analysis Summary Dashboard', fontsize=16, fontweight='bold')
    fig.savefig(output_path)
    plt.close(fig)
    
    return Path(output_path)

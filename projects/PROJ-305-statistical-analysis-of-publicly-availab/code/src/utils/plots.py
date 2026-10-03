import os
import warnings
from pathlib import Path
from typing import List, Optional, Dict, Any, Union

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Ensure non-interactive backend for server environments
if matplotlib.get_backend().lower() == 'agg' or os.environ.get('DISPLAY') is None:
    matplotlib.use('Agg')

# Constants for styling
FIG_WIDTH = 10
FIG_HEIGHT = 6
DPI = 100
FONT_SIZE = 10
TICK_SIZE = 8

def plot_weekly_counts(
    data: pd.DataFrame,
    output_path: Union[str, Path],
    group_col: str = 'VAX_TYPE',
    date_col: str = 'REPT_DATE',
    title_suffix: str = '',
    soc_filter: Optional[str] = None
) -> None:
    """
    Generate a weekly count plot of reports.

    Args:
        data: DataFrame containing report data with date and group columns.
        output_path: Path to save the generated PNG file.
        group_col: Column name for grouping (e.g., 'VAX_TYPE').
        date_col: Column name for dates (e.g., 'REPT_DATE').
        title_suffix: Optional text to append to the plot title.
        soc_filter: If provided, filter data to this SOC before plotting.
    """
    plot_data = data.copy()

    if soc_filter:
        plot_data = plot_data[plot_data['SOC'] == soc_filter]

    if plot_data.empty:
        warnings.warn(f"No data available for plotting with SOC filter: {soc_filter}")
        # Create a placeholder image or empty plot
        fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT))
        ax.text(0.5, 0.5, "No Data Available", ha='center', va='center', transform=ax.transAxes)
        ax.set_title(f"Weekly Counts - {title_suffix}")
        plt.savefig(output_path, dpi=DPI)
        plt.close(fig)
        return

    # Ensure date column is datetime
    if not pd.api.types.is_datetime64_any_dtype(plot_data[date_col]):
        plot_data[date_col] = pd.to_datetime(plot_data[date_col], errors='coerce')
        plot_data = plot_data.dropna(subset=[date_col])

    if plot_data.empty:
        warnings.warn("No valid dates found after conversion.")
        fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT))
        ax.text(0.5, 0.5, "No Valid Dates", ha='center', va='center', transform=ax.transAxes)
        plt.savefig(output_path, dpi=DPI)
        plt.close(fig)
        return

    # Extract week and year for grouping
    plot_data['Week'] = plot_data[date_col].dt.to_period('W').dt.to_timestamp()

    # Group by week and group_col
    weekly_counts = plot_data.groupby([plot_data['Week'], group_col]).size().unstack(fill_value=0)

    # Ensure all expected groups are present if we know them, otherwise just use what's there
    # Plotting
    fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT))

    # Plot each group
    for col in weekly_counts.columns:
        ax.plot(weekly_counts.index, weekly_counts[col], label=col, marker='o', markersize=4)

    ax.set_xlabel("Reporting Week")
    ax.set_ylabel("Number of Reports")
    title = f"Weekly Report Counts {title_suffix}"
    if soc_filter:
        title += f" (SOC: {soc_filter})"
    ax.set_title(title)
    ax.legend(loc='upper left')
    ax.grid(True, linestyle='--', alpha=0.7)

    # Rotate x-axis labels for readability
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=DPI)
    plt.close(fig)

def plot_signal_table(
    signals_df: pd.DataFrame,
    output_path: Union[str, Path],
    top_n: int = 10
) -> None:
    """
    Generate a static image of the top N signals table.

    Args:
        signals_df: DataFrame containing signal metrics (ROR, PRR, IC, etc.).
        output_path: Path to save the generated PNG file.
        top_n: Number of top signals to display.
    """
    if signals_df.empty:
        warnings.warn("Signals DataFrame is empty.")
        fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT))
        ax.text(0.5, 0.5, "No Signals Detected", ha='center', va='center', transform=ax.transAxes)
        plt.savefig(output_path, dpi=DPI)
        plt.close(fig)
        return

    # Sort by signal strength (e.g., ROR or IC) - default to ROR if available
    sort_col = 'ror' if 'ror' in signals_df.columns else 'ic'
    sorted_signals = signals_df.sort_values(by=sort_col, ascending=False).head(top_n)

    # Prepare data for table
    # Select relevant columns for the table
    cols_to_show = ['soc', sort_col, 'ror_ci_lower', 'ror_ci_upper', 'signal_flag']
    # Filter columns that exist
    cols_to_show = [c for c in cols_to_show if c in sorted_signals.columns]

    if not cols_to_show:
        warnings.warn("No relevant columns found for table display.")
        fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT))
        ax.text(0.5, 0.5, "No Columns to Display", ha='center', va='center', transform=ax.transAxes)
        plt.savefig(output_path, dpi=DPI)
        plt.close(fig)
        return

    table_data = sorted_signals[cols_to_show]

    fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT))
    ax.axis('off')

    # Create table
    table = ax.table(
        cellText=table_data.values,
        colLabels=table_data.columns,
        loc='center',
        cellLoc='center'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(FONT_SIZE)
    table.scale(1, 1.5)

    title = f"Top {top_n} Disproportionality Signals"
    ax.set_title(title, fontsize=14, pad=20)

    plt.savefig(output_path, dpi=DPI, bbox_inches='tight')
    plt.close(fig)

def plot_ror_distribution(
    signals_df: pd.DataFrame,
    output_path: Union[str, Path],
    threshold: float = 2.0
) -> None:
    """
    Generate a histogram of ROR values with a threshold line.

    Args:
        signals_df: DataFrame containing signal metrics.
        output_path: Path to save the generated PNG file.
        threshold: The ROR threshold to highlight.
    """
    if signals_df.empty or 'ror' not in signals_df.columns:
        warnings.warn("No ROR data available for distribution plot.")
        fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT))
        ax.text(0.5, 0.5, "No ROR Data", ha='center', va='center', transform=ax.transAxes)
        plt.savefig(output_path, dpi=DPI)
        plt.close(fig)
        return

    fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT))

    # Filter finite values
    ror_values = signals_df['ror'].replace([np.inf, -np.inf], np.nan).dropna()

    ax.hist(ror_values, bins=30, color='skyblue', edgecolor='black', alpha=0.7)
    ax.axvline(x=threshold, color='red', linestyle='--', linewidth=2, label=f'Threshold ({threshold})')
    ax.set_xlabel("Reporting Odds Ratio (ROR)")
    ax.set_ylabel("Frequency")
    ax.set_title("Distribution of Reporting Odds Ratios")
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.5)

    plt.savefig(output_path, dpi=DPI)
    plt.close(fig)

def plot_sensitivity_comparison(
    data: pd.DataFrame,
    output_path: Union[str, Path],
    soc_list: List[str],
    baseline_col: str = 'baseline_type'
) -> None:
    """
    Generate a bar chart comparing metrics between baselines for specific SOCs.

    Args:
        data: DataFrame containing sensitivity analysis results.
        output_path: Path to save the generated PNG file.
        soc_list: List of SOC names to plot.
        baseline_col: Column name indicating the baseline type.
    """
    if data.empty or not soc_list:
        warnings.warn("No data or SOC list provided for sensitivity comparison.")
        fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT))
        ax.text(0.5, 0.5, "No Data for Comparison", ha='center', va='center', transform=ax.transAxes)
        plt.savefig(output_path, dpi=DPI)
        plt.close(fig)
        return

    plot_data = data[data['soc'].isin(soc_list)]

    if plot_data.empty:
        warnings.warn(f"No data found for SOCs: {soc_list}")
        fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT))
        ax.text(0.5, 0.5, f"No data for {soc_list}", ha='center', va='center', transform=ax.transAxes)
        plt.savefig(output_path, dpi=DPI)
        plt.close(fig)
        return

    # Pivot for plotting
    # Assuming 'metric' column exists or we plot ROR delta specifically
    # If 'ror_delta' exists, use that
    if 'ror_delta' in plot_data.columns:
        metric_col = 'ror_delta'
        metric_name = 'ROR Delta'
    else:
        # Fallback: try to plot a specific metric if structure differs
        metric_col = plot_data.columns[2] if len(plot_data.columns) > 2 else None
        if metric_col is None:
            warnings.warn("No suitable metric column found for comparison.")
            fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT))
            ax.text(0.5, 0.5, "No Metric Column", ha='center', va='center', transform=ax.transAxes)
            plt.savefig(output_path, dpi=DPI)
            plt.close(fig)
            return
        metric_name = metric_col

    pivot_data = plot_data.pivot(index='soc', columns=baseline_col, values=metric_col)

    fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT))
    pivot_data.plot(kind='bar', ax=ax, title=f'{metric_name} by SOC and Baseline')
    ax.set_xlabel("System Organ Class (SOC)")
    ax.set_ylabel(metric_name)
    ax.legend(title=baseline_col)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig(output_path, dpi=DPI)
    plt.close(fig)

def create_summary_dashboard(
    signals_df: pd.DataFrame,
    top_signals_data: Optional[pd.DataFrame] = None,
    output_dir: Union[str, Path] = "output/dashboard"
) -> None:
    """
    Generate a multi-panel summary dashboard figure.

    Args:
        signals_df: DataFrame with all signal metrics.
        top_signals_data: Optional DataFrame with top signal details for table.
        output_dir: Directory to save the dashboard image.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = Path(output_dir) / "summary_dashboard.png"

    fig = plt.figure(figsize=(20, 12))

    # Panel 1: ROR Distribution
    ax1 = fig.add_subplot(2, 2, 1)
    if not signals_df.empty and 'ror' in signals_df.columns:
        ror_vals = signals_df['ror'].replace([np.inf, -np.inf], np.nan).dropna()
        ax1.hist(ror_vals, bins=30, color='skyblue', edgecolor='black', alpha=0.7)
        ax1.axvline(x=2.0, color='red', linestyle='--', linewidth=2)
        ax1.set_title("ROR Distribution")
        ax1.set_xlabel("ROR")
        ax1.set_ylabel("Count")
        ax1.grid(True, alpha=0.3)
    else:
        ax1.text(0.5, 0.5, "No ROR Data", ha='center', va='center')
        ax1.set_title("ROR Distribution (No Data)")

    # Panel 2: Signal Table (Top 10)
    ax2 = fig.add_subplot(2, 2, 2)
    ax2.axis('off')
    if top_signals_data is not None and not top_signals_data.empty:
        cols = [c for c in ['soc', 'ror', 'prr', 'ic', 'signal_flag'] if c in top_signals_data.columns]
        table_data = top_signals_data[cols].head(10)
        table = ax2.table(
            cellText=table_data.values,
            colLabels=table_data.columns,
            loc='center',
            cellLoc='center'
        )
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.2)
        ax2.set_title("Top 10 Signals")
    else:
        ax2.text(0.5, 0.5, "No Top Signals Data", ha='center', va='center')
        ax2.set_title("Top Signals (No Data)")

    # Panel 3: Signal Flags Distribution
    ax3 = fig.add_subplot(2, 2, 3)
    if not signals_df.empty and 'signal_flag' in signals_df.columns:
        flag_counts = signals_df['signal_flag'].value_counts()
        ax3.bar(['Signal', 'No Signal'], flag_counts.reindex([True, False], fill_value=0).values, color=['red', 'green'])
        ax3.set_title("Signal Detection (2-out-of-3 Rule)")
        ax3.set_xlabel("Category")
        ax3.set_ylabel("Count")
    else:
        ax3.text(0.5, 0.5, "No Flag Data", ha='center', va='center')
        ax3.set_title("Signal Detection (No Data)")

    # Panel 4: Temporal Trend (if available)
    ax4 = fig.add_subplot(2, 2, 4)
    # This would ideally receive pre-processed temporal data, but for a generic dashboard
    # we assume the caller might pass a specific temporal df or we skip if not applicable.
    # For now, a placeholder or simple summary if temporal data was passed separately.
    # Since this function signature doesn't include temporal data, we leave it as a placeholder
    # or check if 'REPT_DATE' exists in signals_df (unlikely).
    ax4.text(0.5, 0.5, "Temporal Analysis\n(See separate plots)", ha='center', va='center')
    ax4.set_title("Temporal Profile Summary")

    plt.suptitle("Statistical Analysis Summary Dashboard", fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    plt.savefig(output_path, dpi=DPI)
    plt.close(fig)

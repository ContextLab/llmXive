"""
Plots module for generating matplotlib figures for the COVID-19 VAERS analysis.

Provides helpers for:
- Weekly reporting counts (temporal profiles)
- Signal tables (disproportionality metrics)
"""
import os
import warnings
from pathlib import Path
from typing import List, Optional, Dict, Any

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np

# Ensure output directories exist
OUTPUT_DIR = Path("output")
TEMPORAL_PROFILES_DIR = OUTPUT_DIR / "temporal_profiles"
FIGURES_DIR = OUTPUT_DIR / "figures"

# Create directories if they don't exist
OUTPUT_DIR.mkdir(exist_ok=True)
TEMPORAL_PROFILES_DIR.mkdir(exist_ok=True)
FIGURES_DIR.mkdir(exist_ok=True)

# Style configuration
plt.style.use('default')
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3


def plot_weekly_counts(
    df: pd.DataFrame,
    date_col: str = 'REPT_DATE',
    soc_code: str = None,
    group_col: str = 'GROUP',
    output_path: Optional[str] = None,
    title_suffix: str = ""
) -> str:
    """
    Generate a weekly count plot for reporting dates.
    
    Args:
        df: DataFrame containing report data with date column
        date_col: Name of the date column (default: 'REPT_DATE')
        soc_code: Optional SOC code to filter for (if None, plots all)
        group_col: Column name for grouping (e.g., 'GROUP' for COVID-19 vs Non-COVID)
        output_path: Optional custom output path. If None, auto-generates based on soc_code
        title_suffix: Additional text to append to the title
        
    Returns:
        Path to the generated PNG file
    """
    if df.empty:
        raise ValueError("Input DataFrame is empty")
    
    # Ensure date column is datetime
    df_copy = df.copy()
    df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors='coerce')
    df_copy = df_copy.dropna(subset=[date_col])
    
    if df_copy.empty:
        raise ValueError(f"No valid dates found in column '{date_col}'")
    
    # Filter by SOC code if provided
    if soc_code is not None:
        if 'SOC_CODE' in df_copy.columns:
            df_copy = df_copy[df_copy['SOC_CODE'] == soc_code]
        elif 'SOC' in df_copy.columns:
            df_copy = df_copy[df_copy['SOC'] == soc_code]
        else:
            raise ValueError("DataFrame must contain 'SOC_CODE' or 'SOC' column when soc_code is specified")
    
    if df_copy.empty:
        raise ValueError(f"No data found for SOC code: {soc_code}")
    
    # Extract week information
    df_copy['WEEK'] = df_copy[date_col].dt.to_period('W')
    df_copy['WEEK_START'] = df_copy['WEEK'].dt.start_time
    
    # Group by week and group_col (if exists)
    if group_col in df_copy.columns:
        weekly_counts = df_copy.groupby(['WEEK_START', group_col]).size().unstack(fill_value=0)
    else:
        weekly_counts = df_copy.groupby('WEEK_START').size()
        if not isinstance(weekly_counts, pd.DataFrame):
            weekly_counts = weekly_counts.to_frame(name='count')
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    if isinstance(weekly_counts, pd.DataFrame):
        # Multiple groups
        for column in weekly_counts.columns:
            ax.plot(weekly_counts.index, weekly_counts[column], marker='o', label=column)
    else:
        # Single group
        ax.plot(weekly_counts.index, weekly_counts.values, marker='o')
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    plt.xticks(rotation=45)
    
    # Labels and title
    title = f"Weekly Report Counts for SOC {soc_code}" if soc_code else "Weekly Report Counts"
    if title_suffix:
        title += f" - {title_suffix}"
    ax.set_title(title)
    ax.set_xlabel("Report Date (Week Start)")
    ax.set_ylabel("Number of Reports")
    
    if group_col in df_copy.columns:
        ax.legend(title=group_col)
    
    ax.grid(True, alpha=0.3)
    
    # Determine output path
    if output_path is None:
        safe_soc = soc_code if soc_code else "all"
        output_path = str(TEMPORAL_PROFILES_DIR / f"weekly_counts_{safe_soc}.png")
    
    # Save figure
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    return output_path


def plot_signal_table(
    signals_df: pd.DataFrame,
    top_n: int = 10,
    metrics: List[str] = None,
    output_path: Optional[str] = None
) -> str:
    """
    Generate a visualization of the top signals table.
    
    Args:
        signals_df: DataFrame containing signal metrics (ROR, PRR, IC, etc.)
        top_n: Number of top signals to display
        metrics: List of metric columns to display. Defaults to ['ROR', 'PRR', 'IC', 'adjusted_p']
        output_path: Optional custom output path. If None, auto-generates path
        
    Returns:
        Path to the generated PNG file
    """
    if signals_df.empty:
        raise ValueError("Input DataFrame is empty")
    
    if metrics is None:
        metrics = ['ROR', 'PRR', 'IC', 'adjusted_p']
    
    # Filter for available metrics
    available_metrics = [m for m in metrics if m in signals_df.columns]
    if not available_metrics:
        raise ValueError(f"No metrics found in DataFrame. Available columns: {list(signals_df.columns)}")
    
    # Sort by signal strength (e.g., ROR or adjusted_p)
    sort_col = 'adjusted_p' if 'adjusted_p' in signals_df.columns else available_metrics[0]
    sorted_df = signals_df.sort_values(by=sort_col, ascending=True).head(top_n)
    
    # Create the figure
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Hide axes
    ax.axis('off')
    
    # Create table
    table_data = []
    for idx, row in sorted_df.iterrows():
        row_data = [row.get('SOC_CODE', row.get('SOC', f'SOC_{idx}'))]
        for metric in available_metrics:
            val = row.get(metric)
            if pd.isna(val):
                row_data.append('N/A')
            elif isinstance(val, float):
                row_data.append(f"{val:.4f}")
            else:
                row_data.append(str(val))
        table_data.append(row_data)
    
    # Add header
    headers = ['SOC Code'] + available_metrics
    
    table = ax.table(
        cellText=table_data,
        colLabels=headers,
        loc='center',
        cellLoc='center'
    )
    
    # Style the table
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.2, 1.8)
    
    # Style header
    for i in range(len(headers)):
        table[(0, i)].set_facecolor('#4472C4')
        table[(0, i)].set_text_props(color='white', fontweight='bold')
    
    # Style rows
    for i in range(1, len(table_data) + 1):
        for j in range(len(headers)):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#D6DCE4')
    
    # Title
    ax.set_title(f"Top {top_n} Disproportionality Signals", fontsize=14, fontweight='bold', pad=20)
    
    # Determine output path
    if output_path is None:
        output_path = str(FIGURES_DIR / "signal_table.png")
    
    # Save figure
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    return output_path


def plot_ror_distribution(
    signals_df: pd.DataFrame,
    threshold: float = 2.0,
    output_path: Optional[str] = None
) -> str:
    """
    Generate a histogram of ROR values with signal threshold line.
    
    Args:
        signals_df: DataFrame containing ROR values
        threshold: ROR threshold for signal detection (default: 2.0)
        output_path: Optional custom output path
        
    Returns:
        Path to the generated PNG file
    """
    if signals_df.empty:
        raise ValueError("Input DataFrame is empty")
    
    if 'ROR' not in signals_df.columns:
        raise ValueError("DataFrame must contain 'ROR' column")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot histogram
    ror_values = signals_df['ROR'].dropna()
    ax.hist(ror_values, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
    
    # Add threshold line
    ax.axvline(x=threshold, color='red', linestyle='--', linewidth=2, label=f'Threshold ({threshold})')
    
    # Add mean line
    mean_ror = ror_values.mean()
    ax.axvline(x=mean_ror, color='green', linestyle='-', linewidth=2, label=f'Mean ({mean_ror:.2f})')
    
    # Labels and title
    ax.set_xlabel('Reporting Odds Ratio (ROR)')
    ax.set_ylabel('Frequency')
    ax.set_title('Distribution of Reporting Odds Ratios by SOC')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Determine output path
    if output_path is None:
        output_path = str(FIGURES_DIR / "ror_distribution.png")
    
    # Save figure
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    return output_path


def plot_sensitivity_comparison(
    sensitivity_df: pd.DataFrame,
    metric: str = 'ROR',
    output_path: Optional[str] = None
) -> str:
    """
    Generate a bar chart comparing metrics between baseline groups.
    
    Args:
        sensitivity_df: DataFrame containing sensitivity analysis results
        metric: Metric to compare (e.g., 'ROR', 'PRR', 'IC')
        output_path: Optional custom output path
        
    Returns:
        Path to the generated PNG file
    """
    if sensitivity_df.empty:
        raise ValueError("Input DataFrame is empty")
    
    if metric not in sensitivity_df.columns:
        raise ValueError(f"DataFrame must contain '{metric}' column")
    
    if 'SOC_CODE' not in sensitivity_df.columns and 'SOC' not in sensitivity_df.columns:
        raise ValueError("DataFrame must contain 'SOC_CODE' or 'SOC' column")
    
    soc_col = 'SOC_CODE' if 'SOC_CODE' in sensitivity_df.columns else 'SOC'
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Prepare data for plotting
    soc_codes = sensitivity_df[soc_col].values
    baseline_values = sensitivity_df.get('baseline_value', sensitivity_df[metric]).values
    sensitivity_values = sensitivity_df.get('sensitivity_value', sensitivity_df[metric]).values
    delta_values = sensitivity_df.get('delta', sensitivity_df[metric] - baseline_values)
    
    x = np.arange(len(soc_codes))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, baseline_values, width, label='Baseline (Non-COVID)', color='steelblue')
    bars2 = ax.bar(x + width/2, sensitivity_values, width, label='Sensitivity (Non-COVID, Non-Flu)', color='coral')
    
    # Add delta values as annotations
    for i, (bar1, bar2, delta) in enumerate(zip(bars1, bars2, delta_values)):
        height1 = bar1.get_height()
        height2 = bar2.get_height()
        avg_height = (height1 + height2) / 2
        ax.annotate(f'{delta:.2f}',
                    xy=(x[i], avg_height),
                    xytext=(0, 5),
                    textcoords="offset points",
                    ha='center',
                    fontsize=8)
    
    ax.set_xlabel('System Organ Class (SOC)')
    ax.set_ylabel(metric)
    ax.set_title(f'Sensitivity Analysis: {metric} Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(soc_codes, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    # Determine output path
    if output_path is None:
        output_path = str(FIGURES_DIR / f"sensitivity_{metric.lower()}.png")
    
    # Save figure
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    return output_path


def create_summary_dashboard(
    signals_df: pd.DataFrame,
    top_n: int = 5
) -> str:
    """
    Create a comprehensive dashboard with multiple plots.
    
    Args:
        signals_df: DataFrame containing signal metrics
        top_n: Number of top signals to include in detailed plots
        
    Returns:
        Path to the generated PNG file
    """
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Top signals table snippet
    ax1 = axes[0, 0]
    ax1.axis('off')
    
    if not signals_df.empty:
        top_signals = signals_df.sort_values('adjusted_p').head(top_n)
        table_data = []
        for idx, row in top_signals.iterrows():
            row_data = [row.get('SOC_CODE', row.get('SOC', f'SOC_{idx}'))]
            for metric in ['ROR', 'PRR', 'IC', 'adjusted_p']:
                val = row.get(metric)
                row_data.append(f"{val:.4f}" if isinstance(val, float) and not pd.isna(val) else 'N/A')
            table_data.append(row_data)
        
        if table_data:
            table = ax1.table(
                cellText=table_data,
                colLabels=['SOC'] + ['ROR', 'PRR', 'IC', 'Adj P'],
                loc='center',
                cellLoc='center'
            )
            table.auto_set_font_size(False)
            table.set_fontsize(8)
            table.scale(1.1, 1.5)
            ax1.set_title(f"Top {top_n} Signals", fontsize=12, fontweight='bold')
    
    # 2. ROR distribution
    ax2 = axes[0, 1]
    if 'ROR' in signals_df.columns:
        ror_values = signals_df['ROR'].dropna()
        ax2.hist(ror_values, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax2.axvline(x=2.0, color='red', linestyle='--', label='Threshold (2.0)')
        ax2.set_xlabel('ROR')
        ax2.set_ylabel('Frequency')
        ax2.set_title('ROR Distribution')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
    
    # 3. PRR vs IC scatter
    ax3 = axes[1, 0]
    if 'PRR' in signals_df.columns and 'IC' in signals_df.columns:
        prr = signals_df['PRR'].dropna()
        ic = signals_df['IC'].dropna()
        if len(prr) == len(ic):
            ax3.scatter(prr, ic, alpha=0.6)
            ax3.axhline(y=0, color='red', linestyle='--', label='IC Threshold (0)')
            ax3.axvline(x=1.5, color='blue', linestyle='--', label='PRR Threshold (1.5)')
            ax3.set_xlabel('PRR')
            ax3.set_ylabel('IC')
            ax3.set_title('PRR vs IC')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
    
    # 4. Signal count by category
    ax4 = axes[1, 1]
    if 'signal_flag' in signals_df.columns:
        signal_counts = signals_df['signal_flag'].value_counts()
        colors = ['#2ecc71' if x == True else '#e74c3c' for x in signal_counts.index]
        ax4.pie(signal_counts.values, labels=signal_counts.index.astype(str), autopct='%1.1f%%', colors=colors)
        ax4.set_title('Signal Detection Results')
    
    plt.suptitle('Disproportionality Analysis Dashboard', fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    output_path = str(FIGURES_DIR / "summary_dashboard.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    return output_path
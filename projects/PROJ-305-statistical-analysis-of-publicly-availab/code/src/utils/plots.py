"""
Plotting utilities for the VAERS statistical analysis pipeline.

This module provides helper functions for generating matplotlib figures
including weekly counts, signal tables, ROR distributions, and sensitivity
comparisons.
"""

import os
import warnings
from pathlib import Path
from typing import List, Optional, Dict, Any

import matplotlib
# Use non-interactive backend for server environments
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Ensure output directories exist
OUTPUT_DIR = Path("output")
FIGURES_DIR = OUTPUT_DIR / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Style configuration
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['figure.dpi'] = 100
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 11

# Color palette
COLOR_PALETTE = {
    'primary': '#2c3e50',
    'secondary': '#3498db',
    'accent': '#e74c3c',
    'success': '#27ae60',
    'warning': '#f39c12',
    'neutral': '#95a5a6'
}

def plot_weekly_counts(
    df: pd.DataFrame,
    soc_codes: List[str],
    date_col: str = "REPT_DATE",
    output_path: Optional[Path] = None,
    title_suffix: str = ""
) -> Path:
    """
    Generate weekly count plots for specified SOC codes.
    
    Args:
        df: DataFrame containing report data with REPT_DATE column
        soc_codes: List of SOC codes to plot
        date_col: Name of the date column (default: "REPT_DATE")
        output_path: Optional custom output path
        title_suffix: Optional suffix to add to the plot title
        
    Returns:
        Path to the generated figure file
    """
    if df.empty:
        raise ValueError("Input DataFrame is empty")
        
    if date_col not in df.columns:
        raise ValueError(f"Date column '{date_col}' not found in DataFrame")
        
    # Ensure date column is datetime
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df.dropna(subset=[date_col])
    
    # Add week column
    df['week'] = df[date_col].dt.to_period('W').dt.start_time
    
    fig, axes = plt.subplots(
        len(soc_codes), 1, 
        figsize=(14, 4 * len(soc_codes)),
        constrained_layout=True
    )
    
    # Handle single SOC case
    if len(soc_codes) == 1:
        axes = [axes]
        
    for idx, soc_code in enumerate(soc_codes):
        if soc_code not in df.columns:
            warnings.warn(f"SOC code '{soc_code}' not found in DataFrame, skipping")
            continue
            
        ax = axes[idx]
        
        # Filter and group by week
        weekly_data = df.groupby('week')[soc_code].sum().reset_index()
        weekly_data = weekly_data.sort_values('week')
        
        ax.plot(
            weekly_data['week'], 
            weekly_data[soc_code],
            marker='o',
            linewidth=2,
            markersize=4,
            color=COLOR_PALETTE['secondary']
        )
        
        ax.set_title(
            f"Weekly Report Counts for SOC: {soc_code} {title_suffix}",
            pad=15
        )
        ax.set_xlabel("Report Week")
        ax.set_ylabel("Number of Reports")
        ax.tick_params(axis='x', rotation=45)
        
        # Add grid
        ax.grid(True, alpha=0.3, linestyle='--')
        
    # Overall title
    if len(soc_codes) > 1:
        fig.suptitle(
            f"Weekly Reporting Profiles {title_suffix}",
            fontsize=14,
            fontweight='bold',
            y=1.02
        )
    
    # Determine output path
    if output_path is None:
        safe_suffix = "_".join([s.replace(" ", "_") for s in soc_codes[:3]])
        if len(soc_codes) > 3:
            safe_suffix += "_etc"
        output_path = FIGURES_DIR / f"weekly_counts_{safe_suffix}.png"
    
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close(fig)
    
    return output_path

def plot_signal_table(
    signals_df: pd.DataFrame,
    top_n: int = 10,
    output_path: Optional[Path] = None,
    title: str = "Top Signal Detection Results"
) -> Path:
    """
    Generate a formatted table visualization of signal detection results.
    
    Args:
        signals_df: DataFrame containing signal metrics (ROR, PRR, IC, etc.)
        top_n: Number of top signals to display
        output_path: Optional custom output path
        title: Plot title
        
    Returns:
        Path to the generated figure file
    """
    if signals_df.empty:
        raise ValueError("Input DataFrame is empty")
        
    # Sort by ROR descending if available, else by PRR
    sort_col = 'ROR' if 'ROR' in signals_df.columns else 'PRR'
    sorted_df = signals_df.sort_values(by=sort_col, ascending=False).head(top_n)
    
    # Create figure for table
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.axis('tight')
    ax.axis('off')
    
    # Prepare table data
    columns_to_show = [
        col for col in ['SOC_CODE', 'SOC_NAME', 'ROR', 'ROR_CI_lower', 'ROR_CI_upper', 
                       'PRR', 'PRR_CI_lower', 'PRR_CI_upper', 
                       'IC', 'IC_CI_lower', 'IC_CI_upper',
                       'adjusted_p', 'is_signal']
        if col in signals_df.columns
    ]
    
    # Ensure we have at least SOC_CODE and one metric
    if 'SOC_CODE' not in columns_to_show:
        columns_to_show.insert(0, 'SOC_CODE')
        
    table_data = sorted_df[columns_to_show].reset_index(drop=True)
    
    # Format numeric columns
    for col in table_data.columns:
        if table_data[col].dtype in ['float64', 'float32']:
            table_data[col] = table_data[col].apply(lambda x: f"{x:.3f}")
    
    # Create table
    table = ax.table(
        cellText=table_data.values,
        colLabels=table_data.columns,
        loc='center',
        cellLoc='center',
        colColours=[COLOR_PALETTE['primary']] * len(columns_to_show)
    )
    
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.2, 1.5)
    
    # Style the table
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold', color='white')
            cell.set_facecolor(COLOR_PALETTE['primary'])
        elif row % 2 == 0:
            cell.set_facecolor('#f2f2f2')
        else:
            cell.set_facecolor('white')
            
        cell.set_edgecolor('lightgray')
    
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    if output_path is None:
        output_path = FIGURES_DIR / "signal_table.png"
    
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close(fig)
    
    return output_path

def plot_ror_distribution(
    signals_df: pd.DataFrame,
    output_path: Optional[Path] = None,
    title: str = "Distribution of Reporting Odds Ratios"
) -> Path:
    """
    Generate histogram of ROR values with threshold indicators.
    
    Args:
        signals_df: DataFrame containing ROR values
        output_path: Optional custom output path
        title: Plot title
        
    Returns:
        Path to the generated figure file
    """
    if signals_df.empty or 'ROR' not in signals_df.columns:
        raise ValueError("Input DataFrame must contain 'ROR' column")
        
    ror_values = signals_df['ROR'].dropna()
    
    if len(ror_values) == 0:
        raise ValueError("No valid ROR values found")
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot histogram
    ax.hist(
        ror_values, 
        bins=50, 
        color=COLOR_PALETTE['secondary'], 
        alpha=0.7,
        edgecolor='black'
    )
    
    # Add threshold line (ROR > 2.0)
    threshold = 2.0
    ax.axvline(
        x=threshold, 
        color=COLOR_PALETTE['accent'], 
        linestyle='--', 
        linewidth=2,
        label=f"Signal Threshold (ROR > {threshold})"
    )
    
    # Fill area above threshold
    x_vals = np.linspace(ror_values.min(), ror_values.max(), 100)
    y_vals = np.ones_like(x_vals) * len(ror_values) / 50  # Approximate height
    ax.fill_between(
        x_vals, 
        0, 
        y_vals,
        where=(x_vals >= threshold),
        color=COLOR_PALETTE['accent'],
        alpha=0.2,
        label='Signal Region'
    )
    
    ax.set_xlabel("Reporting Odds Ratio (ROR)")
    ax.set_ylabel("Frequency")
    ax.set_title(title)
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    
    if output_path is None:
        output_path = FIGURES_DIR / "ror_distribution.png"
    
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close(fig)
    
    return output_path

def plot_sensitivity_comparison(
    df_primary: pd.DataFrame,
    df_sensitivity: pd.DataFrame,
    soc_codes: List[str],
    metric: str = "ROR",
    output_path: Optional[Path] = None,
    title: str = "Sensitivity Analysis: Baseline Comparison"
) -> Path:
    """
    Compare signal metrics between primary and sensitivity baselines.
    
    Args:
        df_primary: DataFrame with metrics from primary baseline
        df_sensitivity: DataFrame with metrics from sensitivity baseline
        soc_codes: List of SOC codes to compare
        metric: Metric to compare (e.g., "ROR", "PRR", "IC")
        output_path: Optional custom output path
        title: Plot title
        
    Returns:
        Path to the generated figure file
    """
    if metric not in df_primary.columns or metric not in df_sensitivity.columns:
        raise ValueError(f"Metric '{metric}' not found in both DataFrames")
        
    # Filter for relevant SOCs
    primary_vals = df_primary[df_primary['SOC_CODE'].isin(soc_codes)][metric].values
    sens_vals = df_sensitivity[df_sensitivity['SOC_CODE'].isin(soc_codes)][metric].values
    
    if len(primary_vals) == 0 or len(sens_vals) == 0:
        raise ValueError("No matching SOC codes found in both DataFrames")
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(len(soc_codes))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, primary_vals, width, label='Primary Baseline', color=COLOR_PALETTE['secondary'])
    bars2 = ax.bar(x + width/2, sens_vals, width, label='Sensitivity Baseline', color=COLOR_PALETTE['accent'])
    
    ax.set_xlabel("SOC Code")
    ax.set_ylabel(metric)
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(soc_codes, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, axis='y', alpha=0.3)
    
    # Add delta annotations
    deltas = primary_vals - sens_vals
    for i, delta in enumerate(deltas):
        ax.text(
            i, 
            max(primary_vals[i], sens_vals[i]) + 0.1,
            f"Δ: {delta:.3f}",
            ha='center',
            fontsize=8,
            color=COLOR_PALETTE['primary']
        )
    
    if output_path is None:
        output_path = FIGURES_DIR / "sensitivity_comparison.png"
    
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close(fig)
    
    return output_path

def create_summary_dashboard(
    signals_df: pd.DataFrame,
    top_n: int = 5,
    output_path: Optional[Path] = None
) -> Path:
    """
    Create a multi-panel summary dashboard.
    
    Args:
        signals_df: DataFrame containing signal metrics
        top_n: Number of top signals to include
        output_path: Optional custom output path
        
    Returns:
        Path to the generated figure file
    """
    if signals_df.empty:
        raise ValueError("Input DataFrame is empty")
        
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
    
    # 1. Top signals table
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.axis('off')
    
    top_signals = signals_df.sort_values(by='ROR', ascending=False).head(top_n)
    columns = [col for col in ['SOC_CODE', 'ROR', 'PRR', 'IC', 'adjusted_p', 'is_signal'] 
              if col in signals_df.columns]
    
    table_data = top_signals[columns].reset_index(drop=True)
    for col in table_data.columns:
        if table_data[col].dtype in ['float64', 'float32']:
            table_data[col] = table_data[col].apply(lambda x: f"{x:.3f}")
    
    table = ax1.table(
        cellText=table_data.values,
        colLabels=table_data.columns,
        loc='center',
        cellLoc='center',
        colColours=[COLOR_PALETTE['primary']] * len(columns)
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.1, 1.4)
    ax1.set_title("Top Signal Detection Results", fontsize=12, fontweight='bold', pad=10)
    
    # 2. ROR Distribution
    ax2 = fig.add_subplot(gs[0, 1])
    ror_values = signals_df['ROR'].dropna()
    ax2.hist(ror_values, bins=50, color=COLOR_PALETTE['secondary'], alpha=0.7, edgecolor='black')
    ax2.axvline(x=2.0, color=COLOR_PALETTE['accent'], linestyle='--', linewidth=2, label='Threshold')
    ax2.set_xlabel("ROR")
    ax2.set_ylabel("Frequency")
    ax2.set_title("ROR Distribution")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. PRR vs ROR scatter
    ax3 = fig.add_subplot(gs[1, 0])
    if 'PRR' in signals_df.columns:
        ax3.scatter(signals_df['ROR'], signals_df['PRR'], alpha=0.6, color=COLOR_PALETTE['secondary'])
        ax3.axhline(y=1.5, color=COLOR_PALETTE['accent'], linestyle='--', alpha=0.7)
        ax3.axvline(x=2.0, color=COLOR_PALETTE['accent'], linestyle='--', alpha=0.7)
        ax3.set_xlabel("ROR")
        ax3.set_ylabel("PRR")
        ax3.set_title("ROR vs PRR Correlation")
        ax3.grid(True, alpha=0.3)
    else:
        ax3.text(0.5, 0.5, "PRR data not available", ha='center', va='center', transform=ax3.transAxes)
    
    # 4. Signal count summary
    ax4 = fig.add_subplot(gs[1, 1])
    if 'is_signal' in signals_df.columns:
        signal_counts = signals_df['is_signal'].value_counts()
        labels = ['Signals', 'Non-Signals']
        colors = [COLOR_PALETTE['success'], COLOR_PALETTE['neutral']]
        ax4.pie(
            signal_counts, 
            labels=labels, 
            autopct='%1.1f%%',
            colors=colors,
            startangle=90
        )
        ax4.set_title("Signal Detection Summary")
    else:
        ax4.text(0.5, 0.5, "Signal flag not available", ha='center', va='center', transform=ax4.transAxes)
    
    fig.suptitle("Statistical Analysis Summary Dashboard", fontsize=16, fontweight='bold', y=1.02)
    
    if output_path is None:
        output_path = FIGURES_DIR / "summary_dashboard.png"
    
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close(fig)
    
    return output_path
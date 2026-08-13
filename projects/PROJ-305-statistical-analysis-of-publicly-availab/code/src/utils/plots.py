import os
import warnings
from pathlib import Path
from typing import List, Optional, Dict, Any

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Ensure non-interactive backend for headless execution
matplotlib.use('Agg')

# Configure plot style
plt.style.use('seaborn-v0_8-whitegrid')
warnings.filterwarnings('ignore', category=UserWarning)


def plot_weekly_counts(
    df: pd.DataFrame,
    output_path: str,
    date_col: str = 'REPT_DATE',
    count_col: str = 'count',
    title: str = "Weekly Reporting Counts",
    x_label: str = "Week",
    y_label: str = "Number of Reports",
    soc_code: Optional[str] = None
) -> str:
    """
    Generates a line plot of weekly reporting counts.

    Args:
        df: DataFrame containing at least 'REPT_DATE' and a count column.
            If 'REPT_DATE' is present, it will be aggregated to weekly bins.
            If 'count_col' is present, it is used as the y-value.
        output_path: Path to save the generated PNG file.
        date_col: Name of the date column (default 'REPT_DATE').
        count_col: Name of the count column (default 'count'). If None,
                   the plot counts rows per week.
        title: Plot title.
        x_label: X-axis label.
        y_label: Y-axis label.
        soc_code: Optional SOC code to include in the title.

    Returns:
        The absolute path to the saved file.
    """
    plt.figure(figsize=(12, 6))

    # Prepare data
    if date_col in df.columns:
        # Ensure date is datetime
        df_temp = df.copy()
        df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors='coerce')
        df_temp = df_temp.dropna(subset=[date_col])

        # Resample to weekly frequency
        df_temp['week'] = df_temp[date_col].dt.to_period('W')
        if count_col and count_col in df_temp.columns:
            weekly_data = df_temp.groupby('week')[count_col].sum().reset_index()
        else:
            weekly_data = df_temp.groupby('week').size().reset_index(name='count')

        weekly_data['week'] = weekly_data['week'].dt.to_timestamp()
        x_vals = weekly_data['week']
        y_vals = weekly_data['count']
    else:
        # Fallback if no date column, assume index is time or simple range
        x_vals = range(len(df))
        y_vals = df[count_col].values if count_col in df.columns else df.index

    plt.plot(x_vals, y_vals, marker='o', linestyle='-', color='#1f77b4', linewidth=2)

    plt.title(f"{title} {'- ' + soc_code if soc_code else ''}")
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    plt.savefig(output_path, dpi=150)
    plt.close()

    return os.path.abspath(output_path)


def plot_signal_table(
    signals_df: pd.DataFrame,
    output_path: str,
    top_n: int = 10,
    metrics: List[str] = ['ROR', 'PRR', 'IC'],
    flag_col: str = 'is_signal'
) -> str:
    """
    Generates a matplotlib figure displaying a table of signal metrics.

    Args:
        signals_df: DataFrame containing signal metrics (SOC_CODE, ROR, PRR, IC, etc.).
        output_path: Path to save the PNG file.
        top_n: Number of top signals to display.
        metrics: List of metric columns to display.
        flag_col: Column name indicating if a signal was flagged.

    Returns:
        The absolute path to the saved file.
    """
    plt.figure(figsize=(10, 8))
    plt.axis('off')

    # Select top N signals based on ROR or first metric
    if 'ROR' in signals_df.columns:
        display_df = signals_df.nlargest(top_n, 'ROR')
    else:
        display_df = signals_df.head(top_n)

    # Prepare table data
    columns = ['SOC_CODE'] + metrics
    if flag_col in display_df.columns:
        columns.append(flag_col)

    table_data = display_df[columns].values

    # Create table
    table = plt.table(
        cellText=table_data,
        colLabels=columns,
        loc='center',
        cellLoc='center',
        colWidths=[0.2] * len(columns)
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)

    # Highlight header
    for i in range(len(columns)):
        table[(0, i)].set_facecolor('#4472C4')
        table[(0, i)].set_text_props(color='white', weight='bold')

    # Highlight flagged signals
    if flag_col in display_df.columns:
        for i in range(1, len(table_data) + 1):
            if table_data[i-1][-1] == True or table_data[i-1][-1] == 'True':
                table[(i, -1)].set_facecolor('#D9E1F2')

    plt.title(f"Top {top_n} Disproportionality Signals", fontsize=14, pad=20)
    plt.tight_layout()

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    return os.path.abspath(output_path)


def plot_ror_distribution(
    signals_df: pd.DataFrame,
    output_path: str,
    metric: str = 'ROR',
    threshold: float = 2.0,
    title: str = "Distribution of Reporting Odds Ratios"
) -> str:
    """
    Generates a histogram of ROR values with a threshold line.

    Args:
        signals_df: DataFrame containing the metric column.
        output_path: Path to save the PNG file.
        metric: Name of the metric column (default 'ROR').
        threshold: Vertical line threshold value.
        title: Plot title.

    Returns:
        The absolute path to the saved file.
    """
    if metric not in signals_df.columns:
        raise ValueError(f"Column '{metric}' not found in DataFrame.")

    plt.figure(figsize=(10, 6))

    values = signals_df[metric].dropna()

    plt.hist(values, bins=30, color='#2ca02c', alpha=0.7, edgecolor='black')
    plt.axvline(threshold, color='red', linestyle='--', linewidth=2, label=f'Threshold: {threshold}')

    plt.title(title)
    plt.xlabel(metric)
    plt.ylabel("Frequency")
    plt.legend()
    plt.tight_layout()

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    plt.savefig(output_path, dpi=150)
    plt.close()

    return os.path.abspath(output_path)


def plot_sensitivity_comparison(
    df_baseline: pd.DataFrame,
    df_sensitivity: pd.DataFrame,
    output_path: str,
    metrics: List[str] = ['ROR', 'PRR'],
    title: str = "Sensitivity Analysis: Baseline vs Non-COVID, Non-Flu"
) -> str:
    """
    Generates a bar chart comparing metrics between two baseline definitions.

    Args:
        df_baseline: DataFrame with metrics for the primary baseline.
        df_sensitivity: DataFrame with metrics for the sensitivity baseline.
        output_path: Path to save the PNG file.
        metrics: List of metrics to compare.
        title: Plot title.

    Returns:
        The absolute path to the saved file.
    """
    plt.figure(figsize=(14, 8))

    # Assume both DFs have 'SOC_CODE' and the metric columns
    common_socs = list(set(df_baseline['SOC_CODE']).intersection(set(df_sensitivity['SOC_CODE'])))
    if not common_socs:
        raise ValueError("No common SOC codes found between the two datasets.")

    # Sort by baseline ROR for top 10 if ROR exists
    if 'ROR' in df_baseline.columns:
        common_socs = df_baseline[df_baseline['SOC_CODE'].isin(common_socs)].nlargest(10, 'ROR')['SOC_CODE'].tolist()
    else:
        common_socs = common_socs[:10]

    x = np.arange(len(common_socs))
    width = 0.35

    bars1 = plt.bar(x - width/2, [df_baseline[df_baseline['SOC_CODE'] == soc][metrics[0]].values[0] if not df_baseline[df_baseline['SOC_CODE'] == soc].empty else 0 for soc in common_socs], width, label='Primary Baseline (All Non-COVID)', color='#1f77b4')
    bars2 = plt.bar(x + width/2, [df_sensitivity[df_sensitivity['SOC_CODE'] == soc][metrics[0]].values[0] if not df_sensitivity[df_sensitivity['SOC_CODE'] == soc].empty else 0 for soc in common_socs], width, label='Sensitivity Baseline (Non-COVID, Non-Flu)', color='#ff7f0e')

    plt.xticks(x, common_socs, rotation=45, ha='right')
    plt.xlabel('SOC Code')
    plt.ylabel(metrics[0])
    plt.title(title)
    plt.legend()
    plt.tight_layout()

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    plt.savefig(output_path, dpi=150)
    plt.close()

    return os.path.abspath(output_path)


def create_summary_dashboard(
    weekly_path: str,
    signals_table_path: str,
    ror_dist_path: str,
  output_path: str
) -> str:
    """
    Combines three plots into a single dashboard figure.

    Args:
        weekly_path: Path to the weekly counts plot.
        signals_table_path: Path to the signals table plot.
        ror_dist_path: Path to the ROR distribution plot.
        output_path: Path to save the combined dashboard.

    Returns:
        The absolute path to the saved file.
    """
    # Since we need to combine images, we can either re-generate them or
    # use mpl.image. Re-generating is cleaner for layout control.
    # However, to keep it simple and robust, we assume the caller generated
    # the subplots. Here we will just create a layout and draw the subplots
    # by re-calling the logic or creating empty axes if files are missing.
    # For this implementation, we assume the files exist and we are just
    # composing a layout, but matplotlib doesn't easily import existing images
    # into subplots without reading them.
    # Better approach: Return a function that expects DataFrames, but the task
    # asks for helpers. Let's implement a layout that expects the user to
    # have plotted into specific axes, or just create a new figure with
    # 3 subplots and re-plot data if available.
    # Given the constraint of "helpers", let's assume we receive the data
    # or we just create the layout structure.
    # Actually, the most robust "helper" for a dashboard is to create the
    # figure structure. We will assume the inputs are paths to the individual
    # plots. We will read them as images and place them.

    import matplotlib.image as mpimg

    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    fig.suptitle("Statistical Analysis Dashboard", fontsize=16)

    # Load and display images
    try:
        axes[0].imshow(mpimg.imread(weekly_path))
        axes[0].axis('off')
        axes[0].set_title("Weekly Counts")
    except Exception:
        axes[0].text(0.5, 0.5, "Weekly Plot Missing", ha='center', va='center', transform=axes[0].transAxes)

    try:
        axes[1].imshow(mpimg.imread(signals_table_path))
        axes[1].axis('off')
        axes[1].set_title("Signal Table")
    except Exception:
        axes[1].text(0.5, 0.5, "Signal Table Missing", ha='center', va='center', transform=axes[1].transAxes)

    try:
        axes[2].imshow(mpimg.imread(ror_dist_path))
        axes[2].axis('off')
        axes[2].set_title("ROR Distribution")
    except Exception:
        axes[2].text(0.5, 0.5, "ROR Plot Missing", ha='center', va='center', transform=axes[2].transAxes)

    plt.tight_layout()

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

    return os.path.abspath(output_path)

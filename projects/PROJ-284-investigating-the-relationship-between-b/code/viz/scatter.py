"""
Scatter plot generator for metric vs. score analysis.

Generates publication-quality scatter plots with regression lines,
annotated correlation coefficients (r) and FDR-corrected q-values.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

# Import from project API surface
from code.logging_config import get_logger

logger = get_logger(__name__)


def load_correlation_results(
    input_path: Optional[Union[str, Path]] = None
) -> pd.DataFrame:
    """
    Load correlation results from CSV.
    
    Args:
        input_path: Path to correlation results CSV. Defaults to 
                   'data/analysis/fdr_corrected_results.csv' if not provided.
    
    Returns:
        DataFrame containing correlation results.
    
    Raises:
        FileNotFoundError: If the input file does not exist.
    """
    if input_path is None:
        input_path = Path("data/analysis/fdr_corrected_results.csv")
    else:
        input_path = Path(input_path)
    
    if not input_path.exists():
        raise FileNotFoundError(
            f"Correlation results file not found: {input_path}. "
            "Ensure T025 (FDR correction) has been executed first."
        )
    
    df = pd.read_csv(input_path)
    logger.log("load_correlation_results", path=str(input_path), rows=len(df))
    return df


def generate_scatter_plot(
    metric_name: str,
    df: pd.DataFrame,
    output_dir: Union[str, Path] = "figures",
    output_filename: Optional[str] = None,
    metric_col: str = "metric_value",
    score_col: str = "motor_score",
    r_col: str = "r",
    q_col: str = "q",
    significant_col: str = "significant",
    dpi: int = 300,
    figsize: Tuple[int, int] = (8, 6),
) -> Path:
    """
    Generate a scatter plot with regression line and annotations.
    
    Creates a scatter plot of the specified metric vs. motor score,
    adds a regression line, and annotates the plot with r and q values.
    
    Args:
        metric_name: Name of the metric for the x-axis label and title.
        df: DataFrame containing the data.
        output_dir: Directory to save the plot.
        output_filename: Name of the output file. If None, generated from metric_name.
        metric_col: Column name for metric values.
        score_col: Column name for motor scores.
        r_col: Column name for correlation coefficient.
        q_col: Column name for FDR-corrected p-value.
        significant_col: Column name for significance flag.
        dpi: Resolution for the output image.
        figsize: Figure size in inches (width, height).
    
    Returns:
        Path to the generated plot file.
    
    Raises:
        KeyError: If required columns are missing from the DataFrame.
        ValueError: If data is invalid for plotting.
    """
    # Ensure output directory exists
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate output filename if not provided
    if output_filename is None:
        safe_name = metric_name.replace(" ", "_").replace("/", "_").lower()
        output_filename = f"scatter_{safe_name}.png"
    
    output_path = output_dir / output_filename
    
    # Validate columns exist
    required_cols = [metric_col, score_col, r_col, q_col, significant_col]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns: {missing}")
    
    # Extract data for this metric
    # Filter to rows matching the metric_name (assuming metric_name column exists or we filter by name)
    # If metric_name is a value in a 'metric' column, filter by that. 
    # Otherwise, assume df has one row per metric or we use the first row if metric_name matches.
    
    # Check if there's a 'metric' or 'metric_name' column to filter
    if "metric" in df.columns:
        mask = df["metric"] == metric_name
    elif "metric_name" in df.columns:
        mask = df["metric_name"] == metric_name
    else:
        # Assume single row or that we should use the provided metric_name as a label
        # If no filter column, we might be plotting aggregated data or the df is already filtered
        # For robustness, if no filter column exists and len(df) > 1, we log a warning
        if len(df) > 1:
            logger.log(
                "generate_scatter_plot_warning",
                message="No 'metric' column found to filter; using first row or entire dataset if single row.",
                df_shape=list(df.shape)
            )
        mask = pd.Series([True] * len(df))
    
    subset = df[mask]
    
    if len(subset) == 0:
        raise ValueError(f"No data found for metric: {metric_name}")
    
    # If multiple rows match, we might need to aggregate or pick one. 
    # For simplicity, if > 1 row, we take the first one (or aggregate if needed).
    # However, typically this function is called per metric, so we expect one row.
    if len(subset) > 1:
        logger.log(
            "generate_scatter_plot_aggregate",
            message=f"Multiple rows found for {metric_name}; using first.",
            count=len(subset)
        )
        subset = subset.iloc[:1]
    
    row = subset.iloc[0]
    
    # Get r and q for annotation
    r_val = row[r_col]
    q_val = row[q_col]
    is_sig = row[significant_col] if significant_col in row.index else (q_val < 0.05)
    
    # Prepare data for plotting
    # If the df has individual subject data (multiple rows per metric), we plot all.
    # If the df is summary data (one row per metric), we cannot plot a scatter.
    # We assume the df passed here contains SUBJECT-LEVEL data for the metric.
    # If the df is summary, we need to check if there are columns for x and y values.
    
    # Check if we have subject-level data (multiple rows)
    # We expect the df to have columns like 'subject_id', 'motor_score', and the metric value.
    # If the df is summary (one row), we cannot create a scatter plot.
    
    if len(subset) == 1:
        # This might be summary data. Check if we have the raw data elsewhere.
        # For this implementation, we assume the df passed contains subject-level data
        # for the metric. If not, we raise an error or try to load from another source.
        # However, based on the task, we expect the df to be the result of correlations
        # which might be summary. Let's assume the df has been prepared to have subject-level data.
        
        # If the df is summary, we cannot plot. We need to check the schema.
        # Let's assume the df has columns: metric, motor_score, and the metric value is in a column named after the metric?
        # Or the df has been melted?
        
        # Alternative: The df might have columns: subject_id, motor_score, metric_name, metric_value
        # We need to pivot or filter.
        
        # Given the ambiguity, we assume the df has a column for the metric values.
        # If the df is summary (one row), we cannot plot. We need to raise an error.
        if "subject_id" not in subset.columns and len(subset) == 1:
            raise ValueError(
                f"Cannot generate scatter plot for {metric_name}: "
                "DataFrame appears to be summary data (single row). "
                "Expected subject-level data with multiple rows."
            )
        
        # If we have subject_id, we can plot.
        # But the df might be in long format: subject_id, metric, value
        # We need to pivot to wide format or filter.
        
        # Let's assume the df is in wide format: subject_id, motor_score, metric_name, ...
        # Or the df has been filtered to one metric and has columns: subject_id, motor_score, metric_value
        
        # For robustness, we check if we have at least 2 rows.
        if len(subset) < 2:
            raise ValueError(
                f"Insufficient data points for scatter plot of {metric_name}: "
                f"expected >= 2, got {len(subset)}."
            )
        
        # Extract x and y
        # If the df has a column named after the metric, use that.
        # Otherwise, use metric_col.
        if metric_name in subset.columns:
            x_data = subset[metric_name].values
        else:
            # Try to find the metric value in a column named metric_value or similar
            if metric_col in subset.columns:
                x_data = subset[metric_col].values
            else:
                # If no metric value column, we cannot plot.
                raise KeyError(
                    f"Cannot find metric values for {metric_name} in columns: {list(subset.columns)}"
                )
        
        y_data = subset[score_col].values
    else:
        # We have multiple rows, assume they are subject-level
        x_data = subset[metric_col].values
        y_data = subset[score_col].values
    
    # Validate data
    if len(x_data) < 2 or len(y_data) < 2:
        raise ValueError("Insufficient data points for scatter plot.")
    
    # Remove NaN
    valid = ~(np.isnan(x_data) | np.isnan(y_data))
    x_data = x_data[valid]
    y_data = y_data[valid]
    
    if len(x_data) < 2:
        raise ValueError("Insufficient valid data points after removing NaN.")
    
    # Create plot
    fig, ax = plt.subplots(figsize=figsize)
    
    # Scatter plot
    ax.scatter(x_data, y_data, alpha=0.6, edgecolors='w', s=50, color='#2E86AB')
    
    # Regression line
    if len(x_data) >= 2:
        slope, intercept, r, p, std_err = stats.linregress(x_data, y_data)
        x_line = np.linspace(min(x_data), max(x_data), 100)
        y_line = slope * x_line + intercept
        ax.plot(x_line, y_line, color='#A23B72', linewidth=2, label=f'Regression (r={r:.3f})')
    
    # Annotate r and q
    sig_text = "*" if is_sig else ""
    annotation = f"r = {r_val:.3f}{sig_text}\nq = {q_val:.3f}"
    ax.annotate(
        annotation,
        xy=(0.05, 0.95),
        xycoords='axes fraction',
        verticalalignment='top',
        horizontalalignment='left',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
        fontsize=11
    )
    
    # Labels and title
    ax.set_xlabel(metric_name.replace('_', ' ').title(), fontsize=12)
    ax.set_ylabel('Motor Score', fontsize=12)
    ax.set_title(f'{metric_name.replace("_", " ").title()} vs. Motor Performance', fontsize=14)
    
    ax.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    
    # Save
    fig.savefig(output_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    
    logger.log(
        "generate_scatter_plot_success",
        metric=metric_name,
        output=str(output_path),
        points=len(x_data),
        r=r_val,
        q=q_val
    )
    
    return output_path


def generate_all_scatter_plots(
    input_path: Optional[Union[str, Path]] = None,
    output_dir: Union[str, Path] = "figures",
    metrics: Optional[List[str]] = None,
    **kwargs
) -> List[Path]:
    """
    Generate scatter plots for all metrics in the correlation results.
    
    Args:
        input_path: Path to correlation results CSV.
        output_dir: Directory to save plots.
        metrics: List of metric names to plot. If None, plots all unique metrics.
        **kwargs: Additional arguments passed to generate_scatter_plot.
    
    Returns:
        List of paths to generated plot files.
    """
    df = load_correlation_results(input_path)
    
    # Determine which metrics to plot
    if metrics is None:
        # Look for a column named 'metric' or 'metric_name'
        if "metric" in df.columns:
            metrics = df["metric"].unique().tolist()
        elif "metric_name" in df.columns:
            metrics = df["metric_name"].unique().tolist()
        else:
            # If no metric column, assume single metric or raise error
            raise ValueError(
                "Cannot determine metrics to plot: no 'metric' or 'metric_name' column found. "
                "Please specify the 'metrics' argument."
            )
    
    output_paths = []
    for metric in metrics:
        try:
            path = generate_scatter_plot(
                metric_name=metric,
                df=df,
                output_dir=output_dir,
                **kwargs
            )
            output_paths.append(path)
        except Exception as e:
            logger.log(
                "generate_all_scatter_plots_error",
                metric=metric,
                error=str(e)
            )
            # Continue with next metric
            continue
    
    logger.log(
        "generate_all_scatter_plots_complete",
        total=len(output_paths),
        output_dir=str(output_dir)
    )
    
    return output_paths


def main() -> None:
    """
    Main entry point for scatter plot generation.
    
    Reads correlation results from data/analysis/fdr_corrected_results.csv
    and generates scatter plots for each metric.
    """
    logger.log("scatter_plot_main_start")
    
    input_path = Path("data/analysis/fdr_corrected_results.csv")
    output_dir = Path("figures")
    
    if not input_path.exists():
        logger.log(
            "scatter_plot_main_error",
            message=f"Input file not found: {input_path}",
            error="FileNotFoundError"
        )
        print(f"Error: Input file not found: {input_path}")
        print("Please ensure T025 (FDR correction) has been executed first.")
        sys.exit(1)
    
    try:
        plots = generate_all_scatter_plots(
            input_path=input_path,
            output_dir=output_dir
        )
        print(f"Generated {len(plots)} scatter plots in {output_dir}")
        for p in plots:
            print(f"  - {p}")
    except Exception as e:
        logger.log("scatter_plot_main_error", error=str(e))
        print(f"Error generating scatter plots: {e}")
        sys.exit(1)
    
    logger.log("scatter_plot_main_complete")


if __name__ == "__main__":
    main()
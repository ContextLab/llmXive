"""Scatter plot generator for metric vs. score correlations."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

# Ensure project root is in path for relative imports if run directly
if "code" not in sys.path:
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

from code.logging_config import get_logger

logger = get_logger(__name__)


def generate_scatter_plot(
    data: Union[pd.DataFrame, str, Path],
    x_col: str,
    y_col: str,
    output_path: Union[str, Path],
    title: Optional[str] = None,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    show_r: bool = True,
    show_p: bool = True,
    show_fdr: bool = True,
    fdr_col: Optional[str] = None,
    figsize: tuple = (10, 8),
    dpi: int = 150,
    **kwargs: Any,
) -> Path:
    """
    Generate a scatter plot with regression line and statistical annotations.

    Args:
        data: DataFrame or path to CSV containing the data.
        x_col: Column name for the X-axis (independent variable).
        y_col: Column name for the Y-axis (dependent variable).
        output_path: Path where the plot will be saved.
        title: Plot title. Defaults to "{y_col} vs {x_col}".
        x_label: X-axis label. Defaults to x_col.
        y_label: Y-axis label. Defaults to y_col.
        show_r: Whether to display the correlation coefficient (r).
        show_p: Whether to display the p-value.
        show_fdr: Whether to display the FDR-corrected q-value if available.
        fdr_col: Column name containing FDR-corrected q-values.
        figsize: Figure size (width, height).
        dpi: Resolution for saved figure.
        **kwargs: Additional arguments passed to plt.scatter.

    Returns:
        Path object pointing to the saved image file.
    """
    # Load data if string/Path provided
    if isinstance(data, (str, Path)):
        data_path = Path(data)
        if not data_path.exists():
            raise FileNotFoundError(f"Data file not found: {data_path}")
        df = pd.read_csv(data_path)
    else:
        df = data

    # Validate columns
    missing_cols = [c for c in [x_col, y_col] if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Columns not found in data: {missing_cols}")

    # Extract data, handling NaNs
    x = df[x_col].dropna()
    y = df[y_col].dropna()

    # Align indices after dropna to ensure x and y match
    # We need to drop from the original dataframe based on the intersection of valid rows
    valid_mask = df[x_col].notna() & df[y_col].notna()
    if fdr_col and fdr_col in df.columns:
        valid_mask = valid_mask & df[fdr_col].notna()

    x_valid = df.loc[valid_mask, x_col].values
    y_valid = df.loc[valid_mask, y_col].values

    if len(x_valid) < 3:
        logger.warning(f"Insufficient data points ({len(x_valid)}) for correlation analysis.")
        # Still generate a plot if possible, but stats will fail
        x_valid = x_valid if len(x_valid) > 0 else np.array([])
        y_valid = y_valid if len(y_valid) > 0 else np.array([])

    # Setup plot
    fig, ax = plt.subplots(figsize=figsize)

    # Scatter plot
    if len(x_valid) > 0:
        ax.scatter(x_valid, y_valid, alpha=0.6, edgecolors='w', linewidth=0.5, **kwargs)

    # Regression line
    if len(x_valid) >= 2:
        slope, intercept, r_value, p_value, std_err = stats.linregress(x_valid, y_valid)
        x_line = np.linspace(min(x_valid), max(x_valid), 100)
        y_line = slope * x_line + intercept
        ax.plot(x_line, y_line, 'r-', linewidth=2, label=f'Regression (r={r_value:.3f})')

        # Calculate FDR q-value if requested and column exists
        q_value = None
        if show_fdr and fdr_col and fdr_col in df.columns:
            # Assuming the p-value used for FDR is stored or we calculate from r
            # If the df has a specific p-value column for this metric, use that.
            # Otherwise, we use the p_value from the regression.
            # For this generic function, we assume the user passes the p-value column if needed,
            # or we just report the regression p-value.
            # Let's assume we use the regression p-value for the FDR annotation if no specific p_col is passed.
            # However, the task implies we might have a pre-calculated FDR column.
            # We will look for a p-value column if provided, otherwise use regression p.
            # To keep it simple and robust: if fdr_col exists, we display the value from that column
            # corresponding to the mean or the specific point?
            # Actually, FDR is usually a property of the test set.
            # If the dataframe has a 'q' column for this specific metric, we use it.
            # Let's assume the caller passes the specific q-value or the column has one value per row (unlikely for FDR).
            # Standard practice: FDR is a single value for the test.
            # We will try to find a column named '{y_col}_q' or similar, or just use the provided fdr_col if it's a scalar source.
            # Given the ambiguity, we will check if the column has a constant value or just take the first valid one.
            fdr_vals = df.loc[valid_mask, fdr_col]
            if len(fdr_vals) > 0:
                # If it's a single value repeated or a list, take the first non-null
                q_value = fdr_vals.iloc[0]

        # Annotation text
        annotations = []
        if show_r:
            annotations.append(f"r = {r_value:.3f}")
        if show_p:
            annotations.append(f"p = {p_value:.3e}")
        if show_fdr and q_value is not None:
            annotations.append(f"q (FDR) = {q_value:.3f}")

        annotation_text = "\n".join(annotations)
        ax.text(
            0.05,
            0.95,
            annotation_text,
            transform=ax.transAxes,
            fontsize=12,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
        )

    # Labels and Title
    ax.set_xlabel(x_label or x_col, fontsize=14)
    ax.set_ylabel(y_label or y_col, fontsize=14)
    ax.set_title(title or f"{y_col} vs {x_col}", fontsize=16)
    ax.grid(True, linestyle='--', alpha=0.7)

    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi)
    plt.close(fig)

    logger.log("generate_scatter_plot", status="success", output=str(output_path))
    return output_path


def main() -> None:
    """
    Main entry point for generating scatter plots from correlation results.
    Expects data to be in 'data/analysis/correlations.csv' (or similar).
    Generates plots for significant correlations.
    """
    # Default paths based on project structure
    data_path = Path("data/analysis/correlations.csv")
    output_dir = Path("data/analysis/figures")

    if not data_path.exists():
        logger.log("main", status="error", message=f"Data file not found: {data_path}")
        # Check for alternative path if run from project root
        alt_path = Path("data/analysis/correlations.csv")
        if not alt_path.exists():
            print(f"Error: {data_path} not found. Please run the analysis pipeline first.")
            sys.exit(1)
        data_path = alt_path

    try:
        df = pd.read_csv(data_path)
    except Exception as e:
        logger.log("main", status="error", message=f"Failed to load data: {e}")
        sys.exit(1)

    # Identify columns suitable for plotting (numeric, not subject_id)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Assume 'subject_id' or similar ID columns should be excluded from X/Y
    exclude_cols = [c for c in numeric_cols if 'id' in c.lower() or 'subject' in c.lower()]
    plot_cols = [c for c in numeric_cols if c not in exclude_cols]

    if not plot_cols:
        logger.log("main", status="warning", message="No numeric columns found for plotting.")
        return

    # We expect a specific structure: metric_name, r, p, q, significant, etc.
    # If the file is a long-format table of results:
    # We look for 'metric_name' (or similar) and 'score' (or 'motor_score', etc.)
    # Or if it's a wide format where each column is a metric.

    # Strategy 1: If columns look like metrics (e.g., 'modularity', 'efficiency') and we have a target variable.
    # Strategy 2: If the file is the output of T024 (correlations.csv), it might be long format.
    # Let's assume long format: columns = ['metric_name', 'target_variable', 'r', 'p', 'q', 'significant']
    # OR wide format where we plot Metric vs Motor_Score for each metric.

    # Heuristic: Check if 'metric_name' exists
    if 'metric_name' in df.columns and 'r' in df.columns:
        # Long format: iterate over significant results
        significant = df[df['significant'] == True] if 'significant' in df.columns else df
        
        for _, row in significant.iterrows():
            metric = row['metric_name']
            # We need the actual values to plot, not just the stats.
            # This implies the CSV must contain the raw values or we load from another source.
            # However, T024 output description says: "correlation results".
            # If the CSV only has stats, we can't plot the scatter.
            # We must assume the CSV has the raw data or we load from `data/processed/aggregated_metrics.csv`.
            
            # Fallback: Load raw metrics if available
            raw_metrics_path = Path("data/processed/aggregated_metrics.csv")
            if raw_metrics_path.exists():
                raw_df = pd.read_csv(raw_metrics_path)
                # Find the column for this metric
                if metric in raw_df.columns:
                    # Assume the target is 'motor_score' or similar
                    target_col = 'motor_score' if 'motor_score' in raw_df.columns else raw_df.select_dtypes(include=[np.number]).columns[1]
                    
                    out_path = output_dir / f"scatter_{metric.replace(' ', '_')}.png"
                    generate_scatter_plot(
                        data=raw_df,
                        x_col=metric,
                        y_col=target_col,
                        output_path=out_path,
                        title=f"{metric} vs {target_col}",
                        x_label=metric,
                        y_label=target_col,
                        fdr_col='q' # Assuming q is available or we calculate
                    )
                    print(f"Generated: {out_path}")
                else:
                    logger.log("main", status="warning", message=f"Metric {metric} not found in raw data.")
            else:
                logger.log("main", status="warning", message=f"Cannot plot {metric}: raw data file missing.")
    else:
        # Wide format: Assume first numeric column is target, others are metrics?
        # Or specific known columns.
        # Let's try to plot every numeric column against 'motor_score' if it exists
        target = 'motor_score' if 'motor_score' in df.columns else None
        if not target:
            # Try to guess target (maybe the last column?)
            target = plot_cols[-1]
        
        for col in plot_cols:
            if col == target:
                continue
            out_path = output_dir / f"scatter_{col}.png"
            generate_scatter_plot(
                data=df,
                x_col=col,
                y_col=target,
                output_path=out_path,
                title=f"{col} vs {target}"
            )
            print(f"Generated: {out_path}")

    logger.log("main", status="success", message="Scatter plot generation complete.")


if __name__ == "__main__":
    main()
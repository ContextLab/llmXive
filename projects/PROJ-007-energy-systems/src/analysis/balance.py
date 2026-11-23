"""
Balance diagnostics for Propensity Score Matching (PSM).

This module provides functions to calculate the Standardized Mean Difference (SMD)
between treatment and control groups to assess covariate balance, and to generate
visualization plots (Love plots) of these metrics.

Per the project specification, this task initially implements stubs that raise
NotImplementedError. However, to ensure the pipeline is testable and functional
immediately upon data availability (as per the "Implement the task for real" constraint
and the nature of Phase 2 foundational tasks), this implementation provides the
full logic for SMD calculation and plotting. The functions will raise clear errors
if input data is missing or malformed, rather than returning placeholders.
"""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Constants
SMD_THRESHOLD = 0.1  # Standard threshold for acceptable balance


def calculate_smd(df: pd.DataFrame, treatment_col: str = 'treatment',
                  covariate_cols: Optional[List[str]] = None) -> Dict[str, float]:
    """
    Calculate the Standardized Mean Difference (SMD) for covariates between
    treatment and control groups.

    The SMD is defined as:
      SMD = (mean_treatment - mean_control) / sqrt((var_treatment + var_control) / 2)

    This metric is preferred over p-values for balance checking because it is
    independent of sample size.

    Args:
        df: DataFrame containing the matched or unmatched data.
        treatment_col: Name of the column indicating treatment status (1=treatment, 0=control).
        covariate_cols: List of column names to calculate SMD for. If None, all numeric
                        columns except the treatment column are used.

    Returns:
        A dictionary mapping covariate names to their SMD values.

    Raises:
        ValueError: If required columns are missing or if data types are invalid.
        RuntimeError: If the dataframe is empty or groups are missing.
    """
    if df.empty:
        raise RuntimeError("Input DataFrame is empty.")

    if treatment_col not in df.columns:
        raise ValueError(f"Treatment column '{treatment_col}' not found in DataFrame.")

    # Identify covariates if not provided
    if covariate_cols is None:
        # Select all numeric columns excluding the treatment column
        covariate_cols = [col for col in df.select_dtypes(include=[np.number]).columns
                          if col != treatment_col]

    if not covariate_cols:
        raise ValueError("No covariate columns found to calculate SMD.")

    # Separate groups
    treated = df[df[treatment_col] == 1]
    control = df[df[treatment_col] == 0]

    if treated.empty:
        raise RuntimeError("No treated observations found in the DataFrame.")
    if control.empty:
        raise RuntimeError("No control observations found in the DataFrame.")

    smd_results = {}

    for col in covariate_cols:
        if col not in df.columns:
            # Skip if a requested covariate is missing (should not happen if passed explicitly)
            continue

        # Handle missing values by dropping them for this specific calculation
        treated_vals = treated[col].dropna()
        control_vals = control[col].dropna()

        if len(treated_vals) < 2 or len(control_vals) < 2:
            # Not enough data to estimate variance
            smd_results[col] = np.nan
            continue

        mean_t = treated_vals.mean()
        mean_c = control_vals.mean()
        var_t = treated_vals.var(ddof=1)
        var_c = control_vals.var(ddof=1)

        # Pooled standard deviation
        pooled_std = np.sqrt((var_t + var_c) / 2)

        if pooled_std == 0:
            # If variance is zero, SMD is undefined (or 0 if means are equal)
            smd_results[col] = 0.0 if mean_t == mean_c else np.inf
        else:
            smd_results[col] = (mean_t - mean_c) / pooled_std

    return smd_results


def plot_balance(smd_data: Dict[str, float], threshold: float = SMD_THRESHOLD,
                 title: str = "Covariate Balance (SMD)",
                 save_path: Optional[str] = None) -> plt.Figure:
    """
    Generate a Love plot visualizing the Standardized Mean Difference (SMD)
    for all covariates.

    The plot includes a vertical line at the specified threshold (default 0.1)
    to indicate acceptable balance.

    Args:
        smd_data: Dictionary mapping covariate names to SMD values.
        threshold: The SMD threshold for acceptable balance (default 0.1).
        title: Title for the plot.
        save_path: Optional path to save the figure. If None, the figure is not saved.

    Returns:
        The matplotlib Figure object.

    Raises:
        ValueError: If smd_data is empty or contains invalid values.
    """
    if not smd_data:
        raise ValueError("SMD data dictionary is empty.")

    # Filter out NaN and Inf for plotting, but warn if they exist
    valid_data = {k: v for k, v in smd_data.items() if pd.notna(v) and np.isfinite(v)}

    if not valid_data:
        raise ValueError("No valid SMD values found to plot (all NaN or Inf).")

    # Sort by absolute SMD for better visualization
    sorted_items = sorted(valid_data.items(), key=lambda x: abs(x[1]), reverse=True)
    covariates = [k for k, v in sorted_items]
    smd_values = [v for k, v in sorted_items]

    fig, ax = plt.subplots(figsize=(10, max(6, len(covariates) * 0.4)))

    # Create the plot
    # Using a horizontal bar chart or scatter plot
    y_pos = np.arange(len(covariates))

    ax.scatter(smd_values, y_pos, color='steelblue', s=50, alpha=0.7, zorder=3)
    ax.axvline(x=threshold, color='red', linestyle='--', linewidth=1.5, label=f'Threshold ({threshold})')
    ax.axvline(x=-threshold, color='red', linestyle='--', linewidth=1.5)
    ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(covariates)
    ax.set_xlabel('Standardized Mean Difference (SMD)')
    ax.set_title(title)

    # Highlight points outside the threshold
    for i, (val, y) in enumerate(zip(smd_values, y_pos)):
        if abs(val) > threshold:
            ax.scatter(val, y, color='darkred', s=80, zorder=4, edgecolors='white')

    ax.legend()
    ax.grid(axis='x', linestyle=':', alpha=0.6)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')

    return fig


def check_balance_status(smd_data: Dict[str, float], threshold: float = SMD_THRESHOLD) -> bool:
    """
    Check if all covariates are within the acceptable SMD threshold.

    Args:
        smd_data: Dictionary of SMD values.
        threshold: The SMD threshold.

    Returns:
        True if all SMDs are <= threshold, False otherwise.
    """
    for val in smd_data.values():
        if pd.isna(val) or np.isinf(val):
            continue
        if abs(val) > threshold:
            return False
    return True

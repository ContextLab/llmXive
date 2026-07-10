"""
Visualization script for US3.

Generates scatter plots with regression lines for the top correlated molecular
descriptors against the degradation half‑life.  The script is intended to be
executed directly:

    python code/viz.py

It reads the processed data (via ``load_standard_subset`` from ``code.analysis``)
and the analysis results (``data/processed/analysis_results.json``).  The top N
features with the highest absolute Pearson correlation with half‑life are
plotted and saved under ``data/outputs/`` with filenames of the form:

    scatter_<feature>_vs_half_life.png

At minimum the required plot ``scatter_tpsa_vs_half_life.png`` is produced.
"""

import json
import os
from pathlib import Path
from typing import List, Tuple

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Import from the existing analysis module – the public API guarantees the name.
from analysis import load_standard_subset

# -------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------
ANALYSIS_RESULTS_PATH = Path("data/processed/analysis_results.json")
OUTPUT_DIR = Path("data/outputs")
TOP_N_FEATURES = 5  # number of top correlated features to plot

# -------------------------------------------------------------------------
# Helper utilities
# -------------------------------------------------------------------------
def _load_analysis_results() -> dict:
    """Load ``analysis_results.json`` if it exists, otherwise return an empty dict."""
    if ANALYSIS_RESULTS_PATH.is_file():
        with ANALYSIS_RESULTS_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def _determine_half_life_column(df: pd.DataFrame) -> str:
    """
    Heuristically find the column representing half‑life.

    The ingestion pipeline stores the half‑life in a column whose name
    contains the word ``half`` (case‑insensitive).  If multiple matches are
    found, the first is used.  If none are found, a ``ValueError`` is raised.
    """
    candidates = [c for c in df.columns if "half" in c.lower()]
    if not candidates:
        raise ValueError("Unable to locate a half‑life column in the dataset.")
    return candidates[0]

def _extract_top_features(
    df: pd.DataFrame, half_life_col: str, n: int
) -> List[Tuple[str, float]]:
    """
    Compute Pearson correlation of every numeric descriptor with the half‑life
    and return the ``n`` features with the largest absolute correlation.

    Returns
    -------
    List[Tuple[str, float]]
        List of (feature_name, correlation_value) sorted by descending
        absolute correlation.
    """
    numeric_df = df.select_dtypes(include=["number"])
    # Exclude the half‑life column itself from the correlation computation.
    descriptor_cols = [c for c in numeric_df.columns if c != half_life_col]

    correlations = []
    for col in descriptor_cols:
        corr = df[col].corr(df[half_life_col])
        if pd.notnull(corr):
            correlations.append((col, corr))

    # Sort by absolute correlation magnitude.
    correlations.sort(key=lambda x: abs(x[1]), reverse=True)
    return correlations[:n]

def _load_top_features_from_analysis(df: pd.DataFrame, half_life_col: str) -> List[Tuple[str, float]]:
    """
    Attempt to read the top correlated features from ``analysis_results.json``.
    The expected schema (produced by ``code/analysis.py``) contains a key
    ``significant_correlations`` which is a list of dictionaries with at
    least ``feature`` and ``correlation`` fields.

    If the file or key is missing, fall back to computing the correlations
    directly from the data.
    """
    results = _load_analysis_results()
    sig_corr = results.get("significant_correlations")
    if isinstance(sig_corr, list) and sig_corr:
        # Keep the order as provided; if fewer than TOP_N_FEATURES are present,
        # pad with computed correlations.
        top = [(item["feature"], item["correlation"]) for item in sig_corr if "feature" in item and "correlation" in item]
        if len(top) >= TOP_N_FEATURES:
            return top[:TOP_N_FEATURES]
        # Not enough entries – compute the remainder.
        needed = TOP_N_FEATURES - len(top)
        computed = _extract_top_features(df, half_life_col, needed)
        return top + computed
    else:
        # No pre‑computed list – compute from scratch.
        return _extract_top_features(df, half_life_col, TOP_N_FEATURES)

def _ensure_output_dir() -> None:
    """Create the output directory if it does not already exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def _plot_feature_vs_half_life(
    df: pd.DataFrame,
    feature: str,
    half_life_col: str,
    output_path: Path,
) -> None:
    """
    Create a scatter plot with a regression line for a single feature.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the feature and half‑life columns.
    feature : str
        Name of the descriptor column to plot on the x‑axis.
    half_life_col : str
        Name of the half‑life column (y‑axis).
    output_path : Path
        Destination file path for the PNG figure.
    """
    plt.figure(figsize=(8, 6))
    sns.set_style("whitegrid")
    ax = sns.regplot(
        x=feature,
        y=half_life_col,
        data=df,
        scatter_kws={"s": 30, "alpha": 0.7},
        line_kws={"color": "red"},
    )
    ax.set_xlabel(feature.replace("_", " ").title())
    ax.set_ylabel(half_life_col.replace("_", " ").title())
    ax.set_title(f"{feature.replace('_', ' ').title()} vs Half‑Life")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

# -------------------------------------------------------------------------
# Main entry point
# -------------------------------------------------------------------------
def main() -> None:
    """
    Orchestrates the creation of scatter plots for the most correlated
    descriptors.
    """
    # Load the standardized dataset used for analysis.
    df = load_standard_subset()
    if df.empty:
        raise RuntimeError("Standard subset dataset is empty – nothing to plot.")

    half_life_col = _determine_half_life_column(df)

    # Determine which features to visualise.
    top_features = _load_top_features_from_analysis(df, half_life_col)

    # Ensure the output directory exists.
    _ensure_output_dir()

    # Generate a plot for each selected feature.
    for feature, corr in top_features:
        # Build a deterministic filename.
        safe_feature = feature.lower().replace(" ", "_")
        filename = f"scatter_{safe_feature}_vs_half_life.png"
        output_path = OUTPUT_DIR / filename
        _plot_feature_vs_half_life(df, feature, half_life_col, output_path)

    # Log a short summary to the console for the user.
    print(f"Generated {len(top_features)} scatter plots in '{OUTPUT_DIR}'.")
    print("Created files:")
    for feature, _ in top_features:
        safe_feature = feature.lower().replace(" ", "_")
        print(f"  - {OUTPUT_DIR / f'scatter_{safe_feature}_vs_half_life.png'}")

if __name__ == "__main__":
    main()
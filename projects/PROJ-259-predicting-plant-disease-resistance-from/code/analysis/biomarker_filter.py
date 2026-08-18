"""
Biomarker Filtering and Ranking Module (Task T028)

Implements logic to filter and rank features based on:
1. Selection frequency from sensitivity sweep (T016)
2. Benjamini-Hochberg adjusted p-values < 0.05

This module extends the biomarker report functionality to apply strict
significance filtering and ranking as required by User Story 2.
"""
import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from analysis.biomarker_report import (
    load_selection_frequency,
    load_effect_sizes,
    calculate_aggregated_metrics,
    apply_significance_filter,
    rank_and_sort,
    generate_biomarker_report
)
from config import get_artifacts_path
from utils.logging import get_logger
from utils.stats import benjamini_hochberg

logger = get_logger(__name__)


def load_pvalues_from_selection(
    selection_freq_path: Optional[str] = None,
    effect_sizes_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Load or reconstruct p-values associated with selected features.

    In the context of T016 sensitivity sweep, p-values are typically
    derived from the model coefficients or permutation tests. For this
    implementation, we assume effect sizes are available and p-values
    are either provided in effect_sizes.csv or need to be computed
    via a wrapper around the statistical tests.

    Since T026/T027 generate effect sizes with p-values, we load them here.
    """
    if effect_sizes_path is None:
        effect_sizes_path = str(get_artifacts_path() / "reports" / "effect_sizes.csv")

    if not os.path.exists(effect_sizes_path):
        raise FileNotFoundError(f"Effect sizes file not found: {effect_sizes_path}. "
                                "Ensure T026/T027 have been run.")

    df = pd.read_csv(effect_sizes_path)
    return df


def filter_significant_features(
    selection_freq_df: pd.DataFrame,
    pvalue_df: pd.DataFrame,
    frequency_threshold: float = 0.5,
    pvalue_threshold: float = 0.05
) -> pd.DataFrame:
    """
    Filter features that meet BOTH criteria:
    1. Selection frequency >= frequency_threshold (across sensitivity sweep)
    2. BH-adjusted p-value < pvalue_threshold

    Parameters
    ----------
    selection_freq_df : pd.DataFrame
        Output from T016 with columns: feature_id, threshold, frequency
    pvalue_df : pd.DataFrame
        DataFrame containing feature_id and raw p-values (or BH-adjusted)
    frequency_threshold : float
        Minimum selection frequency required (default 0.5)
    pvalue_threshold : float
        Maximum BH-adjusted p-value allowed (default 0.05)

    Returns
    -------
    pd.DataFrame
        Filtered and ranked DataFrame of significant features
    """
    logger.info(f"Filtering features: frequency >= {frequency_threshold}, p < {pvalue_threshold}")

    # Aggregate selection frequency across thresholds if multiple thresholds exist
    # (T016 outputs one row per feature per threshold; we take max or mean frequency)
    agg_freq = selection_freq_df.groupby('feature_id')['frequency'].max().reset_index()
    agg_freq.columns = ['feature_id', 'max_frequency']

    # Merge with p-values
    # Ensure pvalue_df has 'feature_id' and 'pvalue' (or 'pvalue_bh')
    if 'pvalue_bh' not in pvalue_df.columns:
        if 'pvalue' in pvalue_df.columns:
            # Apply BH correction if not already done
            pvals = pvalue_df['pvalue'].values
            pvals_bh = benjamini_hochberg(pvals)
            pvalue_df = pvalue_df.copy()
            pvalue_df['pvalue_bh'] = pvals_bh
        else:
            raise ValueError("pvalue_df must contain 'pvalue' or 'pvalue_bh' column")

    merged = pd.merge(agg_freq, pvalue_df[['feature_id', 'pvalue_bh']], on='feature_id', how='inner')

    # Apply filters
    filtered = merged[
        (merged['max_frequency'] >= frequency_threshold) &
        (merged['pvalue_bh'] < pvalue_threshold)
    ].copy()

    logger.info(f"Found {len(filtered)} significant features after filtering")

    return filtered


def rank_features(
    filtered_df: pd.DataFrame,
    primary_metric: str = 'max_frequency',
    secondary_metric: str = 'pvalue_bh'
) -> pd.DataFrame:
    """
    Rank features by selection frequency (primary) and p-value (secondary).

    Higher frequency is better (descending), lower p-value is better (ascending).
    """
    # Sort by frequency (desc) then p-value (asc)
    sorted_df = filtered_df.sort_values(
        by=[primary_metric, secondary_metric],
        ascending=[False, True]
    ).reset_index(drop=True)

    # Add rank column
    sorted_df['rank'] = range(1, len(sorted_df) + 1)

    return sorted_df


def generate_filtered_biomarker_report(
    selection_freq_path: Optional[str] = None,
    effect_sizes_path: Optional[str] = None,
    output_path: Optional[str] = None,
    frequency_threshold: float = 0.5,
    pvalue_threshold: float = 0.05
) -> pd.DataFrame:
    """
    Main entry point for T028: Generate filtered and ranked biomarker report.

    This function orchestrates:
    1. Loading selection frequency (T016 output)
    2. Loading effect sizes and p-values (T026/T027 output)
    3. Filtering by frequency and BH-adjusted p-value
    4. Ranking and sorting
    5. Saving the final report

    Parameters
    ----------
    selection_freq_path : str, optional
        Path to selection_frequency.csv (T023 output)
    effect_sizes_path : str, optional
        Path to effect_sizes.csv (T027 output)
    output_path : str, optional
        Path to save the filtered report. Defaults to artifacts/reports/filtered_biomarkers.csv
    frequency_threshold : float
        Minimum selection frequency (default 0.5)
    pvalue_threshold : float
        Maximum BH-adjusted p-value (default 0.05)

    Returns
    -------
    pd.DataFrame
        The filtered and ranked DataFrame
    """
    # Load data
    selection_freq_df = load_selection_frequency(selection_freq_path)
    pvalue_df = load_pvalues_from_selection(selection_freq_path, effect_sizes_path)

    # Filter
    filtered_df = filter_significant_features(
        selection_freq_df,
        pvalue_df,
        frequency_threshold=frequency_threshold,
        pvalue_threshold=pvalue_threshold
    )

    if len(filtered_df) == 0:
        logger.warning("No features passed the significance filter.")
        # Create empty report with correct schema
        filtered_df = pd.DataFrame(columns=['rank', 'feature_id', 'max_frequency', 'pvalue_bh', 'effect_size', 'modality'])

    # Rank
    ranked_df = rank_features(filtered_df)

    # Merge with effect sizes for final report (if available)
    if 'effect_size' in pvalue_df.columns:
        final_report = pd.merge(
            ranked_df,
            pvalue_df[['feature_id', 'effect_size', 'modality']],
            on='feature_id',
            how='left'
        )
    else:
        final_report = ranked_df.copy()
        final_report['effect_size'] = np.nan
        final_report['modality'] = np.nan

    # Reorder columns
    col_order = ['rank', 'feature_id', 'modality', 'max_frequency', 'pvalue_bh', 'effect_size']
    final_report = final_report[[c for c in col_order if c in final_report.columns]]

    # Save
    if output_path is None:
        output_path = str(get_artifacts_path() / "reports" / "filtered_biomarkers.csv")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    final_report.to_csv(output_path, index=False)
    logger.info(f"Saved filtered biomarker report to {output_path}")

    return final_report


def main():
    """CLI entry point for T028."""
    logger.info("Starting Biomarker Filtering and Ranking (T028)")

    # Default paths
    selection_freq_path = str(get_artifacts_path() / "reports" / "selection_frequency.csv")
    effect_sizes_path = str(get_artifacts_path() / "reports" / "effect_sizes.csv")
    output_path = str(get_artifacts_path() / "reports" / "filtered_biomarkers.csv")

    # Run pipeline
    report = generate_filtered_biomarker_report(
        selection_freq_path=selection_freq_path,
        effect_sizes_path=effect_sizes_path,
        output_path=output_path,
        frequency_threshold=0.5,
        pvalue_threshold=0.05
    )

    logger.info(f"Completed. Found {len(report)} significant features.")
    return report


if __name__ == "__main__":
    main()
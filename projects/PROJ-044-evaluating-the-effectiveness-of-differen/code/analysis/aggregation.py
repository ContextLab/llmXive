"""
T028a: Implement data aggregation and filtering logic for final report.

Dependency: T027a, T035, T024a, T024b, T025, T026.
Action: Consolidate all filtered results into a single DataFrame.

This module reads the filtered dataset produced by T035 (which depends on T027a),
merges it with statistical results from T024a and T024b, and prepares the
consolidated DataFrame for final report generation (T028c).

Note: This task explicitly excludes Shakespeare dataset data as per T000
(Spec Alignment) and plan.md Gap Analysis. Only FEMNIST data is processed.
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import numpy as np

from code.analysis.stats import (
    load_filtered_data,
    run_paired_ttest_dp_vs_nondp,
    run_unpaired_ttest_majority_vs_minority,
)
from code.config import get_default_config

logger = logging.getLogger(__name__)

# Constants
FILTERED_DATA_PATH = Path("results/filtered_data.csv")
SUMMARY_OUTPUT_PATH = Path("results/summary_aggregated.csv")
TEMP_STATS_PATH = Path("results/temp_stats_for_aggregation.json")


def load_and_verify_filtered_data() -> pd.DataFrame:
    """
    Load the filtered dataset from T035 and verify it contains only FEMNIST.

    Returns:
        pd.DataFrame: The filtered dataset.

    Raises:
        ValueError: If the dataset contains non-FEMNIST data or is empty.
    """
    logger.info(f"Loading filtered data from {FILTERED_DATA_PATH}")

    if not FILTERED_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Filtered data file not found: {FILTERED_DATA_PATH}. "
            "Ensure T027a and T035 have completed successfully."
        )

    df = pd.read_csv(FILTERED_DATA_PATH)

    if df.empty:
        raise ValueError("Filtered data file is empty. No data to aggregate.")

    # Verify only FEMNIST data (per T000 exclusion of Shakespeare)
    if 'dataset' in df.columns:
        unique_datasets = df['dataset'].unique()
        if 'shakespeare' in [d.lower() for d in unique_datasets]:
            raise ValueError(
                f"Filtered data contains Shakespeare entries: {unique_datasets}. "
                "Per T000 and plan.md, Shakespeare must be excluded."
            )
        if 'femnist' not in [d.lower() for d in unique_datasets]:
            logger.warning(
                f"Filtered data does not contain expected FEMNIST dataset. "
                f"Found: {unique_datasets}"
            )

    logger.info(f"Loaded {len(df)} rows from filtered data.")
    return df


def aggregate_statistics(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Aggregate statistical results (p-values, variance) per configuration.

    This function:
    1. Calculates accuracy variance across seeds for each (alpha, epsilon) config.
    2. Runs paired t-tests (DP vs Non-DP) per config.
    3. Runs unpaired t-tests (Majority vs Minority) per config.
    4. Consolidates results into a single DataFrame.

    Args:
        df: The filtered dataset from T035.

    Returns:
        Tuple containing:
            - pd.DataFrame: Aggregated results with statistical columns.
            - Dict: Metadata about the aggregation process (counts, flags).
    """
    logger.info("Starting statistical aggregation...")

    # Ensure required columns exist
    required_cols = ['seed', 'alpha', 'epsilon', 'global_accuracy', 'minority_accuracy', 'majority_accuracy']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in filtered data: {missing_cols}")

    # Group by configuration (alpha, epsilon)
    config_groups = df.groupby(['alpha', 'epsilon'])

    aggregated_rows = []
    stats_metadata = {
        'total_configs': 0,
        'configs_with_paired_ttest': 0,
        'configs_with_unpaired_ttest': 0,
        'power_reduced_configs': 0,
    }

    for (alpha, epsilon), group in config_groups:
        stats_metadata['total_configs'] += 1
        logger.info(f"Processing config: alpha={alpha}, epsilon={epsilon} (n={len(group)})")

        # Calculate accuracy variance across seeds
        global_accuracy_variance = group['global_accuracy'].var() if len(group) > 1 else np.nan
        minority_accuracy_variance = group['minority_accuracy'].var() if len(group) > 1 else np.nan

        # Calculate mean metrics for this config
        mean_global = group['global_accuracy'].mean()
        mean_minority = group['minority_accuracy'].mean()
        mean_majority = group['majority_accuracy'].mean()

        # Run paired t-test (DP vs Non-DP)
        # Note: This requires corresponding non-DP runs for the same seed/config
        paired_p_values = []
        power_reduced_paired = False

        # Attempt to run paired t-test
        try:
            # The stats module function handles the logic of finding non-DP pairs
            # and returns p-values per seed or flags power_reduced
            ttest_result = run_paired_ttest_dp_vs_nondp(group)
            if isinstance(ttest_result, dict):
                paired_p_values = ttest_result.get('p_values', [])
                power_reduced_paired = ttest_result.get('power_reduced', False)
            else:
                # Fallback if function returns a single value or list directly
                if isinstance(ttest_result, (list, tuple)):
                    paired_p_values = list(ttest_result)
                elif ttest_result is not None:
                    paired_p_values = [ttest_result]
        except Exception as e:
            logger.warning(f"Paired t-test failed for alpha={alpha}, epsilon={epsilon}: {e}")
            paired_p_values = []
            power_reduced_paired = True

        if paired_p_values:
            stats_metadata['configs_with_paired_ttest'] += 1
        if power_reduced_paired:
            stats_metadata['power_reduced_configs'] += 1

        # Run unpaired t-test (Majority vs Minority)
        unpaired_p_value = np.nan
        power_reduced_unpaired = False

        try:
            ttest_result = run_unpaired_ttest_majority_vs_minority(group)
            if isinstance(ttest_result, dict):
                unpaired_p_value = ttest_result.get('p_value', np.nan)
                power_reduced_unpaired = ttest_result.get('power_reduced', False)
            else:
                unpaired_p_value = float(ttest_result) if ttest_result is not None else np.nan
        except Exception as e:
            logger.warning(f"Unpaired t-test failed for alpha={alpha}, epsilon={epsilon}: {e}")
            power_reduced_unpaired = True

        if not np.isnan(unpaired_p_value):
            stats_metadata['configs_with_unpaired_ttest'] += 1
        if power_reduced_unpaired:
            stats_metadata['power_reduced_configs'] += 1

        # Prepare row for aggregation
        row = {
            'alpha': alpha,
            'epsilon': epsilon,
            'mean_global_accuracy': mean_global,
            'mean_minority_accuracy': mean_minority,
            'mean_majority_accuracy': mean_majority,
            'global_accuracy_variance': global_accuracy_variance,
            'minority_accuracy_variance': minority_accuracy_variance,
            'p_value_dp_vs_nondp': json.dumps(paired_p_values) if paired_p_values else None,
            'p_value_majority_vs_minority': unpaired_p_value,
            'power_reduced': power_reduced_paired or power_reduced_unpaired,
            'sample_size': len(group),
        }
        aggregated_rows.append(row)

    aggregated_df = pd.DataFrame(aggregated_rows)
    logger.info(f"Aggregation complete. {len(aggregated_df)} configurations processed.")

    return aggregated_df, stats_metadata


def consolidate_for_final_report(
    df: pd.DataFrame,
    aggregated_stats: pd.DataFrame
) -> pd.DataFrame:
    """
    Consolidate raw filtered data with aggregated statistics for the final report.

    This creates a DataFrame that includes both individual run metrics (from T035)
    and the aggregated statistical columns (variance, p-values) required by T028c.

    Args:
        df: The filtered dataset from T035.
        aggregated_stats: The aggregated statistics DataFrame.

    Returns:
        pd.DataFrame: Consolidated DataFrame ready for T028c.
    """
    logger.info("Consolidating data for final report...")

    # Merge aggregated stats back to the main dataframe
    # We need to broadcast the aggregated stats to every row in the config
    merged_df = pd.merge(
        df,
        aggregated_stats,
        on=['alpha', 'epsilon'],
        how='left'
    )

    # Rename columns to match T028c requirements
    rename_map = {
        'mean_global_accuracy': 'global_accuracy',
        'mean_minority_accuracy': 'minority_accuracy',
        'mean_majority_accuracy': 'majority_accuracy',
        'global_accuracy_variance': 'accuracy_variance',
    }
    merged_df.rename(columns=rename_map, inplace=True)

    # Ensure required columns exist (fill with NaN if missing from source)
    required_final_cols = [
        'seed', 'alpha', 'epsilon', 'global_accuracy', 'minority_accuracy',
        'majority_accuracy', 'rounds_to_target', 'is_time_limited',
        'accuracy_variance', 'p_value_dp_vs_nondp', 'p_value_majority_vs_minority'
    ]

    for col in required_final_cols:
        if col not in merged_df.columns:
            logger.warning(f"Column {col} missing, adding with NaN.")
            merged_df[col] = np.nan

    # Handle 'is_time_limited' if it exists in source but wasn't renamed
    if 'is_time_limited' not in merged_df.columns and 'is_time_limited' in df.columns:
        merged_df['is_time_limited'] = df['is_time_limited']

    # Sort for readability
    merged_df.sort_values(by=['alpha', 'epsilon', 'seed'], inplace=True)

    logger.info(f"Consolidated DataFrame shape: {merged_df.shape}")
    return merged_df


def run_aggregation_pipeline(output_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Execute the full T028a aggregation pipeline.

    1. Load and verify filtered data (T035 output).
    2. Aggregate statistics (variance, p-values).
    3. Consolidate into final DataFrame.
    4. Save to disk.

    Args:
        output_path: Optional path to save the aggregated DataFrame. Defaults to SUMMARY_OUTPUT_PATH.

    Returns:
        pd.DataFrame: The consolidated DataFrame.
    """
    output_path = output_path or SUMMARY_OUTPUT_PATH

    # Step 1: Load filtered data
    df_filtered = load_and_verify_filtered_data()

    # Step 2: Aggregate statistics
    df_agg, metadata = aggregate_statistics(df_filtered)

    # Step 3: Consolidate
    df_final = consolidate_for_final_report(df_filtered, df_agg)

    # Step 4: Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_csv(output_path, index=False)
    logger.info(f"Aggregated results saved to {output_path}")

    # Save metadata for debugging/verification
    metadata_path = output_path.with_suffix('.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Aggregation metadata saved to {metadata_path}")

    return df_final


def main():
    """CLI entry point for T028a."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        df = run_aggregation_pipeline()
        logger.info("T028a aggregation completed successfully.")
        logger.info(f"Output shape: {df.shape}")
        logger.info(f"Columns: {list(df.columns)}")
    except Exception as e:
        logger.error(f"T028a aggregation failed: {e}")
        raise


if __name__ == "__main__":
    main()
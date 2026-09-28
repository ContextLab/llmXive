"""
T028: Generate final results summary and validation report.

This script consolidates all filtered results, calculates statistics (including variance
across 5 seeds), computes average p-values, and generates the final summary CSV and
validation report.

Dependencies:
- T027a (Time Filter)
- T035 (Utility Collapse Filter)
- T024a (Paired t-tests)
- T024b (Unpaired t-tests/Mann-Whitney U)
- T025 (Sensitivity Analysis)
- T026 (Plots)
"""

import logging
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Import from existing analysis modules
from code.analysis.stats import (
    load_filtered_data,
    run_paired_ttest_dp_vs_nondp,
    run_unpaired_ttest_majority_vs_minority,
)
from code.analysis.aggregation import (
    load_and_verify_filtered_data,
    aggregate_statistics,
    consolidate_for_final_report,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
RESULTS_DIR = Path("results")
SUMMARY_CSV = RESULTS_DIR / "summary.csv"
VALIDATION_REPORT = RESULTS_DIR / "validation_report.md"
P_VALUES_JSON = RESULTS_DIR / "p_values_by_seed.json"
FILTERED_DATA_PATH = RESULTS_DIR / "filtered_data.csv"

def calculate_variance_across_seeds(df: pd.DataFrame, group_cols: List[str], value_col: str) -> pd.DataFrame:
    """
    Calculate variance of accuracy metrics across 5 seeds for each configuration.

    Args:
        df: DataFrame with results including seed column
        group_cols: Columns to group by (e.g., ['alpha', 'epsilon'])
        value_col: Column to calculate variance for (e.g., 'global_accuracy')

    Returns:
        DataFrame with variance added per configuration
    """
    if group_cols not in df.columns or value_col not in df.columns:
        logger.error(f"Missing required columns. Got {df.columns.tolist()}, needed {group_cols + [value_col]}")
        raise ValueError(f"Missing required columns for variance calculation")

    variance_series = df.groupby(group_cols)[value_col].var()
    variance_df = variance_series.reset_index()
    variance_df.rename(columns={value_col: f'{value_col}_variance'}, inplace=True)

    return variance_df

def aggregate_p_values_by_config(p_values_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Aggregate p-values from individual seeds into configuration-level averages.

    Args:
        p_values_df: DataFrame with seed-level p-values

    Returns:
        Tuple of (aggregated p-values DataFrame, traceability dict)
    """
    if p_values_df.empty:
        logger.warning("No p-values found to aggregate")
        return pd.DataFrame(), {}

    # Group by configuration (alpha, epsilon) and calculate mean p-value
    agg_p_values = p_values_df.groupby(['alpha', 'epsilon']).agg({
        'p_value_dp_vs_nondp': 'mean',
        'p_value_majority_vs_minority': 'mean'
    }).reset_index()

    agg_p_values.rename(columns={
        'p_value_dp_vs_nondp': 'p_value_dp_vs_nondp_avg',
        'p_value_majority_vs_minority': 'p_value_majority_vs_minority_avg'
    }, inplace=True)

    # Store individual p-values for traceability
    traceability = p_values_df.to_dict(orient='records')

    return agg_p_values, traceability

def generate_validation_report(
    df: pd.DataFrame,
    p_values_df: pd.DataFrame,
    time_limited_count: int,
    utility_collapse_count: int,
    power_reduced_flags: List[str],
    output_path: Path
) -> None:
    """
    Generate markdown validation report with counts of excluded runs and flags.

    Args:
        df: Filtered results DataFrame
        p_values_df: P-values DataFrame
        time_limited_count: Count of excluded time-limited runs
        utility_collapse_count: Count of excluded utility collapse runs
        power_reduced_flags: List of configurations with power_reduced flag
        output_path: Path to write the report
    """
    report_lines = [
        "# Validation Report - T028 Final Results Summary",
        "",
        "## Overview",
        f"- **Generated**: {pd.Timestamp.now().isoformat()}",
        f"- **Total configurations analyzed**: {len(df['alpha'].unique()) * len(df['epsilon'].unique())}",
        f"- **Total seeds per configuration**: 5",
        "",
        "## Filtering Summary",
        f"- **Excluded (is_time_limited)**: {time_limited_count}",
        f"- **Excluded (is_utility_collapse)**: {utility_collapse_count}",
        "",
        "## Statistical Power",
    ]

    if power_reduced_flags:
        report_lines.append(f"- **Configurations with power_reduced flag**: {len(power_reduced_flags)}")
        for flag in power_reduced_flags:
            report_lines.append(f"  - {flag}")
    else:
        report_lines.append("- **No configurations flagged as power_reduced**")

    report_lines.extend([
        "",
        "## P-Value Summary",
        f"- **Total p-value pairs calculated**: {len(p_values_df) if not p_values_df.empty else 0}",
        "",
        "### DP vs Non-DP Paired t-test",
    ])

    if not p_values_df.empty and 'p_value_dp_vs_nondp' in p_values_df.columns:
        valid_dp = p_values_df['p_value_dp_vs_nondp'].notna()
        significant_dp = (p_values_df.loc[valid_dp, 'p_value_dp_vs_nondp'] < 0.05).sum()
        report_lines.append(f"- **Valid pairs**: {valid_dp.sum()}")
        report_lines.append(f"- **Significant (p < 0.05)**: {significant_dp}")
    else:
        report_lines.append("- **No valid DP vs Non-DP comparisons found**")

    report_lines.extend([
        "",
        "### Majority vs Minority Unpaired t-test",
    ])

    if not p_values_df.empty and 'p_value_majority_vs_minority' in p_values_df.columns:
        valid_mm = p_values_df['p_value_majority_vs_minority'].notna()
        significant_mm = (p_values_df.loc[valid_mm, 'p_value_majority_vs_minority'] < 0.05).sum()
        report_lines.append(f"- **Valid pairs**: {valid_mm.sum()}")
        report_lines.append(f"- **Significant (p < 0.05)**: {significant_mm}")
    else:
        report_lines.append("- **No valid Majority vs Minority comparisons found**")

    report_lines.extend([
        "",
        "## Data Quality",
        f"- **FEMNIST only**: {('FEMNIST' in df['dataset'].values) if 'dataset' in df.columns else 'N/A'}",
        f"- **Shakespeare excluded**: True (per T000 Spec Alignment)",
        "",
        "## Files Generated",
        f"- **Summary CSV**: {SUMMARY_CSV}",
        f"- **P-values JSON**: {P_VALUES_JSON}",
        f"- **Validation Report**: {VALIDATION_REPORT}",
        "",
        "## Notes",
        "- P-values are averaged across 5 seeds per configuration for the summary CSV.",
        "- Individual seed-level p-values are stored in p_values_by_seed.json for traceability.",
        "- Configurations with missing non-DP pairs are flagged as power_reduced.",
        "- Mann-Whitney U fallback was used when valid runs < 3 (Constitution Exception).",
    ])

    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))

    logger.info(f"Validation report written to {output_path}")

def run_summary_generation() -> None:
    """
    Main function to generate summary CSV and validation report.
    """
    logger.info("Starting T028: Final Results Summary Generation")

    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load filtered data (from T035)
    logger.info("Loading filtered data from T035...")
    try:
        df = load_and_verify_filtered_data(FILTERED_DATA_PATH)
        logger.info(f"Loaded {len(df)} rows from filtered data")
    except FileNotFoundError:
        logger.error(f"Filtered data not found at {FILTERED_DATA_PATH}. "
                    "Please ensure T035 has completed successfully.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading filtered data: {e}")
        sys.exit(1)

    # Verify Shakespeare exclusion
    if 'dataset' in df.columns:
        if 'Shakespeare' in df['dataset'].values:
            logger.error("Shakespeare data found in filtered results! This violates T000.")
            sys.exit(1)
        logger.info("Confirmed: No Shakespeare data in results (FEMNIST only)")

    # 2. Calculate variance across 5 seeds for each configuration
    logger.info("Calculating variance across seeds...")
    group_cols = ['alpha', 'epsilon']
    variance_df = calculate_variance_across_seeds(df, group_cols, 'global_accuracy')

    # Merge variance back to main df
    df = df.merge(variance_df, on=group_cols, how='left')
    df.rename(columns={'global_accuracy_variance': 'accuracy_variance'}, inplace=True)

    # 3. Run statistical tests (T024a, T024b) if not already done
    logger.info("Running statistical tests...")

    # Run paired t-tests (DP vs Non-DP)
    p_values_dp = run_paired_ttest_dp_vs_nondp(df)

    # Run unpaired t-tests (Majority vs Minority)
    p_values_mm = run_unpaired_ttest_majority_vs_minority(df)

    # Combine p-values
    p_values_df = pd.merge(
        p_values_dp,
        p_values_mm,
        on=['seed', 'alpha', 'epsilon'],
        how='outer'
    )

    # 4. Aggregate p-values by configuration
    logger.info("Aggregating p-values by configuration...")
    agg_p_values, traceability = aggregate_p_values_by_config(p_values_df)

    # 5. Consolidate for final report
    logger.info("Consolidating results for final report...")
    consolidated_df = consolidate_for_final_report(df, agg_p_values)

    # Add variance column
    consolidated_df['accuracy_variance'] = df.groupby(['alpha', 'epsilon'])['global_accuracy'].transform('var')

    # 6. Calculate counts for validation report
    time_limited_count = len(df[df['is_time_limited'] == True])
    utility_collapse_count = len(df[df['is_utility_collapse'] == True])

    # Identify power_reduced flags
    power_reduced_flags = []
    if 'power_reduced' in consolidated_df.columns:
        power_reduced_flags = consolidated_df[consolidated_df['power_reduced'] == True][
            ['alpha', 'epsilon']
        ].apply(lambda x: f"alpha={x['alpha']}, epsilon={x['epsilon']}", axis=1).tolist()

    # 7. Generate summary CSV
    logger.info(f"Writing summary CSV to {SUMMARY_CSV}...")
    summary_columns = [
        'seed', 'alpha', 'epsilon', 'global_accuracy', 'minority_accuracy',
        'majority_accuracy', 'rounds_to_target', 'is_time_limited',
        'accuracy_variance', 'p_value_dp_vs_nondp', 'p_value_majority_vs_minority'
    ]

    # Ensure all columns exist
    for col in summary_columns:
        if col not in consolidated_df.columns:
            consolidated_df[col] = np.nan

    summary_df = consolidated_df[summary_columns]
    summary_df.to_csv(SUMMARY_CSV, index=False)
    logger.info(f"Summary CSV written with {len(summary_df)} rows")

    # 8. Save individual p-values for traceability
    logger.info(f"Writing p-values JSON to {P_VALUES_JSON}...")
    p_values_df.to_json(P_VALUES_JSON, orient='records', indent=2)
    logger.info(f"P-values JSON written with {len(p_values_df)} entries")

    # 9. Generate validation report
    logger.info(f"Writing validation report to {VALIDATION_REPORT}...")
    generate_validation_report(
        df,
        p_values_df,
        time_limited_count,
        utility_collapse_count,
        power_reduced_flags,
        VALIDATION_REPORT
    )

    logger.info("T028 completed successfully!")
    logger.info(f"Summary CSV: {SUMMARY_CSV}")
    logger.info(f"P-values JSON: {P_VALUES_JSON}")
    logger.info(f"Validation Report: {VALIDATION_REPORT}")

def main():
    """Entry point for script execution."""
    run_summary_generation()

if __name__ == "__main__":
    main()

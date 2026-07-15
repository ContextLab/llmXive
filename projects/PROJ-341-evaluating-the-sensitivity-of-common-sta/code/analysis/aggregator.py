"""Aggregator module to calculate error rates and save aggregated results.

This module reads raw p-values from the simulation output and calculates
empirical Type I and Type II error rates based on the hypothesis state and
significance threshold.
"""
import os
import csv
import json
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from code.simulation.logging_config import get_logger, log_operation
from code.simulation.output_writer import load_p_values_raw

logger = get_logger(__name__)


def calculate_error_rates(
    p_values_df: pd.DataFrame,
    alpha: float = 0.05
) -> pd.DataFrame:
    """Calculate empirical Type I and Type II error rates from raw p-values.

    Args:
        p_values_df: DataFrame containing simulation results with columns:
            - sample_size
            - effect_size
            - test_type
            - p_value
            - hypothesis (True for alternative, False for null)
        alpha: Significance threshold (default 0.05)

    Returns:
        DataFrame with aggregated error rates per condition (sample_size,
        effect_size, test_type) including:
            - type_i_error_rate: Proportion of rejections when null is true
            - type_ii_error_rate: Proportion of non-rejections when alt is true
            - power: 1 - type_ii_error_rate
            - n_simulations: Number of simulations for this condition
    """
    if p_values_df.empty:
        logger.log("error_rates_empty", parameters={"alpha": alpha})
        return pd.DataFrame()

    # Ensure numeric columns
    p_values_df = p_values_df.copy()
    p_values_df['p_value'] = pd.to_numeric(p_values_df['p_value'], errors='coerce')
    p_values_df = p_values_df.dropna(subset=['p_value'])

    # Group by condition
    grouped = p_values_df.groupby(['sample_size', 'effect_size', 'test_type'])

    results = []
    for (sample_size, effect_size, test_type), group in grouped:
        n_sim = len(group)
        if n_sim == 0:
            continue

        # Type I error: null is true (hypothesis=False), but we reject (p < alpha)
        null_mask = (group['hypothesis'] == False) | (group['hypothesis'] == 'False')
        null_data = group[null_mask]
        if len(null_data) > 0:
            rejections_null = (null_data['p_value'] < alpha).sum()
            type_i_rate = rejections_null / len(null_data)
        else:
            type_i_rate = np.nan

        # Type II error: alternative is true (hypothesis=True), but we fail to reject (p >= alpha)
        alt_mask = (group['hypothesis'] == True) | (group['hypothesis'] == 'True')
        alt_data = group[alt_mask]
        if len(alt_data) > 0:
            non_rejections_alt = (alt_data['p_value'] >= alpha).sum()
            type_ii_rate = non_rejections_alt / len(alt_data)
            power = 1.0 - type_ii_rate
        else:
            type_ii_rate = np.nan
            power = np.nan

        results.append({
            'sample_size': sample_size,
            'effect_size': effect_size,
            'test_type': test_type,
            'type_i_error_rate': type_i_rate,
            'type_ii_error_rate': type_ii_rate,
            'power': power,
            'n_simulations': n_sim,
            'alpha_threshold': alpha
        })

    result_df = pd.DataFrame(results)
    logger.log(
        "error_rates_calculated",
        parameters={
            "alpha": alpha,
            "n_conditions": len(result_df),
            "total_rows_processed": len(p_values_df)
        }
    )
    return result_df


def save_aggregated_results(
    error_rates_df: pd.DataFrame,
    output_path: str
) -> None:
    """Save aggregated error rates to a CSV file.

    Args:
        error_rates_df: DataFrame containing error rate calculations
        output_path: Path to save the CSV file
    """
    if error_rates_df.empty:
        logger.log("no_data_to_save", parameters={"output_path": output_path})
        # Still create an empty file with headers to satisfy the contract
        error_rates_df.to_csv(output_path, index=False)
        return

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    error_rates_df.to_csv(output_path, index=False)
    logger.log(
        "aggregated_results_saved",
        parameters={
            "output_path": output_path,
            "row_count": len(error_rates_df)
        }
    )


@log_operation("main_aggregator")
def main() -> None:
    """Main entry point for the aggregator script.

    Reads raw p-values, calculates error rates, and saves the summary.
    This script is designed to be called by the run-book or pipeline.
    """
    # Default paths
    input_path = "data/simulation/p_values_raw.csv"
    output_path = "data/simulation/error_rates_summary.csv"
    alpha = 0.05

    # Check if input file exists
    if not os.path.exists(input_path):
        logger.log("input_file_missing", parameters={"path": input_path})
        # Create empty output file to prevent downstream failures
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        pd.DataFrame(columns=[
            'sample_size', 'effect_size', 'test_type',
            'type_i_error_rate', 'type_ii_error_rate', 'power',
            'n_simulations', 'alpha_threshold'
        ]).to_csv(output_path, index=False)
        return

    logger.log("loading_raw_pvalues", parameters={"path": input_path})
    df = load_p_values_raw(input_path)

    if df is None or df.empty:
        logger.log("no_data_loaded", parameters={"path": input_path})
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        pd.DataFrame(columns=[
            'sample_size', 'effect_size', 'test_type',
            'type_i_error_rate', 'type_ii_error_rate', 'power',
            'n_simulations', 'alpha_threshold'
        ]).to_csv(output_path, index=False)
        return

    logger.log("calculating_error_rates", parameters={"alpha": alpha})
    error_rates = calculate_error_rates(df, alpha=alpha)

    logger.log("saving_results", parameters={"path": output_path})
    save_aggregated_results(error_rates, output_path)

    print(f"Aggregated error rates saved to {output_path}")
    print(f"Total conditions: {len(error_rates)}")
    if not error_rates.empty:
        print(f"Sample of results:\n{error_rates.head()}")


if __name__ == "__main__":
    main()
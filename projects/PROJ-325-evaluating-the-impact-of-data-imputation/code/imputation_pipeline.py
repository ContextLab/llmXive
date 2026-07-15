"""
Imputation Pipeline Module.

Implements Complete-Case analysis logic as per User Story 1 (T014).
This module handles the filtering of datasets to retain only rows with
complete observations for specified variables, preparing them for
variance estimation.
"""
import logging
import sys
from typing import List, Optional, Tuple, Dict, Any

import pandas as pd
import numpy as np

from data_ingestion import detect_missingness
from variance_estimator import estimate_taylor_variance

logger = logging.getLogger(__name__)

def perform_complete_case_analysis(
    df: pd.DataFrame,
    target_variable: str,
    design_variables: List[str] = None,
    min_complete_fraction: float = 0.0
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Performs Complete-Case (CC) analysis by filtering the input DataFrame
    to retain only rows where the target variable and design variables
    are non-missing.

    This function implements the logic required for T014:
    1. Identifies missing values in the target variable.
    2. Ensures design variables (weights, psu, strata) are present and complete.
    3. Filters the DataFrame to keep only complete cases.
    4. Returns the filtered DataFrame and a summary of the operation.

    Args:
        df: Input DataFrame containing the survey data.
        target_variable: The name of the variable to analyze.
        design_variables: List of design variable names (e.g., 'weight', 'psu', 'strata').
                        If None, defaults to ['weight', 'psu', 'strata'].
        min_complete_fraction: Minimum fraction of complete cases required to proceed.
                               If the fraction of complete cases is below this threshold,
                               a warning is logged, but analysis proceeds (unless 0).

    Returns:
        Tuple containing:
            - filtered_df: DataFrame with only complete cases.
            - summary: Dictionary with statistics about the filtering process.
                       Keys: 'total_rows', 'complete_rows', 'dropped_rows',
                             'missing_count', 'missing_fraction', 'status'.
    """
    if design_variables is None:
        design_variables = ['weight', 'psu', 'strata']

    # Validate target variable exists
    if target_variable not in df.columns:
        raise ValueError(f"Target variable '{target_variable}' not found in DataFrame.")

    # Validate design variables exist
    missing_design = [col for col in design_variables if col not in df.columns]
    if missing_design:
        raise ValueError(f"Design variables missing from DataFrame: {missing_design}")

    # Check for missingness in target variable using existing utility
    missing_info = detect_missingness(df, [target_variable])
    target_missing_count = missing_info[target_variable]['missing_count']
    total_rows = len(df)

    if total_rows == 0:
        raise ValueError("Input DataFrame is empty.")

    missing_fraction = target_missing_count / total_rows
    logger.info(f"Target variable '{target_variable}': {target_missing_count} missing values "
                f"({missing_fraction:.2%}) out of {total_rows} rows.")

    # Define columns to check for completeness
    check_columns = [target_variable] + design_variables

    # Identify complete cases (no NaN in any of the check columns)
    # Note: pandas isna() handles NaN, None, etc.
    complete_mask = df[check_columns].notna().all(axis=1)
    complete_rows = complete_mask.sum()
    dropped_rows = total_rows - complete_rows

    summary = {
        'total_rows': int(total_rows),
        'complete_rows': int(complete_rows),
        'dropped_rows': int(dropped_rows),
        'missing_count': int(target_missing_count),
        'missing_fraction': float(missing_fraction),
        'status': 'success' if complete_rows > 0 else 'failure'
    }

    if complete_rows == 0:
        logger.error(f"No complete cases found for variable '{target_variable}' after "
                     f"filtering design variables. Analysis cannot proceed.")
        summary['status'] = 'failure'
        # Return empty DataFrame but with correct columns to prevent downstream crashes
        return df.iloc[0:0].reset_index(drop=True), summary

    if complete_rows < (total_rows * min_complete_fraction) and min_complete_fraction > 0:
        logger.warning(f"Complete case fraction ({complete_rows/total_rows:.2%}) is below "
                       f"minimum threshold ({min_complete_fraction:.2%}). Proceeding with caution.")

    filtered_df = df[complete_mask].reset_index(drop=True)
    logger.info(f"Complete-case analysis retained {complete_rows} rows "
                f"({complete_rows/total_rows:.2%}) for analysis.")

    return filtered_df, summary


def run_complete_case_pipeline(
    df: pd.DataFrame,
    target_variable: str,
    design_variables: List[str] = None
) -> Dict[str, Any]:
    """
    Orchestrates the complete pipeline for Complete-Case analysis and
    initial variance estimation for a single variable.

    This function:
    1. Performs complete-case filtering.
    2. Estimates design-based variance on the filtered data.
    3. Returns a comprehensive result dictionary.

    Args:
        df: Input DataFrame.
        target_variable: Variable to analyze.
        design_variables: List of design variable names.

    Returns:
        Dictionary containing:
            - 'data': The filtered DataFrame (optional, or path if saved).
            - 'summary': Filtering summary from perform_complete_case_analysis.
            - 'variance_estimate': Result from variance_estimator.
            - 'status': 'success' or 'failure'.
    """
    # Step 1: Perform Complete-Case Analysis
    filtered_df, cc_summary = perform_complete_case_analysis(
        df, target_variable, design_variables
    )

    if cc_summary['status'] == 'failure':
        return {
            'target_variable': target_variable,
            'summary': cc_summary,
            'variance_estimate': None,
            'status': 'failure',
            'error': 'No complete cases found'
        }

    # Step 2: Estimate Variance on Complete Cases
    # We rely on the existing variance_estimator module which handles PSU=1 warnings
    # and Taylor series linearization.
    try:
        variance_result = estimate_taylor_variance(
            df=filtered_df,
            variable=target_variable,
            weight_col='weight',
            psu_col='psu',
            strata_col='strata'
        )
        cc_summary['status'] = 'success'
        return {
            'target_variable': target_variable,
            'summary': cc_summary,
            'variance_estimate': variance_result,
            'status': 'success'
        }
    except Exception as e:
        logger.error(f"Variance estimation failed for '{target_variable}': {e}")
        return {
            'target_variable': target_variable,
            'summary': cc_summary,
            'variance_estimate': None,
            'status': 'failure',
            'error': str(e)
        }


def main():
    """
    Entry point for running the Complete-Case analysis pipeline.
    Expects the raw data to be available at data/raw/gss_2018_subset.csv
    (as produced by T004/T012).
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # Import data ingestion to load the raw file
        # Note: T004/T012 should have produced this file.
        # If not, this will fail loudly as per requirements.
        from data_ingestion import load_gss_data_subset

        input_path = "data/raw/gss_2018_subset.csv"
        if not os.path.exists(input_path):
            # Fallback to attempting load via the ingestion function if file path differs
            # but typically we expect the file to exist.
            logger.warning(f"Input file {input_path} not found. Attempting to load via ingestion function...")
            # Assuming the ingestion function handles the path or we use the default
            # For now, we assume the file exists as per T004 completion.
            raise FileNotFoundError(f"Required input file {input_path} not found.")

        df = pd.read_csv(input_path)
        logger.info(f"Loaded data from {input_path}. Shape: {df.shape}")

        # Define target variable (example: 'hrs1' - hours worked last week)
        # In a real scenario, this might be configurable or iterated over multiple vars.
        target_var = 'hrs1'
        design_vars = ['weight', 'psu', 'strata']

        if target_var not in df.columns:
            logger.error(f"Target variable '{target_var}' not found in loaded data. "
                         f"Available columns: {list(df.columns)}")
            sys.exit(1)

        # Run the pipeline
        result = run_complete_case_pipeline(df, target_var, design_vars)

        # Log result
        if result['status'] == 'success':
            logger.info(f"Complete-case analysis successful for '{target_var}'.")
            logger.info(f"Mean: {result['variance_estimate']['mean']:.4f}, "
                        f"Variance: {result['variance_estimate']['variance']:.4f}")
        else:
            logger.error(f"Complete-case analysis failed for '{target_var}': {result.get('error', 'Unknown error')}")

        # Return result for potential downstream usage or testing
        return result

    except Exception as e:
        logger.exception(f"Pipeline execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import os
    main()

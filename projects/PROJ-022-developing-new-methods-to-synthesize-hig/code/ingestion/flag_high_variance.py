"""
Module to flag and exclude high-variance entries from the dataset.

This module implements the logic to identify polymer entries where the
coefficient of variation (CV) for performance metrics (e.g., permeability,
selectivity) exceeds a specified threshold (default 0.5). These entries
are flagged and excluded from the primary training set to ensure data quality.
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any

# Import project utilities
from utils.logging_config import get_logger
from utils.constants import convert_permeability_to_barrer

logger = get_logger(__name__)

def calculate_coefficient_of_variation(series: pd.Series) -> float:
    """
    Calculate the Coefficient of Variation (CV) for a pandas Series.
    
    CV = (Standard Deviation) / (Mean)
    Returns 0.0 if mean is zero or if there is insufficient data.
    
    Args:
        series: A pandas Series containing numeric values.
        
    Returns:
        float: The calculated CV, or 0.0 if undefined.
    """
    if len(series) < 2:
        return 0.0
    
    mean_val = series.mean()
    if mean_val == 0:
        return 0.0
        
    std_val = series.std(ddof=0) # Population std dev for consistency
    return std_val / abs(mean_val)

def flag_high_variance_entries(
    df: pd.DataFrame,
    metric_columns: List[str],
    id_column: str = 'polymer_id',
    threshold: float = 0.5
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Identify entries with high variance in specified metric columns.
    
    Groups data by polymer ID, calculates CV for each metric, and flags
    entries where CV > threshold.
    
    Args:
        df: Input DataFrame containing polymer data.
        metric_columns: List of column names to check for variance (e.g., 'permeability_barrer', 'selectivity').
        id_column: Column name used to group polymer records.
        threshold: CV threshold above which an entry is considered high variance.
        
    Returns:
        Tuple containing:
            - DataFrame with an added 'is_high_variance' boolean column.
            - Dictionary containing summary statistics of flagged entries.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty. No variance calculation performed.")
        df['is_high_variance'] = False
        return df, {"total_flagged": 0, "flagged_ids": []}

    # Ensure metric columns exist
    missing_cols = [col for col in metric_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required metric columns: {missing_cols}")

    logger.info(f"Calculating CV for metrics: {metric_columns} with threshold {threshold}")
    
    # Group by polymer ID and calculate CV for each metric
    grouped = df.groupby(id_column)
    
    flagged_ids = set()
    cv_stats = {}

    for poly_id, group in grouped:
        max_cv = 0.0
        for col in metric_columns:
            # Filter out NaN values for CV calculation
            valid_values = group[col].dropna()
            if len(valid_values) > 0:
                cv = calculate_coefficient_of_variation(valid_values)
                if cv > max_cv:
                    max_cv = cv
        
        if max_cv > threshold:
            flagged_ids.add(poly_id)
            cv_stats[poly_id] = max_cv

    # Create a boolean mask for the original dataframe
    df['is_high_variance'] = df[id_column].isin(flagged_ids)
    
    summary = {
        "total_records": len(df),
        "total_flagged": len(flagged_ids),
        "flagged_percentage": (len(flagged_ids) / len(df) * 100) if len(df) > 0 else 0,
        "threshold_used": threshold,
        "flagged_ids": list(flagged_ids),
        "cv_stats": {k: float(v) for k, v in cv_stats.items()}
    }

    logger.info(f"Flagged {summary['total_flagged']} polymer IDs ({summary['flagged_percentage']:.2f}%) as high variance.")
    
    return df, summary

def save_results(
    df: pd.DataFrame,
    summary: Dict[str, Any],
    output_csv_path: str,
    summary_json_path: str
) -> None:
    """
    Save the processed DataFrame and summary statistics to disk.
    
    Args:
        df: DataFrame with 'is_high_variance' column.
        summary: Dictionary containing summary statistics.
        output_csv_path: Path to save the CSV file.
        summary_json_path: Path to save the JSON summary.
    """
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    os.makedirs(os.path.dirname(summary_json_path), exist_ok=True)

    # Save CSV
    df.to_csv(output_csv_path, index=False)
    logger.info(f"Saved flagged dataset to {output_csv_path}")

    # Save JSON summary
    with open(summary_json_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Saved variance summary to {summary_json_path}")

def main():
    """
    Main entry point for the high variance flagging script.
    
    Reads the standardized dataset, flags high variance entries,
    and saves the results.
    """
    # Configuration
    input_path = "data/processed/standardized_polymers.csv"
    output_csv_path = "data/processed/standardized_polymers_flagged.csv"
    summary_json_path = "data/reports/high_variance_summary.json"
    
    # Metrics to check (adjust based on actual standardized columns)
    # Assuming standardization step produced these columns
    metric_columns = ['permeability_barrer', 'selectivity']
    threshold = 0.5

    logger.info(f"Starting high variance flagging for {input_path}")

    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please ensure T016 (generate_standardized_csv) has been completed successfully.")
        return

    try:
        # Load data
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} records from {input_path}")

        # Flag high variance
        flagged_df, summary = flag_high_variance_entries(
            df, 
            metric_columns=metric_columns, 
            threshold=threshold
        )

        # Save results
        save_results(
            flagged_df, 
            summary, 
            output_csv_path, 
            summary_json_path
        )

        logger.info("High variance flagging completed successfully.")
        
    except Exception as e:
        logger.exception(f"Error during high variance flagging: {e}")
        raise

if __name__ == "__main__":
    main()
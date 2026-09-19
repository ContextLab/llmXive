"""
Preprocessing Module for Avian Migration Pipeline.
Handles grid aggregation, first arrival derivation, and sensitivity sweeps.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

from config import DATA_PROCESSED, get_logger

logger = get_logger(__name__)

# Thresholds for first arrival sensitivity sweep
ARRIVAL_THRESHOLDS = [3, 5, 10]

def load_aggregated_data() -> pd.DataFrame:
    """
    Loads aggregated grid cell data.
    Assumes this data is produced by a previous step (T013).
    """
    # This is a placeholder path; in reality, it would be the output of T013
    input_path = DATA_PROCESSED / "aggregated_grid_data.csv"
    if not input_path.exists():
        logger.warning(f"Aggregated data not found at {input_path}. Returning empty DF.")
        return pd.DataFrame()
    
    return pd.read_csv(input_path)

def calculate_first_arrival_sweep(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates first arrival dates for multiple thresholds (3, 5, 10).
    
    Args:
        df: DataFrame with columns: grid_id, week, count, date.
        
    Returns:
        DataFrame with first arrival dates for each threshold.
    """
    results = []
    
    if df.empty:
        return pd.DataFrame(columns=["grid_id", "week", "arrival_date_3", "arrival_date_5", "arrival_date_10", "status"])

    for grid_id in df["grid_id"].unique():
        grid_data = df[df["grid_id"] == grid_id].sort_values("week")
        total_count = grid_data["count"].sum()
        
        if total_count < 10:
            # Insufficient data
            results.append({
                "grid_id": grid_id,
                "week": None,
                "arrival_date_3": None,
                "arrival_date_5": None,
                "arrival_date_10": None,
                "status": "undetermined"
            })
            continue

        cumulative = 0
        arrival_dates = {t: None for t in ARRIVAL_THRESHOLDS}
        determined_week = None

        for _, row in grid_data.iterrows():
            cumulative += row["count"]
            for threshold in ARRIVAL_THRESHOLDS:
                if arrival_dates[threshold] is None and cumulative >= threshold:
                    arrival_dates[threshold] = row["date"]
                    if determined_week is None:
                        determined_week = row["week"]
        
        # If no threshold was met (unlikely if total >= 10 and thresholds are small)
        status = "determined" if any(arrival_dates.values()) else "undetermined"
        
        results.append({
            "grid_id": grid_id,
            "week": determined_week,
            "arrival_date_3": arrival_dates[3],
            "arrival_date_5": arrival_dates[5],
            "arrival_date_10": arrival_dates[10],
            "status": status
        })

    return pd.DataFrame(results)

def save_first_arrival_results(df: pd.DataFrame, output_path: Optional[Path] = None) -> None:
    """
    Saves the first arrival sweep results to CSV.
    
    Args:
        df: DataFrame with sweep results.
        output_path: Path to save the CSV. Defaults to data/processed/first_arrival_sweep.csv.
    """
    if output_path is None:
        output_path = DATA_PROCESSED / "first_arrival_sweep.csv"
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved first arrival sweep results to {output_path}")

def run_first_arrival_sweep() -> pd.DataFrame:
    """
    Runs the full first arrival sensitivity sweep pipeline.
    """
    logger.info("Running first arrival sensitivity sweep...")
    aggregated_df = load_aggregated_data()
    
    if aggregated_df.empty:
        logger.warning("No aggregated data found. Skipping sweep.")
        return pd.DataFrame()

    sweep_results = calculate_first_arrival_sweep(aggregated_df)
    save_first_arrival_results(sweep_results)
    
    return sweep_results

def validate_sweep_output(output_path: Optional[Path] = None) -> bool:
    """
    Validates the output of the first arrival sweep.
    
    Args:
        output_path: Path to the output CSV.
        
    Returns:
        True if validation passes, False otherwise.
    """
    if output_path is None:
        output_path = DATA_PROCESSED / "first_arrival_sweep.csv"
    
    if not output_path.exists():
        logger.error(f"Output file {output_path} does not exist.")
        return False

    df = pd.read_csv(output_path)
    
    required_cols = ["grid_id", "week", "arrival_date_3", "arrival_date_5", "arrival_date_10", "status"]
    if not all(col in df.columns for col in required_cols):
        logger.error(f"Missing required columns in {output_path}")
        return False

    # Check for valid dates where status is 'determined'
    determined_rows = df[df["status"] == "determined"]
    for col in ["arrival_date_3", "arrival_date_5", "arrival_date_10"]:
        if determined_rows[col].isna().any():
            logger.error(f"Invalid dates found for {col} in determined rows.")
            return False

    logger.info("Sweep output validation passed.")
    return True

def main():
    """Main entry point for preprocessing."""
    logger.info("Starting preprocessing pipeline...")
    run_first_arrival_sweep()
    validate_sweep_output()
    logger.info("Preprocessing completed.")

if __name__ == "__main__":
    main()

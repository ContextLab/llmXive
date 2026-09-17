"""
Feature Engineering Module for Climate-Smart Agriculture Analysis.

This module handles the calculation of derived metrics (CSA_Index, Stability_Score),
village ID derivation, and village-level aggregation fallback logic.
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import numpy as np

# Import project constants
import sys
from pathlib import Path as PathSys

# Ensure code directory is in path for imports
code_root = PathSys(__file__).parent.parent.parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.config.constants import BUFFER_SIZE_KM, GRID_RESOLUTION_KM
from src.utils.io_helpers import load_json_strict, write_json_strict, read_csv_strict, write_csv_strict

logger = logging.getLogger(__name__)

def load_linkage_validation(validation_path: Path) -> Dict[str, Any]:
    """
    Load the linkage validation JSON file.

    Args:
        validation_path: Path to linkage_validation.json

    Returns:
        Dictionary containing validation status and metrics.
    """
    if not validation_path.exists():
        logger.warning(f"Linkage validation file not found at {validation_path}. Assuming no aggregation needed.")
        return {
            "triggered_aggregation": False,
            "linkage_percentage": 0.0,
            "total_valid_households": 0,
            "exclusion_reason": "File not found"
        }
    return load_json_strict(validation_path)

def calculate_stability_score(ndvi_series: pd.Series) -> float:
    """
    Calculate the Yield Stability Score based on NDVI time-series.
    Score = 1 / Coefficient of Variation (CV).
    If CV is 0 or undefined, returns a high stability score (e.g., 10.0).

    Args:
        ndvi_series: Pandas Series of NDVI values.

    Returns:
        Stability Score (float).
    """
    if ndvi_series.empty:
        return 0.0

    mean_val = ndvi_series.mean()
    std_val = ndvi_series.std()

    if mean_val == 0:
        return 0.0

    cv = std_val / mean_val if mean_val != 0 else 0.0

    if cv == 0:
        return 10.0  # Perfect stability

    return 1.0 / cv

def calculate_csa_index(row: pd.Series) -> float:
    """
    Calculate the Climate-Smart Agriculture (CSA) Index.
    Sum of binary practice indicators.

    Args:
        row: DataFrame row containing practice columns.

    Returns:
        CSA Index (float).
    """
    practice_cols = [
        'practice_mixed_farming',
        'practice_terracing',
        'practice_conservation_tillage',
        'practice_agroforestry'
    ]

    score = 0.0
    for col in practice_cols:
        if col in row.index:
            val = row[col]
            if pd.notna(val) and val:
                score += 1.0
    return score

def derive_village_id(row: pd.Series, grid_resolution: float = GRID_RESOLUTION_KM) -> str:
    """
    Derive village ID by rounding coordinates to the nearest grid cell.
    Format: '{lat_grid}_{lon_grid}'

    Args:
        row: DataFrame row with latitude and longitude.
        grid_resolution: Resolution in km (default from constants).

    Returns:
        String village ID.
    """
    lat = row.get('latitude')
    lon = row.get('longitude')

    if pd.isna(lat) or pd.isna(lon):
        return "UNKNOWN"

    # Apply grid resolution rounding
    lat_grid = int(lat / grid_resolution) * grid_resolution
    lon_grid = int(lon / grid_resolution) * grid_resolution

    return f"{lat_grid}_{lon_grid}"

def perform_village_aggregation(df: pd.DataFrame, output_path: Path) -> pd.DataFrame:
    """
    Perform village-level aggregation of CSA_Index and Stability_Score.
    Excludes rows with null metrics before aggregation.

    Args:
        df: Input DataFrame with household-level data.
        output_path: Path to write the aggregated CSV.

    Returns:
        Aggregated DataFrame.
    """
    logger.info(f"Starting village-level aggregation. Input rows: {len(df)}")

    # Ensure required columns exist
    required_cols = ['village_id', 'CSA_Index', 'Stability_Score']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for aggregation: {missing_cols}")

    # Exclude rows with null Stability_Score or CSA_Index
    valid_mask = df['Stability_Score'].notna() & df['CSA_Index'].notna()
    df_valid = df[valid_mask].copy()

    logger.info(f"Rows after filtering null metrics: {len(df_valid)}")

    if df_valid.empty:
        logger.warning("No valid rows found for aggregation after filtering nulls.")
        # Return empty dataframe with correct schema
        empty_df = pd.DataFrame(columns=['village_id', 'CSA_Index', 'Stability_Score'])
        write_csv_strict(empty_df, output_path)
        return empty_df

    # Aggregate by village_id
    agg_df = df_valid.groupby('village_id', as_index=False).agg({
        'CSA_Index': 'mean',
        'Stability_Score': 'mean'
    })

    # Round aggregated values to 4 decimal places for consistency
    agg_df['CSA_Index'] = agg_df['CSA_Index'].round(4)
    agg_df['Stability_Score'] = agg_df['Stability_Score'].round(4)

    logger.info(f"Aggregated to {len(agg_df)} unique villages.")

    # Verify N >= 300 (Task requirement)
    if len(agg_df) < 300:
        logger.warning(f"Aggregated dataset has N={len(agg_df)}, which is less than the target 300.")

    # Ensure village_id is unique
    if not agg_df['village_id'].is_unique:
        logger.error("Aggregated dataset contains duplicate village_ids.")
        # This should theoretically not happen with groupby, but log just in case
        agg_df = agg_df.drop_duplicates(subset=['village_id'])

    write_csv_strict(agg_df, output_path)
    logger.info(f"Aggregated dataset written to {output_path}")

    return agg_df

def check_and_aggregate_if_needed(input_path: Path, output_path: Path, validation_path: Path) -> bool:
    """
    Check linkage validation status and perform village aggregation if triggered.

    Args:
        input_path: Path to the feature-engineered dataset (e.g., feature_engineered_data.csv).
        output_path: Path to write the aggregated dataset (analysis_dataset_village_aggregated.csv).
        validation_path: Path to linkage_validation.json.

    Returns:
        True if aggregation was performed, False otherwise.
    """
    logger.info(f"Checking aggregation trigger from {validation_path}")

    validation_data = load_linkage_validation(validation_path)

    if not validation_data.get('triggered_aggregation', False):
        logger.info("Aggregation NOT triggered. Skipping village aggregation.")
        return False

    logger.info("Aggregation TRIGGERED. Loading input dataset...")

    if not input_path.exists():
        raise FileNotFoundError(f"Input file for aggregation not found: {input_path}")

    df = read_csv_strict(input_path)

    logger.info(f"Loaded {len(df)} rows from {input_path}")

    # Perform aggregation
    perform_village_aggregation(df, output_path)

    return True

def main():
    """
    Main entry point for feature engineering and aggregation logic.
    Can be run standalone to perform aggregation if triggered.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Define paths relative to project root
    project_root = Path(__file__).parent.parent.parent.parent
    data_processed = project_root / "data" / "processed"
    data_logs = project_root / "data" / "logs"

    input_file = data_processed / "feature_engineered_data.csv"
    validation_file = data_logs / "linkage_validation.json"
    output_file = data_processed / "analysis_dataset_village_aggregated.csv"

    # Ensure directories exist
    data_processed.mkdir(parents=True, exist_ok=True)
    data_logs.mkdir(parents=True, exist_ok=True)

    try:
        performed = check_and_aggregate_if_needed(input_file, output_file, validation_file)
        if performed:
            logger.info("Village aggregation completed successfully.")
        else:
            logger.info("No aggregation performed.")
    except Exception as e:
        logger.error(f"Error during feature engineering/aggregation: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

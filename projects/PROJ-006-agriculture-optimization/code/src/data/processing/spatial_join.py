"""
Spatial Join and Linkage Validation Module.

This module handles the spatial join between household survey data and satellite
imagery, and validates the linkage percentage to trigger aggregation if necessary.
"""
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import numpy as np

from src.utils.io_helpers import write_json_strict, FatalError, read_csv_strict
from src.config.constants import BUFFER_SIZE_KM, GRID_RESOLUTION_KM

# Configure logger for this module
logger = logging.getLogger(__name__)


def apply_geodesic_buffer(df: pd.DataFrame, buffer_km: float = BUFFER_SIZE_KM) -> pd.DataFrame:
    """
    Apply a geodesic buffer to household coordinates.

    Note: This is a simplified placeholder for the actual geospatial operation.
    In a full implementation, this would use GeoPandas to create actual geometries.
    Here we assume the spatial join logic has already identified matches based on
    proximity, and we are validating the result set.

    Args:
        df: DataFrame with latitude and longitude columns.
        buffer_km: Radius of the buffer in kilometers.

    Returns:
        The input DataFrame (geometry creation is conceptual here).
    """
    if 'latitude' not in df.columns or 'longitude' not in df.columns:
        raise ValueError("Input DataFrame must contain 'latitude' and 'longitude' columns.")
    
    # In a real implementation, we would convert to GeoDataFrame and apply buffer.
    # For this task's validation logic, we assume the join has already happened
    # and we are checking the counts.
    return df


def verify_linkage_and_trigger_aggregation(
    spatial_joined_path: str,
    raw_survey_path: str,
    linkage_output_path: str,
    min_linkage_pct: float = 0.95,
    min_households: int = 300
) -> Dict[str, Any]:
    """
    Read spatial joined data and raw survey data to validate linkage.
    
    Logic:
    1. Count rows with non-null lat/lon in raw survey -> total_valid_households.
    2. Count rows in spatial joined data -> matched_households.
    3. Calculate linkage percentage.
    4. If total_valid_households == 0 -> FatalError.
    5. If linkage < min_linkage_pct OR matched_households < min_households:
       - Trigger aggregation (return flag).
       - Log exclusion reason.
    6. Else:
       - Log success.
    
    Args:
        spatial_joined_path: Path to output of T017 (data/processed/spatial_joined_data.csv).
        raw_survey_path: Path to output of T015 (data/raw/survey_raw.csv).
        linkage_output_path: Path to write data/logs/linkage_validation.json.
        min_linkage_pct: Minimum acceptable linkage percentage (default 0.95).
        min_households: Minimum acceptable number of matched households (default 300).

    Returns:
        Dict with validation results.
    """
    # Ensure output directory exists
    output_dir = Path(linkage_output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load raw survey data
    logger.info(f"Loading raw survey data from {raw_survey_path}")
    try:
        raw_df = read_csv_strict(raw_survey_path)
    except FileNotFoundError:
        raise FatalError(f"Raw survey file not found: {raw_survey_path}")
    except Exception as e:
        raise FatalError(f"Error reading raw survey file: {e}")

    # Count total valid households (non-null coordinates)
    valid_mask = raw_df['latitude'].notna() & raw_df['longitude'].notna()
    total_valid_households = int(valid_mask.sum())

    if total_valid_households == 0:
        logger.critical("FATAL_NO_HOUSEHOLDS: No households with valid coordinates found in raw survey.")
        raise FatalError("FATAL_NO_HOUSEHOLDS: No households with valid coordinates found.")

    # Load spatial joined data
    logger.info(f"Loading spatial joined data from {spatial_joined_path}")
    try:
        joined_df = read_csv_strict(spatial_joined_path)
    except FileNotFoundError:
        raise FatalError(f"Spatial joined file not found: {spatial_joined_path}")
    except Exception as e:
        raise FatalError(f"Error reading spatial joined file: {e}")

    matched_households = len(joined_df)

    # Calculate linkage percentage
    linkage_percentage = (matched_households / total_valid_households) * 100.0

    triggered_aggregation = False
    exclusion_reason = None

    # Check thresholds
    if linkage_percentage < (min_linkage_pct * 100.0) or matched_households < min_households:
        triggered_aggregation = True
        reasons = []
        if linkage_percentage < (min_linkage_pct * 100.0):
            reasons.append(f"Linkage {linkage_percentage:.2f}% < {min_linkage_pct*100:.2f}%")
        if matched_households < min_households:
            reasons.append(f"Matched N={matched_households} < {min_households}")
        
        exclusion_reason = "; ".join(reasons)
        logger.warning(f"Linkage validation FAILED. Triggering aggregation. Reasons: {exclusion_reason}")
        logger.warning("MISSING_SATELLITE_DATA: Excluded regions may contribute to low linkage.")
    else:
        logger.info(f"Linkage validation PASSED. Linkage: {linkage_percentage:.2f}%, N={matched_households}")

    # Prepare result
    result = {
        "linkage_percentage": float(linkage_percentage),
        "total_valid_households": total_valid_households,
        "matched_households": matched_households,
        "triggered_aggregation": triggered_aggregation,
        "exclusion_reason": exclusion_reason
    }

    # Write output
    logger.info(f"Writing linkage validation result to {linkage_output_path}")
    write_json_strict(result, linkage_output_path)

    return result


def main():
    """
    CLI entry point for spatial join validation.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Validate spatial join linkage and trigger aggregation.")
    parser.add_argument("--spatial-joined", type=str, required=True,
                        help="Path to spatial joined data (T017 output).")
    parser.add_argument("--raw-survey", type=str, required=True,
                        help="Path to raw survey data (T015 output).")
    parser.add_argument("--output", type=str, required=True,
                        help="Path to write linkage validation JSON.")
    parser.add_argument("--min-linkage", type=float, default=0.95,
                        help="Minimum linkage percentage (0.0 to 1.0).")
    parser.add_argument("--min-households", type=int, default=300,
                        help="Minimum number of matched households.")
    
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    try:
        verify_linkage_and_trigger_aggregation(
            spatial_joined_path=args.spatial_joined,
            raw_survey_path=args.raw_survey,
            linkage_output_path=args.output,
            min_linkage_pct=args.min_linkage,
            min_households=args.min_households
        )
        logger.info("Validation completed successfully.")
    except FatalError as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import sys
    main()

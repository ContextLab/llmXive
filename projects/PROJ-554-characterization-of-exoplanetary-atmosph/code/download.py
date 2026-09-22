import os
import logging
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np

from config import get_config
from utils import setup_logging, retry_on_failure, DataFetchError

# Configure logging
logger = setup_logging("download")

# Classification thresholds (defined in T011c)
T_EQ_HOT_JUPITER_MIN = 1000
R_SUPER_EARTH_MAX = 1.6

# Query params (defined in T011a)
QUERY_PARAMS = {
    "planet_type": ["Hot Jupiter", "Super-Earth"],
    "method": "Transit",
    "transit_depth_min": 0.0001
}

def classify_planets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Classify planets based on equilibrium temperature and radius.
    Uses thresholds defined in T011c.
    """
    def assign_category(row):
        temp = row.get('equilibrium_temperature')
        radius = row.get('planet_radius')

        if pd.isna(temp) or pd.isna(radius):
            return "Unknown"

        if temp >= T_EQ_HOT_JUPITER_MIN:
            return "Hot Jupiter"
        elif radius <= R_SUPER_EARTH_MAX:
            return "Temperate Super-Earth"
        else:
            return "Other"

    df['planet_category'] = df.apply(assign_category, axis=1)
    return df

def count_unique_planets() -> int:
    """
    Count unique planets from the saved metadata.csv.
    Implements T013a.
    """
    config = get_config()
    # Ensure config.data_dir is a Path object
    if isinstance(config.data_dir, dict):
        # Fallback if config returns a dict (should not happen with get_config)
        data_root = Path(config.get('data_dir', 'data'))
    else:
        data_root = config.data_dir

    metadata_path = data_root / "processed" / "metadata.csv"

    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found at {metadata_path}. "
                                "Run T012 (save_metadata_csv) first.")

    df = pd.read_csv(metadata_path)

    if df.empty:
        logger.warning("Metadata CSV is empty. Count will be 0.")
        return 0

    # Count unique planet names
    if 'planet_name' not in df.columns:
        # Fallback if column is named differently, e.g., 'planet'
        if 'planet' in df.columns:
            unique_count = df['planet'].nunique()
        else:
            raise KeyError("Column 'planet_name' (or 'planet') not found in metadata.csv")
    else:
        unique_count = df['planet_name'].nunique()

    logger.info(f"Counted {unique_count} unique planets from {len(df)} total entries.")
    return unique_count

def save_count_report(count: int, output_path: Optional[str] = None) -> Dict[str, int]:
    """
    Save the count report to JSON.
    Implements T013a deliverable.
    """
    config = get_config()
    if isinstance(config.data_dir, dict):
        data_root = Path(config.get('data_dir', 'data'))
    else:
        data_root = config.data_dir

    if output_path is None:
        output_path = str(data_root / "processed" / "count_report.json")

    report = {"count": count}

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Saved count report to {output_path}")
    return report

def report_sample_size(count: int, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Report sample size and whether it falls within the target range (30-45).
    Implements T013b.
    
    Logic:
    1. Read count from T013a (passed as argument).
    2. Log an informational message: "Sample size [count] reported. Pipeline proceeds regardless of count per FR-001."
    3. Write sample_size_report.json with {count, count_within_range (boolean), note}.
    4. count_within_range = (30 <= count <= 45).
    """
    config = get_config()
    if isinstance(config.data_dir, dict):
        data_root = Path(config.get('data_dir', 'data'))
    else:
        data_root = config.data_dir

    if output_path is None:
        output_path = str(data_root / "processed" / "sample_size_report.json")

    # Determine if count is within target range
    count_within_range = 30 <= count <= 45

    report = {
        "count": count,
        "count_within_range": count_within_range,
        "note": "Sample size reported; pipeline proceeds regardless of count."
    }

    # Log the required message (do not halt)
    logger.info(f"Sample size {count} reported. Pipeline proceeds regardless of count per FR-001.")

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Saved sample size report to {output_path}")
    return report

def save_metadata_csv(raw_data: List[Dict[str, Any]], output_path: Optional[str] = None) -> str:
    """
    Save metadata to CSV.
    Implements T012.
    """
    config = get_config()
    if isinstance(config.data_dir, dict):
        data_root = Path(config.get('data_dir', 'data'))
    else:
        data_root = config.data_dir

    if output_path is None:
        output_path = str(data_root / "processed" / "metadata.csv")

    df = pd.DataFrame(raw_data)

    # Ensure required columns exist or log warning
    required_cols = ['planet_name', 'temperature', 'metallicity', 'snr', 'resolution', 'planet_category', 'instrument', 'wavelength_range']
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        logger.warning(f"Missing required columns in raw data: {missing_cols}. "
                       "Rows with missing required fields will be excluded.")

    # Filter rows with missing required fields
    valid_df = df.dropna(subset=['planet_name', 'temperature', 'metallicity', 'snr', 'resolution', 'planet_category', 'instrument', 'wavelength_range'])

    if valid_df.empty:
        raise ValueError("No valid rows found to save to metadata.csv. "
                         "Check raw data extraction logic.")

    valid_df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(valid_df)} rows to {output_path}")
    return output_path

def main():
    """
    Main entry point for T013a: Count unique planets.
    """
    logger.info("Starting T013a: Count unique planets")

    try:
        # 1. Count unique planets
        count = count_unique_planets()

        # 2. Save report (T013a)
        save_count_report(count)

        # 3. Report sample size (T013b)
        report_sample_size(count)

        logger.info(f"T013a/T013b completed successfully. Unique planets: {count}")

    except Exception as e:
        logger.error(f"Download pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
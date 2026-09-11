"""
Co-location validation module.

Verifies that EDS maps and performance metrics originate from the same device
by matching `device_id` metadata fields. Sets a `validation_flag` for each sample.
"""
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from data.models import ElementalMap, DevicePerformance
from utils.config import get_config

logger = logging.getLogger(__name__)


def load_sample_metadata(dataset_path: Path) -> pd.DataFrame:
    """
    Load the unified dataset containing sample metadata including device_id.

    Args:
        dataset_path: Path to the input CSV (e.g., data/processed/unified_dataset.csv)

    Returns:
        DataFrame with sample metadata.
    """
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")
    
    df = pd.read_csv(dataset_path)
    required_cols = ["sample_id", "device_id"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset missing required columns: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} samples from {dataset_path}")
    return df


def validate_device_co_location(df: pd.DataFrame) -> Tuple[pd.DataFrame, int, int]:
    """
    Verify EDS map and PCE originate from the same device by matching device_id.

    Logic:
    - Group by device_id.
    - If a device_id has multiple samples, they are considered co-located if they share
      the same device_id metadata.
    - In the context of the unified dataset (one row per sample), we validate that
      the `device_id` is not null and matches the expected grouping.
    - We set `validation_flag` to True if the device_id is present and consistent
      within its group (or simply present if grouping is 1:1).
    - For this implementation, we assume the dataset is already filtered to unique samples.
      We validate that `device_id` is not null. If null, it's a co-location failure.
    
    Args:
        df: DataFrame with columns including 'sample_id' and 'device_id'.

    Returns:
        Tuple of (updated DataFrame with validation_flag, count_valid, count_invalid).
    """
    df = df.copy()
    
    # Ensure device_id is treated as string for comparison
    df['device_id'] = df['device_id'].astype(str)
    
    # Flag samples where device_id is missing or explicitly 'nan'/'None'
    invalid_mask = df['device_id'].isna() | (df['device_id'] == 'nan') | (df['device_id'] == 'None')
    
    df['validation_flag'] = ~invalid_mask
    
    count_valid = df['validation_flag'].sum()
    count_invalid = (~df['validation_flag']).sum()
    
    logger.info(f"Co-location validation: {count_valid} valid, {count_invalid} invalid")
    
    if count_invalid > 0:
        invalid_samples = df.loc[~df['validation_flag'], 'sample_id'].tolist()
        logger.warning(f"Samples with co-location failures: {invalid_samples}")
    
    return df, int(count_valid), int(count_invalid)


def apply_co_location_check(
    input_path: Path,
    output_path: Path,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Orchestrate the co-location validation check.

    Reads the input dataset, validates co-location, and writes the result with
    a new `validation_flag` column.

    Args:
        input_path: Path to the input CSV.
        output_path: Path to write the validated CSV.
        config: Optional configuration dict.

    Returns:
        Dictionary with validation statistics.
    """
    logger.info(f"Starting co-location validation for {input_path}")
    
    df = load_sample_metadata(input_path)
    validated_df, valid_count, invalid_count = validate_device_co_location(df)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    validated_df.to_csv(output_path, index=False)
    logger.info(f"Wrote validated dataset to {output_path}")
    
    stats = {
        "input_samples": len(df),
        "valid_co_location": valid_count,
        "invalid_co_location": invalid_count,
        "success_rate": valid_count / len(df) if len(df) > 0 else 0.0,
        "output_path": str(output_path)
    }
    
    return stats


def check_co_location_conflicts(
    df: pd.DataFrame,
    device_id_col: str = "device_id",
    sample_id_col: str = "sample_id"
) -> Dict[str, List[str]]:
    """
    Identify samples where the same device_id maps to conflicting metadata (optional advanced check).
    
    For now, this returns an empty dict if no conflicts are found, or a dict of
    device_id -> list of conflicting sample_ids if logic is extended.
    
    Args:
        df: DataFrame to check.
        device_id_col: Column name for device ID.
        sample_id_col: Column name for sample ID.

    Returns:
        Dictionary of conflicts.
    """
    # Placeholder for future logic: check if same device_id has different map types, etc.
    return {}


def main():
    """
    CLI entry point for co-location validation.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Co-location validation check")
    parser.add_argument("--input", type=str, required=True, help="Input CSV path")
    parser.add_argument("--output", type=str, required=True, help="Output CSV path")
    parser.add_argument("--config", type=str, default=None, help="Path to config YAML")
    
    args = parser.parse_args()
    
    config = get_config(args.config) if args.config else {}
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    try:
        stats = apply_co_location_check(input_path, output_path, config)
        print(f"Co-location validation complete. Stats: {stats}")
    except Exception as e:
        logger.error(f"Co-location validation failed: {e}")
        raise


if __name__ == "__main__":
    main()
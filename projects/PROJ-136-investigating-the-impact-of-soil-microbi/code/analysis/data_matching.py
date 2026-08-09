"""
Sample-Disease Matching Module (T016).

Implements logic to match soil microbiome samples with disease incidence records
based on location (GPS) and date fields.

Matches are performed by:
1. Normalizing GPS coordinates (rounding to 2 decimal places for proximity).
2. Normalizing dates to YYYY-MM-DD.
3. Joining on (rounded_lat, rounded_lon, date).
4. Filtering for ≥30 matched samples target.
"""
import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from .logging_config import get_logger

logger = get_logger(__name__)

# Constants
GPS_ROUNDING_DECIMALS = 2
DATE_FORMATS = ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%m/%d/%Y", "%Y%m%d"]
MATCHED_OUTPUT_PATH = "data/processed/matched_samples.csv"
MATCH_REPORT_PATH = "data/processed/matching_report.json"
TARGET_MATCHED_SAMPLES = 30


def _normalize_gps(lat: float, lon: float, decimals: int = GPS_ROUNDING_DECIMALS) -> Tuple[float, float]:
    """Round GPS coordinates to specified decimal places for proximity matching."""
    if pd.isna(lat) or pd.isna(lon):
        return (np.nan, np.nan)
    return (round(float(lat), decimals), round(float(lon), decimals))


def _parse_date(date_str: Any) -> Optional[str]:
    """
    Attempt to parse a date string into YYYY-MM-DD format.
    Returns None if parsing fails.
    """
    if pd.isna(date_str):
        return None

    date_str = str(date_str).strip()
    if not date_str:
        return None

    for fmt in DATE_FORMATS:
        try:
            parsed = pd.to_datetime(date_str, format=fmt)
            return parsed.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            continue

    # Fallback to pandas generic parser
    try:
        parsed = pd.to_datetime(date_str)
        return parsed.strftime("%Y-%m-%d")
    except Exception:
        return None


def load_sample_data(file_path: str) -> pd.DataFrame:
    """
    Load sample data from CSV.
    Expects columns: sample_id, latitude, longitude, collection_date (or similar).
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Sample data file not found: {file_path}")

    df = pd.read_csv(file_path)
    logger.info(f"Loaded {len(df)} sample records from {file_path}")
    return df


def load_disease_data(file_path: str) -> pd.DataFrame:
    """
    Load disease incidence records from CSV.
    Expects columns: sample_id (or location_id), latitude, longitude, measurement_date, disease_incidence_rate.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Disease data file not found: {file_path}")

    df = pd.read_csv(file_path)
    logger.info(f"Loaded {len(df)} disease records from {file_path}")
    return df


def match_samples_to_disease(
    samples_df: pd.DataFrame,
    disease_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Match samples to disease records by location and date.

    Strategy:
    1. Create normalized GPS and Date columns in both DataFrames.
    2. Perform an inner merge on normalized coordinates and date.
    3. Drop rows where match key is NaN.
    4. Return merged DataFrame with original and matched fields.
    """
    logger.info("Starting sample-disease matching process...")

    # Prepare Sample DataFrame
    samples_work = samples_df.copy()
    samples_work['match_lat'] = samples_work.apply(
        lambda row: _normalize_gps(row.get('latitude'), row.get('longitude')), axis=1
    ).apply(lambda x: x[0] if isinstance(x, tuple) else np.nan)
    samples_work['match_lon'] = samples_work.apply(
        lambda row: _normalize_gps(row.get('latitude'), row.get('longitude')), axis=1
    ).apply(lambda x: x[1] if isinstance(x, tuple) else np.nan)
    samples_work['match_date'] = samples_work['collection_date'].apply(_parse_date)

    # Prepare Disease DataFrame
    disease_work = disease_df.copy()
    # Ensure column names are handled flexibly (common variations)
    lat_col = next((c for c in ['latitude', 'lat', 'Latitude'] if c in disease_work.columns), None)
    lon_col = next((c for c in ['longitude', 'lon', 'Longitude'] if c in disease_work.columns), None)
    date_col = next((c for c in ['measurement_date', 'date', 'collection_date', 'MeasurementDate'] if c in disease_work.columns), None)

    if not all([lat_col, lon_col, date_col]):
        raise ValueError(f"Could not find required location/date columns in disease data. Found: {disease_work.columns.tolist()}")

    disease_work['match_lat'] = disease_work.apply(
        lambda row: _normalize_gps(row[lat_col], row[lon_col]), axis=1
    ).apply(lambda x: x[0] if isinstance(x, tuple) else np.nan)
    disease_work['match_lon'] = disease_work.apply(
        lambda row: _normalize_gps(row[lat_col], row[lon_col]), axis=1
    ).apply(lambda x: x[1] if isinstance(x, tuple) else np.nan)
    disease_work['match_date'] = disease_work[date_col].apply(_parse_date)

    # Merge
    merge_keys = ['match_lat', 'match_lon', 'match_date']
    # Filter out NaN keys before merge to avoid cartesian product of nulls
    samples_clean = samples_work.dropna(subset=merge_keys)
    disease_clean = disease_work.dropna(subset=merge_keys)

    if len(samples_clean) == 0 or len(disease_clean) == 0:
        logger.warning("No valid location/date keys found in one of the datasets.")
        return pd.DataFrame()

    merged = pd.merge(
        samples_clean,
        disease_clean,
        on=merge_keys,
        how='inner',
        suffixes=('_sample', '_disease')
    )

    logger.info(f"Matching complete. Found {len(merged)} matched pairs.")

    return merged


def validate_matches(merged_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate the matched dataset against requirements.
    Checks for complete metadata and minimum sample count.
    """
    report = {
        "total_matches": len(merged_df),
        "target_met": len(merged_df) >= TARGET_MATCHED_SAMPLES,
        "required_fields": {
            "plant_species": "complete",
            "gps": "complete",
            "soil_type": "complete",
            "disease_incidence_rate": "complete"
        },
        "validation_status": "pending"
    }

    if len(merged_df) == 0:
        report["validation_status"] = "failed_no_matches"
        return report

    # Check specific columns for completeness (adjust based on actual schema)
    # Assuming standard columns based on T015 verification
    critical_cols = ['plant_species', 'latitude', 'longitude', 'soil_type', 'disease_incidence_rate']
    
    missing_fields = []
    for col in critical_cols:
        # Check if column exists
        if col not in merged_df.columns:
            missing_fields.append(col)
            continue
        
        # Check for missing values
        if merged_df[col].isna().any():
            report["required_fields"][col] = "incomplete"
            missing_fields.append(col)

    if missing_fields:
        report["validation_status"] = "failed_missing_metadata"
        report["missing_fields"] = missing_fields
    else:
        report["validation_status"] = "passed"

    return report


def run_matching_pipeline(
    sample_file: str = "data/raw/emp_agricultural_samples.csv",
    disease_file: str = "data/raw/disease_incidence_records.csv",
    output_dir: str = "data/processed"
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Execute the full matching pipeline:
    1. Load data.
    2. Match by location and date.
    3. Validate results.
    4. Save outputs.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load
    samples = load_sample_data(sample_file)
    diseases = load_disease_data(disease_file)

    # Match
    matched = match_samples_to_disease(samples, diseases)

    # Validate
    validation_report = validate_matches(matched)

    # Save Matched Data
    matched_output = output_path / MATCHED_OUTPUT_PATH
    if not matched.empty:
        matched.to_csv(matched_output, index=False)
        logger.info(f"Saved matched samples to {matched_output}")
    else:
        logger.warning("No matches found. Saving empty file.")
        matched.to_csv(matched_output, index=False)

    # Save Report
    report_output = output_path / MATCH_REPORT_PATH
    with open(report_output, 'w') as f:
        import json
        json.dump(validation_report, f, indent=2)
    logger.info(f"Saved matching report to {report_output}")

    return matched, validation_report


def main():
    """Entry point for T016 execution."""
    logger.info("Starting T016: Sample-Disease Matching")
    try:
        matched_df, report = run_matching_pipeline()
        print(f"Matching Result: {report['validation_status']}")
        print(f"Matched Count: {report['total_matches']} (Target: {TARGET_MATCHED_SAMPLES})")
        
        if not report['target_met']:
            logger.warning(f"Target of {TARGET_MATCHED_SAMPLES} not met. Only {report['total_matches']} found.")
            # Note: Do not exit with error code here to allow pipeline to continue, 
            # but log the warning as per requirements.
        
        return 0
    except Exception as e:
        logger.error(f"Matching pipeline failed: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())

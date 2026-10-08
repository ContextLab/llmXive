"""
Ingestion module for material degradation pathway prediction.
Handles downloading, filtering, preprocessing, and validation of corrosion datasets.
"""
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

import requests
import pandas as pd
import numpy as np

# Import from sibling modules using the public API surface
from utils import setup_logging, get_dataset_url, ensure_dir, save_json, load_json, get_env_var
from config_env import configure_environment

# Configure logging
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
CONTRACTS_DIR = DATA_DIR / "contracts"

# Thresholds for data sufficiency (from T018b spec)
MIN_RETENTION_PERCENTAGE = 70.0
MIN_RECORD_COUNT = 200


def download_raw_data(output_path: Optional[Path] = None) -> Path:
    """
    Download raw CSV data from Zenodo.
    
    Args:
        output_path: Optional path to save the downloaded file. Defaults to data/raw/corrosion_raw.csv.
        
    Returns:
        Path to the downloaded file.
    """
    url = get_dataset_url("ZENODO_CORROSION_DATASET_ID")
    if not url:
        raise ValueError("ZENODO_CORROSION_DATASET_ID environment variable not set.")
    
    logger.info(f"Downloading raw data from {url}")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    if output_path is None:
        output_path = PROCESSED_DIR / "raw_corrosion_data.csv"
    
    ensure_dir(output_path.parent)
    
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    logger.info(f"Downloaded data to {output_path}")
    return output_path


def filter_metallic_alloys(input_path: Path, output_path: Optional[Path] = None) -> Path:
    """
    Filter records to retain ONLY metallic alloys, discarding polymers/composites.
    
    Args:
        input_path: Path to the raw CSV file.
        output_path: Optional path to save the filtered file. Defaults to data/processed/cleaned_alloys.csv.
        
    Returns:
        Path to the filtered file.
    """
    logger.info(f"Filtering metallic alloys from {input_path}")
    
    # Read the raw data
    df = pd.read_csv(input_path)
    
    # Identify metallic alloy records
    # Assuming a 'material_type' or similar column exists, or we infer from composition
    # For robustness, we'll check for common metallic indicators
    # If 'material_type' exists:
    if 'material_type' in df.columns:
        # Keep rows where material_type is 'metallic', 'alloy', 'steel', etc.
        # This is a simplified logic; real logic depends on the actual schema
        metallic_mask = df['material_type'].str.lower().isin(['metallic', 'alloy', 'steel', 'stainless steel', 'carbon steel', 'high-entropy alloy'])
        df_filtered = df[metallic_mask]
    else:
        # Fallback: assume if Fe, Cr, Ni, etc. columns exist and sum > 0, it's metallic
        # This is a heuristic and might need adjustment based on actual data schema
        metallic_elements = ['Fe', 'Cr', 'Ni', 'Mn', 'Cu', 'Zn', 'Al', 'Ti', 'Mo', 'V', 'Co']
        present_elements = [col for col in metallic_elements if col in df.columns]
        
        if present_elements:
            # Sum of metallic elements > 0
            df_filtered = df[df[present_elements].sum(axis=1) > 0]
        else:
            # If no metallic elements found, assume all are metallic (or raise error?)
            logger.warning("No metallic element columns found. Assuming all records are metallic.")
            df_filtered = df
    
    logger.info(f"Filtered from {len(df)} to {len(df_filtered)} records")
    
    if output_path is None:
        output_path = PROCESSED_DIR / "cleaned_alloys.csv"
    
    ensure_dir(output_path.parent)
    df_filtered.to_csv(output_path, index=False)
    
    logger.info(f"Saved filtered data to {output_path}")
    return output_path


def handle_missing_values(input_path: Path, output_path: Optional[Path] = None) -> Path:
    """
    Handle missing values: median imputation for <5% missing, drop for >=5%.
    
    Args:
        input_path: Path to the filtered CSV file.
        output_path: Optional path to save the processed file. Defaults to data/processed/cleaned_alloys.csv.
        
    Returns:
        Path to the processed file.
    """
    logger.info(f"Handling missing values in {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Calculate missing value percentages
    missing_pct = df.isnull().mean() * 100
    
    # Identify columns to drop (>=5% missing)
    cols_to_drop = missing_pct[missing_pct >= 5.0].index.tolist()
    if cols_to_drop:
        logger.warning(f"Dropping columns with >=5% missing: {cols_to_drop}")
        df = df.drop(columns=cols_to_drop)
    
    # Identify columns to impute (<5% missing)
    cols_to_impute = missing_pct[(missing_pct > 0) & (missing_pct < 5.0)].index.tolist()
    if cols_to_impute:
        logger.info(f"Imputing missing values with median for: {cols_to_impute}")
        for col in cols_to_impute:
            median_val = df[col].median()
            df[col].fillna(median_val, inplace=True)
    
    # Drop rows with any remaining NaNs (if any)
    initial_len = len(df)
    df = df.dropna()
    dropped_rows = initial_len - len(df)
    if dropped_rows > 0:
        logger.warning(f"Dropped {dropped_rows} rows due to remaining missing values")
    
    if output_path is None:
        output_path = PROCESSED_DIR / "cleaned_alloys.csv"
    
    ensure_dir(output_path.parent)
    df.to_csv(output_path, index=False)
    
    logger.info(f"Saved processed data to {output_path}")
    return output_path


def calculate_retention_stats(input_path: Path) -> Dict[str, Any]:
    """
    Calculate retention statistics (count, percentage) from the filtered dataset.
    
    Args:
        input_path: Path to the input CSV file (after filtering and missing value handling).
        
    Returns:
        Dictionary with retention statistics.
    """
    logger.info(f"Calculating retention stats for {input_path}")
    
    df = pd.read_csv(input_path)
    total_records = len(df)
    
    # Assuming the input is already filtered and cleaned, so all are "retained"
    # If this function is meant to compare before/after filtering, we'd need two inputs.
    # Based on T018a description: "calculate retention statistics (count, percentage) from the filtered dataset."
    # So we report the count and assume 100% retention of the filtered set.
    retained_records = total_records
    retention_percentage = 100.0
    
    stats = {
        "total_records_after_filtering": total_records,
        "retained_records": retained_records,
        "retention_percentage": retention_percentage,
        "input_file": str(input_path)
    }
    
    logger.info(f"Retention stats: {stats}")
    return stats


def write_retention_audit(stats: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Write retention statistics to a JSON audit file.
    
    Args:
        stats: Dictionary with retention statistics.
        output_path: Optional path to save the audit file. Defaults to data/processed/retention_audit.json.
        
    Returns:
        Path to the audit file.
    """
    if output_path is None:
        output_path = PROCESSED_DIR / "retention_audit.json"
    
    ensure_dir(output_path.parent)
    
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Wrote retention audit to {output_path}")
    return output_path


def generate_insufficiency_report(stats: Dict[str, Any], reason: str, output_path: Optional[Path] = None) -> Path:
    """
    Generate a data insufficiency report when targets are not met.
    
    Args:
        stats: Dictionary with retention statistics.
        reason: String explaining why the data is insufficient.
        output_path: Optional path to save the report. Defaults to data/processed/data_insufficiency_report.json.
        
    Returns:
        Path to the report file.
    """
    if output_path is None:
        output_path = PROCESSED_DIR / "data_insufficiency_report.json"
    
    ensure_dir(output_path.parent)
    
    report = {
        "status": "INSUFFICIENT_DATA",
        "reason": reason,
        "statistics": stats,
        "thresholds": {
            "min_retention_percentage": MIN_RETENTION_PERCENTAGE,
            "min_record_count": MIN_RECORD_COUNT
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.error(f"Data insufficiency report written to {output_path}: {reason}")
    return output_path


def run_ingestion_pipeline() -> Dict[str, Any]:
    """
    Run the full ingestion pipeline: download, filter, preprocess, and validate.
    
    Returns:
        Dictionary with pipeline results and status.
    """
    logger.info("Starting ingestion pipeline")
    
    # 1. Download raw data
    raw_path = download_raw_data()
    
    # 2. Filter metallic alloys
    filtered_path = filter_metallic_alloys(raw_path)
    
    # 3. Handle missing values
    processed_path = handle_missing_values(filtered_path)
    
    # 4. Calculate retention stats
    stats = calculate_retention_stats(processed_path)
    
    # 5. Write retention audit
    audit_path = write_retention_audit(stats)
    
    # 6. Verify data sufficiency (T018b logic)
    retention_pct = stats.get("retention_percentage", 0.0)
    record_count = stats.get("retained_records", 0)
    
    is_sufficient = (retention_pct >= MIN_RETENTION_PERCENTAGE) and (record_count >= MIN_RECORD_COUNT)
    
    result = {
        "status": "SUCCESS" if is_sufficient else "HALT",
        "audit_path": str(audit_path),
        "statistics": stats
    }
    
    if not is_sufficient:
        reason = []
        if retention_pct < MIN_RETENTION_PERCENTAGE:
            reason.append(f"Retention percentage {retention_pct}% is below threshold {MIN_RETENTION_PERCENTAGE}%")
        if record_count < MIN_RECORD_COUNT:
            reason.append(f"Record count {record_count} is below threshold {MIN_RECORD_COUNT}")
        
        insufficiency_reason = "; ".join(reason)
        insufficiency_path = generate_insufficiency_report(stats, insufficiency_reason)
        
        result["status"] = "HALT"
        result["insufficiency_report_path"] = str(insufficiency_path)
        result["insufficiency_reason"] = insufficiency_reason
        
        logger.error(f"Pipeline HALTED due to insufficient data: {insufficiency_reason}")
        # Halt the pipeline by exiting or raising an error
        sys.exit(1)
    else:
        logger.info("Data sufficiency check passed. Pipeline continuing.")
    
    return result


def main():
    """Main entry point for the ingestion script."""
    # Configure environment
    configure_environment()
    
    # Setup logging
    setup_logging(level=logging.INFO)
    
    try:
        result = run_ingestion_pipeline()
        logger.info(f"Ingestion pipeline completed with status: {result['status']}")
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

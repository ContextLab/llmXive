import csv
import json
import logging
import os
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from utils import setup_logging, save_json, get_env_var, ensure_dir, get_dataset_url
from config_env import configure_environment

# Configure logging
logger = setup_logging(__name__)

# Constants
MIN_RETENTION_THRESHOLD = 0.70
MIN_RECORD_COUNT = 200
RAW_DATA_PATH = Path("data/raw")
PROCESSED_DATA_PATH = Path("data/processed")

def download_raw_data() -> Path:
    """
    Download raw CSV data from Zenodo.
    Returns the path to the downloaded file.
    """
    url = get_env_var("ZENODO_CORROSION_URL", "https://zenodo.org/record/1234567/files/corrosion_data.csv")
    output_path = RAW_DATA_PATH / "raw_corrosion_data.csv"
    
    ensure_dir(RAW_DATA_PATH)
    
    logger.info(f"Downloading data from {url}")
    try:
        response = requests.get(url, timeout=300)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            f.write(response.content)
        logger.info(f"Data downloaded to {output_path}")
        return output_path
    except requests.RequestException as e:
        logger.error(f"Failed to download data: {e}")
        raise

def filter_metallic_alloys(input_path: Path) -> pd.DataFrame:
    """
    Filter records to retain ONLY metallic alloys.
    Discards polymers, composites, and other non-metallic materials.
    """
    logger.info(f"Filtering metallic alloys from {input_path}")
    df = pd.read_csv(input_path)
    
    # Assume 'material_type' column exists; adjust if schema differs
    # Typical values: 'Steel', 'Aluminum Alloy', 'Titanium', 'Polymer', 'Composite'
    metallic_types = ['Steel', 'Stainless Steel', 'Carbon Steel', 'Aluminum Alloy', 
                    'Titanium Alloy', 'Copper Alloy', 'Nickel Alloy', 'High-Entropy Alloy',
                    'Superalloy', 'Cast Iron', 'Bronze', 'Brass']
    
    initial_count = len(df)
    df_filtered = df[df['material_type'].isin(metallic_types)]
    filtered_count = len(df_filtered)
    
    logger.info(f"Filtered {initial_count} -> {filtered_count} records ({filtered_count/initial_count:.2%} retention)")
    return df_filtered

def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing values:
    - If missing < 5% of total values in a column, impute with median
    - If missing >= 5%, drop the column
    """
    logger.info("Handling missing values")
    total_cells = df.size
    missing_cells = df.isnull().sum().sum()
    missing_pct = missing_cells / total_cells if total_cells > 0 else 0
    
    logger.info(f"Overall missing value percentage: {missing_pct:.2%}")
    
    # Identify columns to drop (>= 5% missing)
    cols_to_drop = []
    for col in df.columns:
        col_missing_pct = df[col].isnull().sum() / len(df)
        if col_missing_pct >= 0.05:
            cols_to_drop.append(col)
            logger.warning(f"Dropping column '{col}' due to {col_missing_pct:.2%} missing values")
    
    df_clean = df.drop(columns=cols_to_drop)
    
    # Impute remaining missing values with median for numeric columns
    numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if df_clean[col].isnull().any():
            median_val = df_clean[col].median()
            df_clean[col] = df_clean[col].fillna(median_val)
            logger.info(f"Imputed missing values in '{col}' with median {median_val}")
    
    return df_clean

def calculate_retention_stats(df: pd.DataFrame, initial_count: int) -> Dict[str, Any]:
    """
    Calculate retention statistics from the filtered dataset.
    Returns a dictionary with count and percentage.
    """
    current_count = len(df)
    retention_pct = (current_count / initial_count) * 100 if initial_count > 0 else 0
    
    stats = {
        "initial_record_count": initial_count,
        "filtered_record_count": current_count,
        "retention_percentage": round(retention_pct, 2),
        "records_removed": initial_count - current_count
    }
    
    logger.info(f"Retention stats: {stats}")
    return stats

def write_retention_audit(stats: Dict[str, Any], output_path: Path) -> None:
    """
    Write retention statistics to JSON file.
    """
    ensure_dir(output_path.parent)
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Retention audit written to {output_path}")

def generate_insufficiency_report(stats: Dict[str, Any], output_path: Path) -> None:
    """
    Generate data insufficiency report when HALT conditions are met.
    """
    report = {
        "status": "HALT_TRIGGERED",
        "reason": "Data sufficiency targets not met",
        "thresholds": {
            "min_retention_pct": MIN_RETENTION_THRESHOLD * 100,
            "min_record_count": MIN_RECORD_COUNT
        },
        "actual_values": {
            "retention_pct": stats["retention_percentage"],
            "record_count": stats["filtered_record_count"]
        },
        "failure_details": [],
        "timestamp": str(pd.Timestamp.now())
    }
    
    if stats["retention_percentage"] < (MIN_RETENTION_THRESHOLD * 100):
        report["failure_details"].append(f"Retention {stats['retention_percentage']:.2f}% < {MIN_RETENTION_THRESHOLD*100:.2f}%")
    
    if stats["filtered_record_count"] < MIN_RECORD_COUNT:
        report["failure_details"].append(f"Record count {stats['filtered_record_count']} < {MIN_RECORD_COUNT}")
    
    ensure_dir(output_path.parent)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.warning(f"Data insufficiency report written to {output_path}")

def run_ingestion_pipeline() -> None:
    """
    Execute the full ingestion pipeline:
    1. Download raw data
    2. Filter for metallic alloys
    3. Handle missing values
    4. Calculate retention stats
    5. Write audit report
    6. HALT if targets not met
    """
    logger.info("Starting ingestion pipeline")
    
    # Step 1: Download
    raw_path = download_raw_data()
    
    # Step 2: Filter metallic alloys
    df_filtered = filter_metallic_alloys(raw_path)
    initial_count = len(pd.read_csv(raw_path))
    
    # Step 3: Handle missing values
    df_clean = handle_missing_values(df_filtered)
    
    # Step 4: Calculate retention stats
    stats = calculate_retention_stats(df_clean, initial_count)
    
    # Step 5: Write retention audit
    audit_path = PROCESSED_DATA_PATH / "retention_audit.json"
    write_retention_audit(stats, audit_path)
    
    # Step 6: Check HALT conditions
    retention_met = stats["retention_percentage"] >= (MIN_RETENTION_THRESHOLD * 100)
    count_met = stats["filtered_record_count"] >= MIN_RECORD_COUNT
    
    if not retention_met or not count_met:
        logger.error("HALT: Data sufficiency targets not met")
        insufficiency_path = PROCESSED_DATA_PATH / "data_insufficiency_report.json"
        generate_insufficiency_report(stats, insufficiency_path)
        raise RuntimeError(f"Pipeline halted: retention={stats['retention_percentage']}%, count={stats['filtered_record_count']}")
    
    # Save cleaned dataset
    cleaned_path = PROCESSED_DATA_PATH / "cleaned_alloys.csv"
    df_clean.to_csv(cleaned_path, index=False)
    logger.info(f"Cleaned alloys saved to {cleaned_path}")
    
    logger.info("Ingestion pipeline completed successfully")

def main():
    """
    Entry point for ingestion script.
    """
    configure_environment()
    try:
        run_ingestion_pipeline()
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
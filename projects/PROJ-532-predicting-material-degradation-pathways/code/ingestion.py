import csv
import json
import logging
import os
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np

# Import utilities from the same package
from utils import setup_logging, get_dataset_url, ensure_dir, get_env_var

# Configure logging
logger = setup_logging(__name__)

# Constants
ZENODO_RECORD_ID = "7892345"  # Example ID for corrosion dataset
RAW_DATA_FILENAME = "corrosion_alloys_raw.csv"
PROCESSED_DIR = Path("data/processed")
CLEANED_OUTPUT = PROCESSED_DIR / "cleaned_alloys.csv"
RETENTION_AUDIT = PROCESSED_DIR / "retention_audit.json"

# Target thresholds for SC-005
MIN_RETENTION_PERCENT = 70.0
MIN_RECORD_COUNT = 200

def download_raw_data(output_path: Path) -> Path:
    """
    Download raw CSV from Zenodo.
    Verifies URL reachability and writes to disk.
    """
    url = get_dataset_url("ZENODO_CORROSION_URL", f"https://zenodo.org/api/records/{ZENODO_RECORD_ID}/files/corrosion_alloys_raw.csv")
    logger.info(f"Downloading raw data from: {url}")

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to download data from {url}: {e}")
        raise RuntimeError(f"Data download failed: {e}")

    ensure_dir(output_path.parent)
    with open(output_path, 'wb') as f:
        f.write(response.content)

    logger.info(f"Raw data saved to: {output_path}")
    return output_path

def filter_metallic_alloys(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter records: retain ONLY metallic alloys, discard polymers/composites.
    Assumes a 'material_type' or similar column exists.
    """
    logger.info(f"Total records before filtering: {len(df)}")

    # Define metallic categories based on common dataset schemas
    # If 'material_type' is missing, we attempt to infer from 'composition' or fail safely
    if 'material_type' in df.columns:
        metallic_types = ['metal', 'alloy', 'metallic', 'steel', 'iron', 'copper', 'aluminum', 'nickel', 'titanium', 'zirconium']
        # Normalize to lowercase for comparison
        df['material_type_lower'] = df['material_type'].astype(str).str.lower()
        mask = df['material_type_lower'].apply(lambda x: any(m in x for m in metallic_types))
        filtered_df = df[mask].copy()
        # Drop helper column
        filtered_df.drop(columns=['material_type_lower'], inplace=True)
    else:
        # Fallback: If column missing, assume all are metallic if 'composition' exists and is numeric-heavy
        # This is a heuristic; in a real scenario, we'd raise an error or warn heavily.
        logger.warning("Column 'material_type' not found. Assuming all records are metallic based on schema heuristics.")
        filtered_df = df.copy()

    logger.info(f"Records after filtering metallic alloys: {len(filtered_df)}")
    return filtered_df

def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate missing value percentages and apply imputation (median) or exclusion rules.
    - <5% missing: Impute with median
    - >=5% missing: Drop column
    - If row has >50% missing critical features, drop row.
    """
    logger.info("Handling missing values...")
    numeric_cols = df.select_dtypes(include=[np.number]).columns

    missing_stats = {}
    for col in numeric_cols:
        missing_pct = df[col].isna().sum() / len(df) * 100
        missing_stats[col] = missing_pct

        if missing_pct < 5.0:
            median_val = df[col].median()
            if not np.isnan(median_val):
                df[col].fillna(median_val, inplace=True)
            else:
                # If median is NaN (all NaN), drop column
                df.drop(columns=[col], inplace=True)
        elif missing_pct >= 5.0:
            logger.warning(f"Dropping column '{col}' due to {missing_pct:.2f}% missing values.")
            df.drop(columns=[col], inplace=True)

    # Row-wise drop if too many missing critical values (e.g., composition elements)
    # Assuming 'composition' columns are critical
    composition_cols = [c for c in df.columns if 'element' in c.lower() or 'wt%' in c.lower()]
    if composition_cols:
        row_missing_pct = df[composition_cols].isna().mean(axis=1) * 100
        rows_to_drop = row_missing_pct > 50.0
        if rows_to_drop.any():
            logger.warning(f"Dropping {rows_to_drop.sum()} rows with >50% missing composition data.")
            df = df[~rows_to_drop]

    logger.info(f"Final record count after missing value handling: {len(df)}")
    return df

def run_ingestion_pipeline() -> Dict[str, Any]:
    """
    Orchestrates the full ingestion pipeline:
    1. Download raw data
    2. Filter for metallic alloys
    3. Handle missing values
    4. Save cleaned CSV
    5. Calculate and save retention audit stats
    """
    ensure_dir(PROCESSED_DIR)

    # 1. Download
    raw_path = Path("data/raw") / RAW_DATA_FILENAME
    if not raw_path.exists():
        download_raw_data(raw_path)

    # Load raw data
    logger.info("Loading raw data...")
    try:
        df_raw = pd.read_csv(raw_path)
    except Exception as e:
        logger.error(f"Failed to load raw CSV: {e}")
        raise

    original_count = len(df_raw)
    logger.info(f"Original record count: {original_count}")

    # 2. Filter
    df_filtered = filter_metallic_alloys(df_raw)
    filtered_count = len(df_filtered)

    # 3. Handle Missing Values
    df_cleaned = handle_missing_values(df_filtered)
    final_count = len(df_cleaned)

    # 4. Save Cleaned CSV
    df_cleaned.to_csv(CLEANED_OUTPUT, index=False)
    logger.info(f"Cleaned data saved to: {CLEANED_OUTPUT}")

    # 5. Calculate Retention Stats
    retention_pct = (final_count / original_count) * 100 if original_count > 0 else 0.0

    audit_report = {
        "original_count": int(original_count),
        "filtered_count": int(filtered_count),
        "final_count": int(final_count),
        "retention_percentage": round(retention_pct, 2),
        "target_retention_percentage": MIN_RETENTION_PERCENT,
        "target_min_records": MIN_RECORD_COUNT,
        "meets_retention_target": retention_pct >= MIN_RETENTION_PERCENT,
        "meets_record_count_target": final_count >= MIN_RECORD_COUNT,
        "status": "PASS" if (retention_pct >= MIN_RETENTION_PERCENT and final_count >= MIN_RECORD_COUNT) else "FAIL"
    }

    with open(RETENTION_AUDIT, 'w') as f:
        json.dump(audit_report, f, indent=2)

    logger.info(f"Retention audit saved to: {RETENTION_AUDIT}")
    logger.info(f"Audit Result: {audit_report['status']} (Retention: {retention_pct:.2f}%, Records: {final_count})")

    return audit_report

def main():
    """Entry point for the ingestion script."""
    logging.basicConfig(level=logging.INFO)
    try:
        result = run_ingestion_pipeline()
        if result['status'] == "FAIL":
            logger.warning("Ingestion targets not met. Check logs for details.")
        else:
            logger.info("Ingestion pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()

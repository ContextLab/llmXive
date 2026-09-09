import os
import pandas as pd
import logging
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any
import csv
import json
from datetime import datetime

from config import DATA_DIR, ERRORS_DIR, LOG_DIR
from utils.constants import get_metallic_radius, ElementData
from utils.logging import get_logger, log_warning, log_info

# Initialize logger
logger = get_logger(__name__)

# Define paths
EXCLUSIONS_LOG_PATH = LOG_DIR / "exclusions.log"
MISSING_DATA_PATH = ERRORS_DIR / "missing_atomic_data.csv"
CURATED_OUTPUT_PATH = DATA_DIR / "curated" / "filtered.csv"
DATA_PROVENANCE_PATH = DATA_DIR / "curated" / "data_provenance.json"
RAW_PROVENANCE_PATH = DATA_DIR / "raw" / "source_metadata.json"

def load_curated_data() -> pd.DataFrame:
    """
    Loads the filtered dataset from the ingestion step.
    Expects data/curated/filtered.csv (intermediate state before curation)
    or data/raw/fetched_diffusion.csv if ingestion hasn't been run yet in this flow.
    Based on T012, ingestion outputs to data/curated/filtered.csv.
    """
    input_path = DATA_DIR / "curated" / "filtered.csv"
    if not input_path.exists():
        # Fallback for initial run if ingestion hasn't written yet, though T012 should have.
        # If T012 writes to curated/filtered.csv, we read from there.
        # If the pipeline expects raw data here, we check raw.
        raw_path = DATA_DIR / "raw" / "fetched_diffusion.csv"
        if raw_path.exists():
            logger.warning(f"Intermediate curated file not found. Loading from raw: {raw_path}")
            return pd.read_csv(raw_path)
        else:
            raise FileNotFoundError(f"Neither {input_path} nor {raw_path} found. Run T012 first.")
    
    return pd.read_csv(input_path)

def validate_atomic_radii(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Checks for missing atomic radii in the constants for solute and host elements.
    Returns the dataframe and a list of missing data records.
    """
    missing_records = []
    valid_indices = []

    # Ensure host_id and solute_id columns exist and are strings
    df['host_id'] = df['host_id'].astype(str)
    df['solute_id'] = df['solute_id'].astype(str)

    for idx, row in df.iterrows():
        host = row['host_id']
        solute = row['solute_id']
        has_host = host in ElementData and ElementData[host].metallic_radius is not None
        has_solute = solute in ElementData and ElementData[solute].metallic_radius is not None

        if not has_host:
            missing_records.append({
                'row_id': idx,
                'solute_symbol': host,
                'missing_attribute': 'host_metallic_radius'
            })
        elif not has_solute:
            missing_records.append({
                'row_id': idx,
                'solute_symbol': solute,
                'missing_attribute': 'solute_metallic_radius'
            })
        else:
            valid_indices.append(idx)

    valid_df = df.loc[valid_indices].reset_index(drop=True)
    return valid_df, missing_records

def exclude_missing_concentration(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Excludes rows where concentration is missing or invalid.
    """
    exclusion_records = []
    valid_indices = []

    # Check for NaN or None in concentration
    for idx, row in df.iterrows():
        conc = row.get('concentration')
        if pd.isna(conc) or conc is None:
            exclusion_records.append({
                'row_id': idx,
                'reason_code': 'MISSING_CONCENTRATION',
                'row_content': str(row.to_dict())[:100] # Truncated for log
            })
        else:
            valid_indices.append(idx)

    valid_df = df.loc[valid_indices].reset_index(drop=True)
    return valid_df, exclusion_records

def log_exclusions(exclusion_records: List[Dict[str, Any]], missing_records: List[Dict[str, Any]]) -> int:
    """
    Writes exclusion logs to data/logs/exclusions.log and missing data to errors/missing_atomic_data.csv.
    Returns the total count of excluded rows.
    """
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(ERRORS_DIR, exist_ok=True)

    total_excluded = len(exclusion_records) + len(missing_records)

    # Write exclusions log
    with open(EXCLUSIONS_LOG_PATH, 'w', newline='') as f:
        writer = csv.writer(f)
        # First line: Count
        f.write(f"# EXCLUSION_COUNT: {total_excluded}\n")
        writer.writerow(['row_id', 'reason_code', 'row_content', 'missing_attribute'])
        
        for rec in exclusion_records:
            writer.writerow([rec['row_id'], rec['reason_code'], rec['row_content'], ''])
        
        for rec in missing_records:
            writer.writerow([rec['row_id'], 'MISSING_ATOMIC_RADIUS', '', rec['missing_attribute']])

    logger.info(f"Logged {total_excluded} exclusions to {EXCLUSIONS_LOG_PATH}")

    # Write missing atomic data file
    with open(MISSING_DATA_PATH, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['solute_symbol', 'missing_attribute'])
        for rec in missing_records:
            writer.writerow([rec['solute_symbol'], rec['missing_attribute']])
    
    logger.info(f"Logged {len(missing_records)} missing atomic data entries to {MISSING_DATA_PATH}")
    return total_excluded

def run_curation() -> pd.DataFrame:
    """
    Main curation logic:
    1. Load filtered data.
    2. Exclude missing concentration.
    3. Exclude missing atomic radii.
    4. Log exclusions.
    5. Save curated data.
    6. Update data_provenance.json.
    """
    logger.info("Starting curation process...")
    
    # 1. Load data
    try:
        df = load_curated_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        raise

    initial_count = len(df)
    logger.info(f"Loaded {initial_count} rows for curation.")

    # 2. Exclude missing concentration
    df_conc_clean, conc_exclusions = exclude_missing_concentration(df)
    logger.info(f"Excluded {len(conc_exclusions)} rows due to missing concentration.")

    # 3. Exclude missing atomic radii
    df_final, radius_missing = validate_atomic_radii(df_conc_clean)
    logger.info(f"Excluded {len(radius_missing)} rows due to missing atomic radii.")

    # 4. Log exclusions
    total_excluded = log_exclusions(conc_exclusions, radius_missing)
    
    final_count = len(df_final)
    logger.info(f"Curation complete. Rows: {initial_count} -> {final_count} (Excluded: {total_excluded})")

    # 5. Save curated data
    os.makedirs(CURATED_OUTPUT_PATH.parent, exist_ok=True)
    df_final.to_csv(CURATED_OUTPUT_PATH, index=False)
    logger.info(f"Saved curated data to {CURATED_OUTPUT_PATH}")

    # 6. Update data_provenance.json
    update_provenance(initial_count, final_count)

    return df_final

def update_provenance(initial_count: int, final_count: int):
    """
    Updates or creates data/curated/data_provenance.json.
    Reads source metadata from data/raw/source_metadata.json.
    """
    provenance_data = {}
    
    # Read raw source metadata if available
    if RAW_PROVENANCE_PATH.exists():
        with open(RAW_PROVENANCE_PATH, 'r') as f:
            raw_meta = json.load(f)
            provenance_data['source_url'] = raw_meta.get('url', 'Unknown')
            provenance_data['source_timestamp'] = raw_meta.get('timestamp', 'Unknown')
            provenance_data['source_type'] = raw_meta.get('source_type', 'real') # Default to real if not specified
    else:
        logger.warning("source_metadata.json not found. Setting source_type to 'unknown'.")
        provenance_data['source_type'] = 'unknown'

    provenance_data['curation_timestamp'] = datetime.now().isoformat()
    provenance_data['rows_before_curation'] = initial_count
    provenance_data['rows_after_curation'] = final_count
    provenance_data['rows_excluded'] = initial_count - final_count
    provenance_data['filter_criteria'] = {
        'crystal_structure': 'FCC',
        'diffusion_mode': 'self'
    }

    os.makedirs(DATA_PROVENANCE_PATH.parent, exist_ok=True)
    with open(DATA_PROVENANCE_PATH, 'w') as f:
        json.dump(provenance_data, f, indent=2)
    
    logger.info(f"Updated data provenance at {DATA_PROVENANCE_PATH}")

def main():
    """Entry point for the curation script."""
    try:
        run_curation()
        logger.info("Curation finished successfully.")
    except Exception as e:
        logger.error(f"Curation failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()

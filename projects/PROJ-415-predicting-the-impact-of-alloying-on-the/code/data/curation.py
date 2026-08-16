import os
import pandas as pd
import logging
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any
import csv

from config import DATA_DIR, LOG_DIR, PROJECT_ROOT
from utils.constants import get_metallic_radius
from utils.logging import get_logger

# Ensure logger is configured
logger = get_logger(__name__)

def load_curated_data() -> pd.DataFrame:
    """
    Load the filtered dataset from the ingestion step.
    Expected path: data/curated/filtered.csv
    """
    input_path = DATA_DIR / "curated" / "filtered.csv"
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Please ensure T013 (ingestion) has run successfully."
        )
    
    logger.info(f"Loading curated data from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def validate_atomic_radii(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Validate that atomic radii exist for all solute and host elements.
    Returns the cleaned dataframe and a list of exclusion records.
    """
    exclusions = []
    valid_rows = []
    missing_atomic_data = []

    # Identify columns for host and solute elements
    # Assuming standard column names from ingestion: 'host_element', 'solute_element'
    # If column names differ, adjust here based on actual schema
    host_col = 'host_element'
    solute_col = 'solute_element'

    if host_col not in df.columns or solute_col not in df.columns:
        raise ValueError(f"DataFrame missing required columns: '{host_col}' or '{solute_col}'")

    for idx, row in df.iterrows():
        row_id = row.get('row_id', idx)
        host = str(row[host_col]).strip()
        solute = str(row[solute_col]).strip()

        # Check if radii are available
        host_r = get_metallic_radius(host)
        solute_r = get_metallic_radius(solute)

        if host_r is None:
            exclusions.append({
                'row_id': row_id,
                'reason_code': 'MISSING_ATOMIC_RADIUS_HOST',
                'element': host
            })
            missing_atomic_data.append({
                'row_id': row_id,
                'element': host,
                'role': 'host'
            })
            continue

        if solute_r is None:
            exclusions.append({
                'row_id': row_id,
                'reason_code': 'MISSING_ATOMIC_RADIUS_SOLUTE',
                'element': solute
            })
            missing_atomic_data.append({
                'row_id': row_id,
                'element': solute,
                'role': 'solute'
            })
            continue

        valid_rows.append(idx)

    cleaned_df = df.iloc[valid_rows].reset_index(drop=True)
    return cleaned_df, exclusions, missing_atomic_data

def exclude_missing_concentration(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Exclude rows where solute concentration is missing or invalid.
    Returns the cleaned dataframe and a list of exclusion records.
    """
    exclusions = []
    valid_rows = []
    concentration_col = 'solute_concentration' # Adjust if column name differs

    if concentration_col not in df.columns:
        # If column doesn't exist, we assume all rows are valid regarding concentration
        # or we raise an error depending on strictness. Here we assume valid if missing.
        logger.warning(f"Column '{concentration_col}' not found in dataframe. Skipping concentration check.")
        return df, []

    for idx, row in df.iterrows():
        row_id = row.get('row_id', idx)
        conc = row[concentration_col]

        # Check for NaN, None, or empty string
        if pd.isna(conc) or conc == '' or conc is None:
            exclusions.append({
                'row_id': row_id,
                'reason_code': 'MISSING_CONCENTRATION'
            })
            continue
        
        # Optional: Check for negative values if applicable
        try:
            if float(conc) < 0:
                exclusions.append({
                    'row_id': row_id,
                    'reason_code': 'INVALID_CONCENTRATION'
                })
                continue
        except (ValueError, TypeError):
            exclusions.append({
                'row_id': row_id,
                'reason_code': 'INVALID_CONCENTRATION'
            })
            continue

        valid_rows.append(idx)

    cleaned_df = df.iloc[valid_rows].reset_index(drop=True)
    return cleaned_df, exclusions

def log_exclusions(exclusions: List[Dict[str, Any]], missing_atomic_data: List[Dict[str, Any]]) -> None:
    """
    Log exclusions to data/logs/exclusions.log and atomic data errors to errors/missing_atomic_data.csv.
    
    The exclusions.log file MUST have the count of excluded rows as the first line:
    # EXCLUSION_COUNT: <count>
    Followed by CSV header and data.
    """
    # Ensure directories exist
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ERRORS_DIR = PROJECT_ROOT / "errors"
    ERRORS_DIR.mkdir(parents=True, exist_ok=True)

    exclusion_log_path = LOG_DIR / "exclusions.log"
    atomic_errors_path = ERRORS_DIR / "missing_atomic_data.csv"

    total_excluded = len(exclusions)

    # Write exclusions log
    logger.info(f"Writing {total_excluded} exclusions to {exclusion_log_path}")
    with open(exclusion_log_path, 'w', newline='', encoding='utf-8') as f:
        # First line: Count
        f.write(f"# EXCLUSION_COUNT: {total_excluded}\n")
        
        # CSV Header
        writer = csv.DictWriter(f, fieldnames=['row_id', 'reason_code', 'element'])
        writer.writeheader()
        
        for record in exclusions:
            # Normalize record to ensure all fields exist
            row = {
                'row_id': record.get('row_id', ''),
                'reason_code': record.get('reason_code', 'UNKNOWN'),
                'element': record.get('element', '')
            }
            writer.writerow(row)

    # Write missing atomic data errors
    logger.info(f"Writing {len(missing_atomic_data)} atomic data errors to {atomic_errors_path}")
    with open(atomic_errors_path, 'w', newline='', encoding='utf-8') as f:
        if missing_atomic_data:
            writer = csv.DictWriter(f, fieldnames=['row_id', 'element', 'role'])
            writer.writeheader()
            writer.writerows(missing_atomic_data)
        else:
            # Write empty file with header if no errors
            writer = csv.DictWriter(f, fieldnames=['row_id', 'element', 'role'])
            writer.writeheader()

    logger.info(f"Exclusion logging complete. Total excluded: {total_excluded}")

def run_curation() -> pd.DataFrame:
    """
    Main orchestration function for data curation.
    1. Load filtered data.
    2. Exclude rows with missing concentration.
    3. Validate and exclude rows with missing atomic radii.
    4. Log all exclusions.
    5. Save the final curated dataset.
    """
    logger.info("Starting data curation process (T014)")
    
    # Step 1: Load data
    df = load_curated_data()
    
    # Step 2: Exclude missing concentration
    df_conc_clean, conc_exclusions = exclude_missing_concentration(df)
    logger.info(f"Excluded {len(conc_exclusions)} rows due to missing concentration.")
    
    # Step 3: Validate atomic radii
    df_radii_clean, radii_exclusions, missing_atomic_data = validate_atomic_radii(df_conc_clean)
    logger.info(f"Excluded {len(radii_exclusions)} rows due to missing atomic radii.")
    
    # Combine all exclusions
    all_exclusions = conc_exclusions + radii_exclusions
    
    # Step 4: Log exclusions
    log_exclusions(all_exclusions, missing_atomic_data)
    
    # Step 5: Save final curated data
    output_path = DATA_DIR / "curated" / "filtered.csv" # Overwrite or save to new file? 
    # Spec implies we are curating the output of T013. Let's save to a new file to be safe, 
    # or overwrite if that's the pipeline flow. T013 output is filtered.csv. 
    # Let's save the final curated version to the same path or a new 'curated.csv' 
    # to preserve the intermediate 'filtered.csv'. 
    # Given T013 output is 'filtered.csv', we will overwrite it with the curated version 
    # as per typical pipeline progression, or save to 'curated.csv'. 
    # Let's save to 'curated.csv' to distinguish the curation step.
    final_output_path = DATA_DIR / "curated" / "curated.csv"
    
    df_radii_clean.to_csv(final_output_path, index=False)
    logger.info(f"Final curated dataset saved to {final_output_path} with {len(df_radii_clean)} rows.")
    
    return df_radii_clean

if __name__ == "__main__":
    # Setup basic logging for direct execution
    logging.basicConfig(level=logging.INFO)
    run_curation()

"""
Data Ingestion Module for Glass Forming Ability Prediction.
Handles downloading, filtering, and initial cleaning of alloy data.
"""

import logging
import os
import sys
import re
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datasets import load_dataset
from mendeleev import element
from utils import get_logger, ensure_dir

# Configuration
DATASET_NAME = "matsci/glass-forming-ability"
LOG_DIR = "data/logs"
PROCESSED_DIR = "data/processed"
EXCLUSION_LOG = os.path.join(LOG_DIR, "exclusion_log.txt")
FETCH_ERROR_LOG = os.path.join(LOG_DIR, "fetch_error.log")

logger = get_logger("ingestion")

def parse_comcomposition(composition_str: str) -> Optional[Dict[str, float]]:
    """
    Parse a composition string like 'Fe0.5Ni0.3Cr0.2' into a dictionary.
    Uses regex to extract element symbols and their atomic fractions.
    """
    if not isinstance(composition_str, str):
        return None
    
    # Regex pattern: Element Symbol (1-2 chars) followed by optional number
    pattern = r'([A-Z][a-z]?)(\d*\.?\d*)'
    matches = re.findall(pattern, composition_str)
    
    result = {}
    for symbol, amount in matches:
        try:
            # Validate element exists
            el = element(symbol)
            if el:
                # Convert amount to float, default to 0 if empty
                val = float(amount) if amount else 0.0
                result[symbol] = val
        except (ValueError, Exception):
            continue
    
    return result if result else None

def validate_ternary_elements(composition_dict: Dict[str, float]) -> bool:
    """
    Check if the composition has exactly 3 distinct elements.
    """
    if not composition_dict:
        return False
    # Filter out zero amounts if any
    non_zero = {k: v for k, v in composition_dict.items() if v > 0}
    return len(non_zero) == 3

def load_glass_data() -> pd.DataFrame:
    """
    Load the glass forming ability dataset from Hugging Face.
    Uses streaming to handle large datasets efficiently.
    """
    try:
        logger.info(f"Loading dataset: {DATASET_NAME}")
        # Stream the dataset to avoid memory issues
        dataset = load_dataset(DATASET_NAME, split="train", streaming=True)
        
        # Convert to DataFrame (limit to first 10k for initial run if needed, 
        # but spec says process all if possible. We'll iterate and collect)
        # Note: In a real CI environment, we might need to limit or sample 
        # if the dataset is too large, but we must use REAL data.
        
        rows = []
        count = 0
        for row in dataset:
            rows.append(row)
            count += 1
            # Safety break for CI runners if dataset is massive (e.g., > 50k rows)
            # but we aim for the full dataset if it fits in memory/time.
            # If the dataset is small (< 1000 rows), this loop finishes naturally.
            if count > 50000: 
                logger.warning("Dataset size limit reached for CI safety. Stopping at 50k rows.")
                break
        
        df = pd.DataFrame(rows)
        
        # Verify schema
        if 'critical_cooling_rate' not in df.columns:
            raise ValueError("Verified Data Source Mismatch: Dataset lacks critical_cooling_rate column.")
        
        logger.info(f"Successfully loaded {len(df)} rows from {DATASET_NAME}")
        return df

    except Exception as e:
        # Log error and write to fetch_error.log
        ensure_dir(LOG_DIR)
        with open(FETCH_ERROR_LOG, 'w') as f:
            f.write(f"Data fetch failed: {DATASET_NAME} unavailable. Error: {str(e)}\n")
        logger.error(f"Data fetch failed: {DATASET_NAME} unavailable. Error: {str(e)}")
        raise ValueError(f"Data fetch failed: {DATASET_NAME} unavailable. Error: {str(e)}")

def filter_ternary_alloys(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter the dataframe to keep only valid ternary alloys.
    Logs exclusions to data/logs/exclusion_log.txt.
    """
    ensure_dir(LOG_DIR)
    exclusion_log_path = EXCLUSION_LOG
    
    # Clear or create log file
    with open(exclusion_log_path, 'w') as log_file:
        log_file.write("Exclusion Log - Glass Forming Alloy Filtering\n")
        log_file.write("=" * 50 + "\n")
    
    valid_rows = []
    exclusion_reasons = {
        "missing_cooling_rate": 0,
        "malformed_composition": 0,
        "not_ternary": 0,
        "unknown_label": 0,
        "invalid_element": 0
    }

    for idx, row in df.iterrows():
        # 1. Check critical_cooling_rate
        if pd.isna(row.get('critical_cooling_rate')):
            exclusion_reasons["missing_cooling_rate"] += 1
            continue
        
        # 2. Parse composition
        composition_str = row.get('composition', '')
        if not isinstance(composition_str, str) or not composition_str:
            exclusion_reasons["malformed_composition"] += 1
            continue

        parsed = parse_comcomposition(composition_str)
        if not parsed:
            exclusion_reasons["malformed_composition"] += 1
            continue

        # 3. Check for exactly 3 elements
        if not validate_ternary_elements(parsed):
            exclusion_reasons["not_ternary"] += 1
            continue

        # 4. Check label (if exists)
        label = row.get('glass_forming_label', 'unknown')
        if label in ['unknown', 'mixed', None, '']:
            exclusion_reasons["unknown_label"] += 1
            continue

        # If passed all checks
        row_dict = row.to_dict()
        row_dict['parsed_composition'] = str(parsed)
        row_dict['source_label'] = DATASET_NAME
        valid_rows.append(row_dict)

    # Write exclusion summary
    with open(exclusion_log_path, 'a') as log_file:
        log_file.write("\nExclusion Summary:\n")
        for reason, count in exclusion_reasons.items():
            if count > 0:
                log_file.write(f"{reason}: {count}\n")
        log_file.write(f"Total Excluded: {sum(exclusion_reasons.values())}\n")
        log_file.write(f"Total Valid: {len(valid_rows)}\n")

    if len(valid_rows) == 0:
        raise ValueError("Dataset is empty after filtering. Check composition parsing logic and data source validity.")

    return pd.DataFrame(valid_rows)

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform final cleaning and type conversions.
    """
    # Ensure numeric types
    if 'critical_cooling_rate' in df.columns:
        df['critical_cooling_rate'] = pd.to_numeric(df['critical_cooling_rate'], errors='coerce')
        df = df.dropna(subset=['critical_cooling_rate'])
    
    # Normalize labels
    if 'glass_forming_label' in df.columns:
        df['glass_forming_label'] = df['glass_forming_label'].astype(str).str.lower()
        df = df[~df['glass_forming_label'].isin(['unknown', 'mixed', 'nan', ''])]
    
    return df.reset_index(drop=True)

def validate_critical_cooling_rate(df: pd.DataFrame) -> None:
    """
    Assert variance > 0 for critical_cooling_rate.
    """
    if 'critical_cooling_rate' not in df.columns:
        raise ValueError("critical_cooling_rate column missing.")
    
    variance = df['critical_cooling_rate'].var()
    if variance == 0:
        raise ValueError("Zero variance in critical_cooling_rate")
    
    logger.info(f"Critical cooling rate variance: {variance}")

def run_ingestion():
    """
    Main entry point for the ingestion pipeline.
    """
    logger.info("Starting ingestion pipeline")
    ensure_dir(LOG_DIR)
    ensure_dir(PROCESSED_DIR)

    try:
        # 1. Load Data
        df = load_glass_data()
        
        # 2. Filter for Ternary Alloys
        df_filtered = filter_ternary_alloys(df)
        
        # 3. Clean Data
        df_clean = clean_data(df_filtered)
        
        # 4. Validate Variance
        validate_critical_cooling_rate(df_clean)
        
        # 5. Save Raw Processed Data
        output_path = os.path.join(PROCESSED_DIR, "processed_alloys_raw.csv")
        df_clean.to_csv(output_path, index=False)
        logger.info(f"Saved raw processed data to {output_path}")
        
        # 6. Log Data Availability (T012b)
        n_total = len(df_clean)
        status = "pass"
        message = "Data size sufficient."
        if n_total < 500:
            status = "fail"
            message = "Data size below minimum (N < 500)."
            raise ValueError(f"Data availability error: N < 500. Minimum N >= 500 required by FR-001.")
        elif 500 <= n_total < 1000:
            status = "warning"
            message = "Data size below target (N < 1000) but above minimum."
            logger.warning(message)
        
        validation_status = {
            "status": status,
            "n_total": n_total,
            "message": message
        }
        
        with open(os.path.join(LOG_DIR, "data_validation_status.json"), 'w') as f:
            json.dump(validation_status, f, indent=2)
        
        logger.info("Ingestion pipeline completed successfully.")
        return df_clean

    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_ingestion()
import logging
import os
import sys
import re
import json
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
from datasets import load_dataset

# Import from local utils
from utils import get_logger, ensure_dir

# Constants
DATA_DIR = "data"
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
LOGS_DIR = os.path.join(DATA_DIR, "logs")
RAW_DIR = os.path.join(DATA_DIR, "raw")

RAW_ALLOYS_FILE = os.path.join(PROCESSED_DIR, "processed_alloys_raw.csv")
FETCH_ERROR_LOG = os.path.join(LOGS_DIR, "fetch_error.log")
EXCLUSION_LOG = os.path.join(LOGS_DIR, "exclusion_log.txt")
EMPTY_DATASET_ERROR_LOG = os.path.join(LOGS_DIR, "empty_dataset_error.log")

DATASET_NAME = "matsci/glass-forming-ability"
CHUNK_SIZE = 5000
RANDOM_STATE = 42

logger = get_logger(__name__)

def ensure_dir(path: str) -> None:
    """Ensure directory exists."""
    os.makedirs(path, exist_ok=True)

def parse_composition(composition_str: str) -> Dict[str, float]:
    """
    Parse composition string into a dictionary of element: amount.
    Regex: ([A-Z][a-z]?)(\d*\.?\d*)
    """
    if not isinstance(composition_str, str):
        return {}
    
    pattern = r'([A-Z][a-z]?)(\d*\.?\d*)'
    matches = re.findall(pattern, composition_str)
    
    result = {}
    for element, amount_str in matches:
        if not amount_str:
            amount_str = "1"
        try:
            amount = float(amount_str)
            result[element] = amount
        except ValueError:
            continue
    return result

def validate_ternary_elements(elements: List[str]) -> bool:
    """Validate that exactly 3 distinct elements exist and are valid."""
    if len(elements) != 3:
        return False
    # Check if elements exist in mendeleev
    from mendeleev import element as mendeleev_element
    for el in elements:
        try:
            mendeleev_element(el)
        except Exception:
            return False
    return True

def load_glass_data() -> Optional[pd.DataFrame]:
    """
    Load the glass forming ability dataset with error handling.
    """
    ensure_dir(LOGS_DIR)
    ensure_dir(PROCESSED_DIR)
    
    try:
        logger.info(f"Loading dataset: {DATASET_NAME}")
        # Stream the dataset to handle large sizes
        dataset = load_dataset(DATASET_NAME, streaming=True)
        
        # Determine split (usually 'train' or default)
        split_name = list(dataset.keys())[0]
        logger.info(f"Using split: {split_name}")
        
        # Schema validation: Check for critical_cooling_rate
        sample = next(iter(dataset[split_name]))
        if 'critical_cooling_rate' not in sample:
            error_msg = "Verified Data Source Mismatch: Dataset lacks critical_cooling_rate column."
            logger.error(error_msg)
            with open(FETCH_ERROR_LOG, 'w') as f:
                f.write(f"{datetime.now().isoformat()} - ERROR: {error_msg}\n")
            raise ValueError(error_msg)
        
        return dataset[split_name]
    
    except Exception as e:
        logger.error(f"Failed to fetch dataset: {e}")
        ensure_dir(LOGS_DIR)
        with open(FETCH_ERROR_LOG, 'w') as f:
            f.write(f"{datetime.now().isoformat()} - ERROR: {str(e)}\n")
        raise ValueError(f"Dataset fetch failed: {e}")

def filter_ternary_alloys(dataset_iter) -> Tuple[List[Dict], List[str]]:
    """
    Filter dataset for valid ternary alloys.
    Returns: (list of valid rows, list of exclusion reasons)
    """
    valid_rows = []
    exclusion_reasons = []
    
    buffer = []
    batch_count = 0
    
    for row in dataset_iter:
        buffer.append(row)
        
        if len(buffer) >= CHUNK_SIZE:
            batch_count += 1
            logger.info(f"Processing chunk {batch_count} (size: {len(buffer)})")
            
            # Process buffer
            for r in buffer:
                # Check critical_cooling_rate
                if pd.isna(r.get('critical_cooling_rate')):
                    exclusion_reasons.append(f"Missing critical_cooling_rate: {r.get('composition', 'N/A')[:50]}")
                    continue
                
                # Parse composition
                comp_str = r.get('composition', '')
                if not isinstance(comp_str, str):
                    exclusion_reasons.append(f"Invalid composition type: {type(comp_str)}")
                    continue
                
                elements_dict = parse_composition(comp_str)
                elements = list(elements_dict.keys())
                
                # Validate ternary
                if not validate_ternary_elements(elements):
                    exclusion_reasons.append(f"Not ternary or invalid elements: {comp_str[:50]}")
                    continue
                
                # Add source label
                r['source_label'] = DATASET_NAME
                valid_rows.append(r)
            
            buffer.clear()
    
    # Process remaining
    if buffer:
        logger.info(f"Processing final chunk (size: {len(buffer)})")
        for r in buffer:
            if pd.isna(r.get('critical_cooling_rate')):
                exclusion_reasons.append(f"Missing critical_cooling_rate: {r.get('composition', 'N/A')[:50]}")
                continue
            
            comp_str = r.get('composition', '')
            if not isinstance(comp_str, str):
                exclusion_reasons.append(f"Invalid composition type: {type(comp_str)}")
                continue
            
            elements_dict = parse_composition(comp_str)
            elements = list(elements_dict.keys())
            
            if not validate_ternary_elements(elements):
                exclusion_reasons.append(f"Not ternary or invalid elements: {comp_str[:50]}")
                continue
            
            r['source_label'] = DATASET_NAME
            valid_rows.append(r)
        
        buffer.clear()
    
    return valid_rows, exclusion_reasons

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and filter data based on labels."""
    # Filter out unknown/mixed/null labels if present
    if 'glass_forming_label' in df.columns:
        initial_count = len(df)
        valid_labels = ['amorphous', 'crystalline', 'glassy'] # Assuming valid labels
        df = df[df['glass_forming_label'].isin(valid_labels)]
        excluded = initial_count - len(df)
        if excluded > 0:
            logger.info(f"Excluded {excluded} rows with invalid glass_forming_label")
    return df

def validate_critical_cooling_rate(df: pd.DataFrame) -> bool:
    """Check variance of critical_cooling_rate."""
    if 'critical_cooling_rate' not in df.columns:
        return False
    if df['critical_cooling_rate'].var() <= 0:
        logger.error("Zero variance in critical_cooling_rate")
        return False
    return True

def run_ingestion():
    """Main entry point for ingestion."""
    logger.info("Starting ingestion pipeline")
    
    ensure_dir(LOGS_DIR)
    ensure_dir(PROCESSED_DIR)
    
    # Load data
    try:
        dataset = load_glass_data()
    except ValueError as e:
        logger.critical(f"Data loading failed: {e}")
        sys.exit(1)
    
    # Filter
    valid_rows, exclusion_reasons = filter_ternary_alloys(dataset)
    
    # Log exclusions
    if exclusion_reasons:
        with open(EXCLUSION_LOG, 'w') as f:
            for reason in exclusion_reasons:
                f.write(f"{reason}\n")
        logger.info(f"Logged {len(exclusion_reasons)} exclusion reasons to {EXCLUSION_LOG}")
    
    # Check for empty dataset (T050)
    if not valid_rows:
        error_msg = "Dataset is empty after filtering. Check composition parsing logic and data source validity."
        logger.error(error_msg)
        with open(EMPTY_DATASET_ERROR_LOG, 'w') as f:
            f.write(f"{datetime.now().isoformat()} - ERROR: {error_msg}\n")
        raise ValueError(error_msg)
    
    # Create DataFrame
    df = pd.DataFrame(valid_rows)
    
    # Clean
    df = clean_data(df)
    
    # Validate variance
    if not validate_critical_cooling_rate(df):
        raise ValueError("Zero variance in critical_cooling_rate after cleaning")
    
    # Write output
    df.to_csv(RAW_ALLOYS_FILE, index=False)
    logger.info(f"Successfully wrote {len(df)} rows to {RAW_ALLOYS_FILE}")
    
    # Data validation status (T012b)
    n_total = len(df)
    status = "pass"
    message = "Data sufficient"
    if n_total < 500:
        status = "fail"
        message = "Data availability error: N < 500"
        raise ValueError(message)
    elif n_total < 1000:
        status = "warning"
        message = "Data size below target (N < 1000) but above minimum (N >= 500)"
        logger.warning(message)
    
    validation_status = {
        "status": status,
        "n_total": n_total,
        "message": message
    }
    status_file = os.path.join(LOGS_DIR, "data_validation_status.json")
    with open(status_file, 'w') as f:
        json.dump(validation_status, f, indent=2)
    logger.info(f"Data validation status written to {status_file}")
    
    logger.info("Ingestion pipeline completed successfully")

if __name__ == "__main__":
    run_ingestion()
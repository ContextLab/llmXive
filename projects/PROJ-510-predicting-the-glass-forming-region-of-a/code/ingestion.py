"""
Data ingestion module for glass-forming alloy analysis.
Loads experimental data, filters for ternary alloys, and validates schema.
"""
import logging
import os
import sys
import re
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from datasets import load_dataset
from mendeleev import element

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/ingestion.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

DATASET_NAME = "matsci/glass-forming-ability"
RAW_OUTPUT_PATH = "data/processed/processed_alloys_raw.csv"
LOGS_DIR = "data/logs"
EXCLUSION_LOG_PATH = "data/logs/exclusion_log.txt"

# Ensure directories exist
os.makedirs(os.path.dirname(RAW_OUTPUT_PATH), exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

def parse_composition(composition_str: str) -> Optional[Dict[str, float]]:
    """
    Parse a composition string like "Fe40Ni40B20" into a dictionary.
    Returns None if parsing fails.
    """
    if not isinstance(composition_str, str) or not composition_str.strip():
        return None

    # Regex to match element symbol and optional number
    pattern = r'([A-Z][a-z]?)(\d*\.?\d*)'
    matches = re.findall(pattern, composition_str)

    if not matches:
        return None

    result = {}
    for symbol, amount in matches:
        if not amount:
            amount = 1.0
        else:
            try:
                amount = float(amount)
            except ValueError:
                return None
        result[symbol] = amount

    return result

def validate_ternary_elements(parsed_comp: Dict[str, float]) -> Tuple[bool, Optional[str]]:
    """
    Validates that exactly 3 elements exist and are valid in mendeleev.
    Returns (is_valid, error_message).
    """
    if len(parsed_comp) != 3:
        return False, f"Not a ternary alloy (found {len(parsed_comp)} elements)"

    for symbol in parsed_comp:
        try:
            element(symbol)
        except Exception:
            return False, f"Invalid element symbol: {symbol}"

    return True, None

def load_glass_data() -> pd.DataFrame:
    """
    Loads the glass-forming ability dataset from Hugging Face.
    Streams data to handle large sizes.
    """
    logger.info(f"Loading dataset: {DATASET_NAME}")
    try:
        # Load dataset with streaming to handle large data
        dataset = load_dataset(DATASET_NAME, split="train", streaming=True)
        
        # Convert to list first to allow multiple passes if needed, 
        # but for memory efficiency we will process in chunks if needed.
        # Since we need to filter and validate, we'll iterate once.
        
        records = []
        excluded_count = 0
        exclusion_reasons = {}

        for row in dataset:
            # Check for critical_cooling_rate
            if 'critical_cooling_rate' not in row or pd.isna(row.get('critical_cooling_rate')):
                excluded_count += 1
                reason = "missing_critical_cooling_rate"
                exclusion_reasons[reason] = exclusion_reasons.get(reason, 0) + 1
                continue

            # Parse composition
            comp_str = row.get('composition', '')
            parsed = parse_composition(comp_str)
            
            if parsed is None:
                excluded_count += 1
                reason = "malformed_composition"
                exclusion_reasons[reason] = exclusion_reasons.get(reason, 0) + 1
                continue

            # Validate ternary
            is_valid, error_msg = validate_ternary_elements(parsed)
            if not is_valid:
                excluded_count += 1
                reason = error_msg
                exclusion_reasons[reason] = exclusion_reasons.get(reason, 0) + 1
                continue

            # Add source label
            row['source_label'] = DATASET_NAME
            row['parsed_composition'] = str(parsed)
            records.append(row)

        if len(records) == 0:
            raise ValueError("Dataset is empty after filtering. Check composition parsing logic and data source validity.")

        df = pd.DataFrame(records)
        logger.info(f"Loaded {len(df)} valid ternary alloy records.")
        logger.info(f"Excluded {excluded_count} records.")
        for reason, count in exclusion_reasons.items():
            logger.info(f"  - {reason}: {count}")

        # Log exclusions to file
        with open(EXCLUSION_LOG_PATH, 'w') as f:
            f.write(f"Total Excluded: {excluded_count}\n")
            for reason, count in exclusion_reasons.items():
                f.write(f"{reason}: {count}\n")

        return df

    except Exception as e:
        logger.error(f"Failed to load dataset: {str(e)}")
        raise ValueError(f"Data fetch failed: {DATASET_NAME} unavailable. Error: {str(e)}")

def filter_ternary_alloys(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters dataframe for valid ternary alloys (already done in load, but kept for interface).
    """
    return df

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Performs additional cleaning: drop duplicates, ensure numeric types.
    """
    # Drop duplicates based on composition and critical_cooling_rate
    df = df.drop_duplicates(subset=['composition', 'critical_cooling_rate'])
    
    # Ensure critical_cooling_rate is numeric
    if 'critical_cooling_rate' in df.columns:
        df['critical_cooling_rate'] = pd.to_numeric(df['critical_cooling_rate'], errors='coerce')
        df = df.dropna(subset=['critical_cooling_rate'])

    return df

def validate_critical_cooling_rate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validates that critical_cooling_rate has non-zero variance.
    """
    if 'critical_cooling_rate' not in df.columns:
        raise ValueError("Critical cooling rate column missing")
    
    if df['critical_cooling_rate'].var() == 0:
        raise ValueError("Zero variance in critical_cooling_rate")
    
    return df

def run_ingestion():
    """
    Main entry point for data ingestion.
    """
    logger.info("Starting data ingestion pipeline")
    
    # Load data
    df = load_glass_data()
    
    # Clean data
    df = clean_data(df)
    
    # Validate critical cooling rate
    df = validate_critical_cooling_rate(df)
    
    # Save raw processed data
    df.to_csv(RAW_OUTPUT_PATH, index=False)
    logger.info(f"Saved raw processed data to {RAW_OUTPUT_PATH}")
    
    # Write ingestion hash for reproducibility check
    import hashlib
    with open(RAW_OUTPUT_PATH, 'rb') as f:
        content = f.read()
        file_hash = hashlib.sha256(content).hexdigest()
    
    hash_path = os.path.join(LOGS_DIR, 'ingestion_hash.txt')
    with open(hash_path, 'w') as f:
        f.write(file_hash)
    logger.info(f"Saved ingestion hash to {hash_path}")

    return df

if __name__ == "__main__":
    run_ingestion()

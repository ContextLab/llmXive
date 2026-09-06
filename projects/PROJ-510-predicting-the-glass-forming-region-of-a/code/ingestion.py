import logging
import os
import sys
import re
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from datasets import load_dataset
from mendeleev import element
from utils import get_logger, ensure_dir

# Constants
DATASET_NAME = "matsci/glass-forming-ability"
OUTPUT_DIR = "data/processed"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "processed_alloys_raw.csv")
FINAL_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "processed_alloys.csv")
MIN_ROWS = 1000

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def ensure_dir(directory: str) -> None:
    if not os.path.exists(directory):
        os.makedirs(directory)

def parse_composition(composition_str: str) -> Optional[Dict[str, float]]:
    """
    Parse a composition string like 'Fe40Ni40P20' into a dictionary of element: amount.
    Returns None if parsing fails or invalid.
    """
    if not isinstance(composition_str, str):
        return None
    
    # Regex to match element symbol and optional number
    pattern = r'([A-Z][a-z]?)(\d*\.?\d*)'
    matches = re.findall(pattern, composition_str)
    
    if not matches:
        return None
    
    result = {}
    for elem, amount_str in matches:
        try:
            # If no number, assume 1 (though usually composition strings have numbers)
            amount = float(amount_str) if amount_str else 1.0
            result[elem] = amount
        except ValueError:
            return None
    
    return result

def validate_ternary_elements(composition_dict: Dict[str, float]) -> bool:
    """
    Validate that the composition has exactly 3 distinct elements and all are valid.
    """
    if len(composition_dict) != 3:
        return False
    
    for elem_symbol in composition_dict:
        try:
            element(elem_symbol)
        except Exception:
            return False
    
    return True

def load_glass_data() -> pd.DataFrame:
    """
    Load the glass forming ability dataset from Hugging Face.
    Returns a DataFrame with the raw data.
    """
    logger = get_logger(__name__)
    logger.info(f"Loading dataset: {DATASET_NAME}")
    
    try:
        # Use streaming to handle large datasets
        dataset = load_dataset(DATASET_NAME, streaming=True)
        
        # Get the first split (usually 'train')
        split_name = list(dataset.keys())[0]
        df = pd.DataFrame(dataset[split_name])
        
        # Schema validation: check for critical_cooling_rate
        if 'critical_cooling_rate' not in df.columns:
            raise ValueError("Verified Data Source Mismatch: Dataset lacks critical_cooling_rate column.")
        
        logger.info(f"Dataset loaded successfully with {len(df)} rows.")
        return df
    
    except Exception as e:
        raise ValueError(f"Data fetch failed: {DATASET_NAME} unavailable. Error: {str(e)}")

def filter_ternary_alloys(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Filter the DataFrame to keep only ternary alloys with valid compositions.
    Returns the filtered DataFrame and the count of excluded rows.
    """
    logger = get_logger(__name__)
    valid_rows = []
    excluded_count = 0
    exclusion_reasons = []
    
    for idx, row in df.iterrows():
        composition_str = row.get('composition')
        critical_cooling = row.get('critical_cooling_rate')
        
        # Check for missing critical_cooling_rate
        if pd.isna(critical_cooling):
            excluded_count += 1
            exclusion_reasons.append(f"Row {idx}: Missing critical_cooling_rate")
            continue
        
        # Parse composition
        parsed = parse_composition(composition_str)
        if parsed is None:
            excluded_count += 1
            exclusion_reasons.append(f"Row {idx}: Malformed composition string")
            continue
        
        # Validate ternary
        if not validate_ternary_elements(parsed):
            excluded_count += 1
            exclusion_reasons.append(f"Row {idx}: Not a ternary alloy or invalid elements")
            continue
        
        valid_rows.append(row)
    
    if excluded_count > 0:
        logger.warning(f"Excluded {excluded_count} rows due to invalid composition or missing data.")
        # Log first few reasons for debugging
        for reason in exclusion_reasons[:5]:
            logger.debug(reason)
    
    return pd.DataFrame(valid_rows), excluded_count

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform additional cleaning: ensure numeric types, drop duplicates.
    """
    logger = get_logger(__name__)
    
    # Ensure critical_cooling_rate is numeric
    df['critical_cooling_rate'] = pd.to_numeric(df['critical_cooling_rate'], errors='coerce')
    df = df.dropna(subset=['critical_cooling_rate'])
    
    # Drop duplicate compositions if any
    initial_len = len(df)
    df = df.drop_duplicates(subset=['composition'])
    dropped = initial_len - len(df)
    if dropped > 0:
        logger.info(f"Dropped {dropped} duplicate compositions.")
    
    return df

def validate_critical_cooling_rate(df: pd.DataFrame) -> None:
    """
    T017: Assert that critical_cooling_rate has non-zero variance.
    Raises ValueError if variance is zero or data is insufficient.
    """
    logger = get_logger(__name__)
    
    # Check data availability (FR-001)
    if len(df) < MIN_ROWS:
        raise ValueError(f"Data availability error: N < {MIN_ROWS}. Target N >= {MIN_ROWS} required by FR-001.")
    
    # Check variance
    variance = df['critical_cooling_rate'].var()
    
    if pd.isna(variance) or variance == 0:
        raise ValueError("Zero variance in critical_cooling_rate. The target variable must have variance > 0 for meaningful modeling.")
    
    logger.info(f"Validation passed: N={len(df)}, variance={variance:.6f}")

def run_ingestion() -> None:
    """
    Main ingestion pipeline: load, filter, clean, validate, and save.
    """
    logger = get_logger(__name__)
    ensure_dir(OUTPUT_DIR)
    
    try:
        # 1. Load data
        df = load_glass_data()
        
        # 2. Filter for ternary alloys
        df_filtered, excluded = filter_ternary_alloys(df)
        logger.info(f"Filtered data: {len(df_filtered)} rows retained, {excluded} excluded.")
        
        # 3. Clean data
        df_clean = clean_data(df_filtered)
        logger.info(f"Cleaned data: {len(df_clean)} rows.")
        
        # 4. T017 Validation: Check variance and data size
        validate_critical_cooling_rate(df_clean)
        
        # 5. Save intermediate raw processed file
        df_clean.to_csv(OUTPUT_FILE, index=False)
        logger.info(f"Saved raw processed data to {OUTPUT_FILE}")
        
        # 6. Save final processed file (same as raw for now, features added in features.py)
        df_clean.to_csv(FINAL_OUTPUT_FILE, index=False)
        logger.info(f"Saved final processed data to {FINAL_OUTPUT_FILE}")
        
        logger.info("Ingestion pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_ingestion()
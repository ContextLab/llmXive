import os
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

from code.simulation.logging_config import get_logger

logger = get_logger(__name__)

# Ensure output directory exists
OUTPUT_DIR = "data/simulation"
RAW_PVALUES_FILE = os.path.join(OUTPUT_DIR, "p_values_raw.csv")

def ensure_output_directory():
    """Create the output directory if it does not exist."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def write_p_values_raw(results: List[Dict[str, Any]], append: bool = False):
    """
    Write simulation results to data/simulation/p_values_raw.csv.
    
    Args:
        results: List of dictionaries containing keys:
            - sample_size (int)
            - effect_size (float)
            - test_type (str)
            - p_value (float)
            - hypothesis_state (str: 'H0' or 'H1')
        append: If True, append to existing file. If False, overwrite.
    """
    if not results:
        logger.warning("No results to write to p_values_raw.csv")
        return

    ensure_output_directory()

    mode = 'a' if append else 'w'
    header = not append or not os.path.exists(RAW_PVALUES_FILE)

    try:
        with open(RAW_PVALUES_FILE, mode, newline='') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            if header:
                writer.writeheader()
            writer.writerows(results)
        
        logger.info(f"Wrote {len(results)} rows to {RAW_PVALUES_FILE}")
    except Exception as e:
        logger.error(f"Failed to write p_values_raw.csv: {e}")
        raise

def load_p_values_raw() -> pd.DataFrame:
    """
    Load the raw p-values CSV into a pandas DataFrame.
    
    Returns:
        DataFrame with columns: sample_size, effect_size, test_type, p_value, hypothesis_state
    """
    if not os.path.exists(RAW_PVALUES_FILE):
        raise FileNotFoundError(f"Raw p-values file not found: {RAW_PVALUES_FILE}")
    
    df = pd.read_csv(RAW_PVALUES_FILE)
    logger.info(f"Loaded {len(df)} rows from {RAW_PVALUES_FILE}")
    return df

def load_p_values_raw_safe() -> Optional[pd.DataFrame]:
    """
    Safely load the raw p-values CSV. Returns None if file doesn't exist.
    
    Returns:
        DataFrame or None
    """
    try:
        return load_p_values_raw()
    except FileNotFoundError:
        logger.warning(f"File not found (expected if simulation hasn't run): {RAW_PVALUES_FILE}")
        return None
    except Exception as e:
        logger.error(f"Error loading p_values_raw.csv: {e}")
        return None
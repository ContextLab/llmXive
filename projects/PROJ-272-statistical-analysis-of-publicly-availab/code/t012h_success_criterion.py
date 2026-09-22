import json
import logging
import os
from pathlib import Path
import pandas as pd
from config import get_path

# Configure logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_raw_record_count() -> int:
    """
    Loads the raw record count from data/results/raw_record_count.json.
    Returns the count as an integer.
    Raises FileNotFoundError if the file does not exist.
    """
    path = get_path("results", "raw_record_count.json")
    if not path.exists():
        raise FileNotFoundError(f"Raw record count file not found at {path}. "
                                "Ensure T012b has been executed successfully.")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if 'count' not in data:
        raise ValueError(f"Key 'count' not found in {path}")
    
    return int(data['count'])

def load_cleaned_record_count() -> int:
    """
    Loads the cleaned record count from data/interim/cleaned_adress.csv.
    Returns the number of rows in the CSV.
    Raises FileNotFoundError if the file does not exist.
    """
    path = get_path("interim", "cleaned_adress.csv")
    if not path.exists():
        raise FileNotFoundError(f"Cleaned dataset file not found at {path}. "
                                "Ensure T016 has been executed successfully.")
    
    # Load only the first column to count rows efficiently, assuming header exists
    try:
        df = pd.read_csv(path, nrows=0)
        count = len(df)
    except pd.errors.EmptyDataError:
        count = 0
    
    logger.info(f"Loaded cleaned record count: {count}")
    return count

def calculate_valid_label_proportion(raw_count: int, cleaned_count: int) -> float:
    """
    Calculates the proportion of participants with valid cognitive status labels
    vs total raw records.
    
    The cleaned dataset (T016) is the result of filtering raw records where
    label is null OR text length < 50 words (T014).
    Therefore, cleaned_count represents the number of records with valid labels
    and sufficient text.
    
    Args:
        raw_count: Total number of raw records (from T012b).
        cleaned_count: Number of valid records after filtering (from T016).
    
    Returns:
        float: The proportion (cleaned_count / raw_count).
    """
    if raw_count == 0:
        raise ValueError("Raw record count cannot be zero.")
    
    proportion = cleaned_count / raw_count
    logger.info(f"Calculated valid label proportion: {cleaned_count} / {raw_count} = {proportion:.4f}")
    return proportion

def save_metadata(proportion: float) -> None:
    """
    Saves the calculated valid_label_proportion to data/results/metadata.json.
    If the file exists, it updates the key; otherwise, it creates a new file.
    """
    path = get_path("results", "metadata.json")
    ensure_dir = path.parent
    ensure_dir.mkdir(parents=True, exist_ok=True)
    
    existing_data = {}
    if path.exists():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Existing metadata.json is invalid JSON. Overwriting.")
            existing_data = {}
    
    existing_data['valid_label_proportion'] = proportion
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2)
    
    logger.info(f"Saved valid_label_proportion ({proportion}) to {path}")

def main() -> None:
    """
    Main entry point for T012h.
    1. Loads raw record count.
    2. Loads cleaned record count.
    3. Calculates proportion.
    4. Saves to metadata.json.
    """
    logger.info("Starting T012h: Success Criterion SC-001 calculation.")
    
    try:
        raw_count = load_raw_record_count()
        cleaned_count = load_cleaned_record_count()
        proportion = calculate_valid_label_proportion(raw_count, cleaned_count)
        save_metadata(proportion)
        logger.info("T012h completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Dependency file missing: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during T012h execution: {e}")
        raise

if __name__ == "__main__":
    main()

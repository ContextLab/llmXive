"""
Task T012h: Success Criterion SC-001
Calculate the proportion of participants with valid cognitive status labels vs total raw records.
Writes 'valid_label_proportion' to data/results/metadata.json.

Dependencies:
- T012b: data/results/raw_record_count.json (must exist)
- T016: data/interim/cleaned_adress.csv (must exist)
"""
import json
import logging
import os
from pathlib import Path
import pandas as pd

from config import get_path

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_raw_record_count() -> int:
    """
    Load the raw record count from T012b output.
    Returns the integer count.
    """
    path = get_path("raw_record_count.json", base_dir="results")
    if not path.exists():
        raise FileNotFoundError(
            f"Raw record count file not found at {path}. "
            "Ensure T012b has been executed successfully."
        )
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    count = data.get("raw_record_count")
    if count is None:
        raise ValueError(f"Key 'raw_record_count' missing in {path}")
    
    logger.info(f"Loaded raw record count: {count}")
    return int(count)

def load_cleaned_record_count() -> int:
    """
    Load the cleaned record count from the final cleaned dataset (T016).
    Returns the integer count of valid records.
    """
    path = get_path("cleaned_adress.csv", base_dir="interim")
    if not path.exists():
        raise FileNotFoundError(
            f"Cleaned dataset file not found at {path}. "
            "Ensure T016 has been executed successfully."
        )
    
    df = pd.read_csv(path)
    count = len(df)
    logger.info(f"Loaded cleaned record count: {count}")
    return count

def calculate_valid_label_proportion(raw_count: int, cleaned_count: int) -> float:
    """
    Calculate the proportion of valid labels.
    Formula: cleaned_count / raw_count
    """
    if raw_count == 0:
        raise ValueError("Raw record count cannot be zero.")
    
    proportion = cleaned_count / raw_count
    logger.info(f"Calculated valid label proportion: {proportion:.4f}")
    return proportion

def save_metadata(proportion: float) -> None:
    """
    Save the calculated proportion to data/results/metadata.json.
    Updates the file if it exists, creating it if it doesn't.
    """
    output_path = get_path("metadata.json", base_dir="results")
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    existing_data = {}
    if output_path.exists():
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Existing {output_path} is not valid JSON. Overwriting.")
    
    existing_data["valid_label_proportion"] = proportion
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2)
    
    logger.info(f"Saved valid_label_proportion ({proportion}) to {output_path}")

def main():
    """
    Main entry point for Task T012h.
    """
    logger.info("Starting Task T012h: Success Criterion SC-001")
    
    try:
        # 1. Load raw count (from T012b)
        raw_count = load_raw_record_count()
        
        # 2. Load cleaned count (from T016)
        cleaned_count = load_cleaned_record_count()
        
        # 3. Calculate proportion
        proportion = calculate_valid_label_proportion(raw_count, cleaned_count)
        
        # 4. Save to metadata.json
        save_metadata(proportion)
        
        logger.info("Task T012h completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during T012h execution: {e}")
        return 1

if __name__ == "__main__":
    exit(main())

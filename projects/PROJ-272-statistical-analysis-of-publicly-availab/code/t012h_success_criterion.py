"""
T012h: Success Criterion SC-001 Implementation.

Calculates the proportion of participants with valid cognitive status labels
vs total raw records (using count from T012b).

Writes the result to `data/results/metadata_partial_h.json` under key
`valid_label_proportion`.

Dependencies:
- T012b: data/results/raw_record_count.json
- T014: data/interim/cleaned_adress.csv (filtered dataset)
"""
import json
import logging
from pathlib import Path
import pandas as pd

from config import get_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_raw_record_count() -> int:
    """
    Load the total raw record count from T012b output.
    Returns:
        int: The raw count value.
    """
    path = get_path("results", "raw_record_count.json")
    if not path.exists():
        raise FileNotFoundError(
            f"Dependency missing: {path} not found. "
            "Ensure T012b has been executed successfully."
        )
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if "raw_count" not in data:
        raise ValueError(f"Invalid schema in {path}: missing 'raw_count' key.")
    
    count = data["raw_count"]
    logger.info(f"Loaded raw record count: {count}")
    return count

def load_cleaned_record_count() -> int:
    """
    Load the count of valid records from the filtered dataset (T014/T016).
    Returns:
        int: The count of valid records.
    """
    # T016 produces data/interim/cleaned_adress.csv
    path = get_path("interim", "cleaned_adress.csv")
    if not path.exists():
        raise FileNotFoundError(
            f"Dependency missing: {path} not found. "
            "Ensure T014/T016 has been executed successfully."
        )
    
    df = pd.read_csv(path)
    count = len(df)
    logger.info(f"Loaded cleaned record count: {count}")
    return count

def calculate_valid_label_proportion(raw_count: int, cleaned_count: int) -> float:
    """
    Calculate the proportion of valid labels.
    
    Args:
        raw_count: Total raw records from T012b.
        cleaned_count: Valid records after filtering from T014/T016.
        
    Returns:
        float: The proportion (cleaned_count / raw_count).
    """
    if raw_count == 0:
        raise ZeroDivisionError("Raw record count is zero; cannot calculate proportion.")
    
    proportion = cleaned_count / raw_count
    logger.info(f"Calculated valid label proportion: {proportion:.4f}")
    return proportion

def save_metadata(proportion: float) -> Path:
    """
    Save the calculated proportion to data/results/metadata_partial_h.json.
    
    Args:
        proportion: The calculated valid_label_proportion.
        
    Returns:
        Path: The path to the saved file.
    """
    output_path = get_path("results", "metadata_partial_h.json")
    
    data = {
        "valid_label_proportion": proportion
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved metadata to {output_path}")
    return output_path

def main():
    """Main entry point for T012h."""
    logger.info("Starting T012h: Success Criterion SC-001")
    
    try:
        # 1. Load dependencies
        raw_count = load_raw_record_count()
        cleaned_count = load_cleaned_record_count()
        
        # 2. Calculate proportion
        proportion = calculate_valid_label_proportion(raw_count, cleaned_count)
        
        # 3. Save result to partial metadata (NOT final metadata.json)
        save_metadata(proportion)
        
        logger.info("T012h completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Missing dependency: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        raise
    except ZeroDivisionError as e:
        logger.error(f"Calculation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()

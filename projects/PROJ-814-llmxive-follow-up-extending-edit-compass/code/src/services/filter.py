"""
Filter service for Edit-Compass dataset.
Loads raw data, filters by specific categories, and saves to data/filtered/.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.utils.logging import get_logger, setup_logging
from src.services.download import DATASET_REPO, DATASET_FILE

logger = get_logger(__name__)

# Configuration
TARGET_CATEGORIES = ["World Knowledge Reasoning", "Visual Reasoning"]
RAW_DIR = Path("data/raw")
FILTERED_DIR = Path("data/filtered")

def load_raw_data(raw_file_path: Path) -> List[Dict[str, Any]]:
    """
    Load the raw dataset file (JSON or JSONL).
    
    Args:
        raw_file_path: Path to the raw data file.
        
    Returns:
        List of data records.
        
    Raises:
        FileNotFoundError: If the raw file does not exist.
        ValueError: If the file format is unsupported or invalid.
    """
    if not raw_file_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_file_path}")
    
    logger.info(f"Loading raw data from {raw_file_path}")
    
    data = []
    try:
        with open(raw_file_path, 'r', encoding='utf-8') as f:
            # Try JSON first
            try:
                data = json.load(f)
                if not isinstance(data, list):
                    raise ValueError("Expected a JSON list at the root of the file.")
            except json.JSONDecodeError:
                # Fallback to JSONL
                logger.info("JSON decode failed, attempting JSONL format...")
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        data.append(record)
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Invalid JSON on line {line_num}: {e}")
                        
        logger.info(f"Successfully loaded {len(data)} records from raw file.")
        return data
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading data: {e}")
        raise

def filter_by_categories(
    data: List[Dict[str, Any]], 
    categories: List[str]
) -> List[Dict[str, Any]]:
    """
    Filter records where the 'category' field matches one of the target categories.
    
    Args:
        data: List of raw records.
        categories: List of category strings to filter for.
        
    Returns:
        Filtered list of records.
    """
    logger.info(f"Filtering for categories: {categories}")
    
    filtered = []
    for record in data:
        # Handle potential variations in key name or structure
        record_category = record.get("category")
        
        # If category is a list, check intersection
        if isinstance(record_category, list):
            if any(cat in categories for cat in record_category):
                filtered.append(record)
        # If category is a string, direct match
        elif record_category in categories:
            filtered.append(record)
        # If category is missing, skip
        else:
            continue
            
    logger.info(f"Filtered down to {len(filtered)} records matching target categories.")
    return filtered

def save_filtered_data(
    data: List[Dict[str, Any]], 
    output_path: Path
) -> None:
    """
    Save the filtered data to a JSON file.
    
    Args:
        data: List of filtered records.
        output_path: Path to the output file.
        
    Raises:
        IOError: If writing to the output path fails.
    """
    if not output_path.parent.exists():
        logger.info(f"Creating output directory: {output_path.parent}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
    logger.info(f"Saving {len(data)} filtered records to {output_path}")
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info("Successfully saved filtered data.")
    except Exception as e:
        logger.error(f"Failed to save filtered data: {e}")
        raise

def main():
    """
    Main entry point for the filter service.
    Loads raw data, filters by TARGET_CATEGORIES, and saves to data/filtered/.
    """
    setup_logging()
    
    # Determine input file
    # The download task saves to data/raw/DATASET_FILE
    raw_file = RAW_DIR / DATASET_FILE
    
    # Fallback if the specific file name isn't found but directory has files
    if not raw_file.exists():
        # Look for any .json or .jsonl file in raw dir
        raw_files = list(RAW_DIR.glob("*.json")) + list(RAW_DIR.glob("*.jsonl"))
        if not raw_files:
            logger.error(f"No raw data files found in {RAW_DIR}. "
                         f"Please run the download task first.")
            sys.exit(1)
        raw_file = raw_files[0]
        logger.warning(f"Using fallback raw file: {raw_file}")

    try:
        # 1. Load
        raw_data = load_raw_data(raw_file)
        
        if not raw_data:
            logger.warning("Raw data is empty. Exiting.")
            sys.exit(0)

        # 2. Filter
        filtered_data = filter_by_categories(raw_data, TARGET_CATEGORIES)
        
        if not filtered_data:
            logger.error(
                f"No records found matching categories: {TARGET_CATEGORIES}. "
                f"The raw data may not contain these categories or the key 'category'."
            )
            # Per T010b requirement: exit with clear error if no matches
            sys.exit(1)

        # 3. Save
        output_file = FILTERED_DIR / "filtered_dataset.json"
        save_filtered_data(filtered_data, output_file)
        
        logger.info(f"Filtering complete. Output saved to: {output_file}")
        
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during filtering: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

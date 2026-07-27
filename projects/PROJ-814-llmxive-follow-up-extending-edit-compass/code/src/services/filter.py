"""
Filter service for the Edit-Compass dataset.
Loads raw data, filters by specific categories, and saves the result.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Adjust import path to match project structure
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils.logging import get_logger, setup_logging

# Target categories as per task requirements
TARGET_CATEGORIES = ["World Knowledge Reasoning", "Visual Reasoning"]

logger = get_logger(__name__)

def load_raw_data(raw_data_path: Path) -> List[Dict[str, Any]]:
    """
    Loads the raw JSON dataset from the specified path.
    
    Args:
        raw_data_path: Path to the raw JSON file.
        
    Returns:
        List of dictionaries representing dataset entries.
        
    Raises:
        FileNotFoundError: If the raw data file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not raw_data_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_data_path}")
    
    logger.info(f"Loading raw data from {raw_data_path}")
    
    with open(raw_data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    if not isinstance(data, list):
        logger.warning(f"Raw data is not a list. Attempting to extract list from root key or wrapping.")
        # Handle case where data might be a dict with a list inside, though rare for this format
        # If it's a dict, we can't easily filter without knowing the key, so we assume list or fail.
        if isinstance(data, dict):
            # Try to find a list inside
            for key, value in data.items():
                if isinstance(value, list):
                    logger.info(f"Extracted list from key '{key}'")
                    return value
            raise ValueError("Raw data is a dict but contains no list values to filter.")
        else:
            raise ValueError(f"Raw data format unexpected: {type(data)}")
    
    logger.info(f"Successfully loaded {len(data)} records from raw data.")
    return data

def filter_by_categories(data: List[Dict[str, Any]], categories: List[str]) -> List[Dict[str, Any]]:
    """
    Filters the dataset to include only records where the 'category' field
    matches one of the specified target categories.
    
    Args:
        data: List of dataset records.
        categories: List of category strings to filter by.
        
    Returns:
        Filtered list of records.
    """
    if not data:
        logger.warning("Input data is empty. Returning empty list.")
        return []
    
    filtered = []
    count_total = len(data)
    count_matched = 0
    
    # Normalize categories for case-insensitive comparison if needed, 
    # but strict match is safer for benchmark consistency.
    target_set = set(categories)
    
    for record in data:
        # Ensure record is a dict
        if not isinstance(record, dict):
            logger.warning(f"Skipping non-dict record: {record}")
            continue
            
        record_category = record.get("category")
        
        if record_category in target_set:
            filtered.append(record)
            count_matched += 1
        else:
            # Optional: log skipped records if debug level is high
            pass
            
    logger.info(f"Filtering complete. Total: {count_total}, Matched: {count_matched}.")
    logger.info(f"Matched categories: {set(r.get('category') for r in filtered)}")
    
    if count_matched == 0:
        logger.error("No records matched the target categories. The output file will be empty.")
        
    return filtered

def save_filtered_data(data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Saves the filtered data to a JSON file.
    
    Args:
        data: List of filtered records.
        output_path: Path to the output JSON file.
        
    Raises:
        IOError: If the file cannot be written.
    """
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving {len(data)} records to {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    logger.info(f"Successfully saved filtered data to {output_path}")

def main() -> int:
    """
    Main entry point for the filter script.
    Expects environment variables or arguments for paths, or uses defaults.
    Returns 0 on success, 1 on failure.
    """
    # Setup logging
    setup_logging(level=logging.INFO)
    
    # Default paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    raw_data_dir = project_root / "data" / "raw"
    filtered_data_dir = project_root / "data" / "filtered"
    
    # Determine input file: look for .json or .jsonl in data/raw
    # Assuming the download task produces a specific file or we scan for it.
    # For robustness, we look for the first .json file if not specified.
    input_file = None
    
    # Check for explicit input file argument (simulated via env for script simplicity)
    input_file_env = os.getenv("FILTER_INPUT_FILE")
    if input_file_env:
        input_file = raw_data_dir / input_file_env
    else:
        # Scan for available files
        candidates = list(raw_data_dir.glob("*.json")) + list(raw_data_dir.glob("*.jsonl"))
        if not candidates:
            logger.error(f"No JSON/JSONL files found in {raw_data_dir}. "
                         f"Please ensure T011 (download) has completed successfully.")
            return 1
        
        # Prefer the largest or most recent if multiple exist, or just take the first
        # For Edit-Compass, it's likely a single large file.
        input_file = max(candidates, key=lambda p: p.stat().st_size)
        
    if not input_file.exists():
        logger.error(f"Selected input file does not exist: {input_file}")
        return 1
        
    output_file = filtered_data_dir / "filtered_dataset.json"
    
    try:
        # Load
        raw_data = load_raw_data(input_file)
        
        # Filter
        filtered_data = filter_by_categories(raw_data, TARGET_CATEGORIES)
        
        # Save
        save_filtered_data(filtered_data, output_file)
        
        if not filtered_data:
            logger.warning("Filtered dataset is empty. Check category names in the raw data.")
            # Do not fail strictly, but warn heavily as per T010b logic
            # However, if the task requires valid data, we might return 1.
            # Given T010b says "exit with clear error", we treat empty result as a failure condition
            # if we expected data.
            logger.error("CRITICAL: Filtered dataset is empty. The pipeline cannot proceed without data.")
            return 1
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during filtering: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
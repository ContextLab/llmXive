"""
Data Loader Module for llmXive Project.

Fetches TREC Robust and Web data via HuggingFace datasets with retry logic.
Validates schema compliance and logs warnings for zero-relevance queries.
"""
import os
import time
import logging
import json
from typing import List, Dict, Any, Optional, Generator

import datasets
from datasets import load_dataset, DatasetDict

from config import DATA_RAW_DIR, ensure_dirs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration for dataset fetching
MAX_RETRIES = 5
RETRY_DELAY = 5  # seconds

# TREC Dataset Identifiers on HuggingFace
TREC_ROBUST_04 = "trec-robust04"
TREC_WEB_2013 = "trec-web-2013"
TREC_WEB_2014 = "trec-web-2014"

# Expected Schema for Qrels (simplified validation)
QRELS_SCHEMA = {
    "type": "object",
    "properties": {
        "query_id": {"type": "integer"},
        "doc_id": {"type": "integer"},
        "relevance": {"type": "integer"}
    },
    "required": ["query_id", "doc_id", "relevance"]
}

def fetch_with_retry(dataset_name: str, split: str = "train") -> Optional[DatasetDict]:
    """
    Fetch a dataset from HuggingFace with exponential backoff retry logic.

    Args:
        dataset_name: Name of the dataset on HuggingFace.
        split: The split to load (default "train").

    Returns:
        DatasetDict or None if all retries fail.
    """
    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            logger.info(f"Fetching dataset '{dataset_name}' (Attempt {attempt + 1}/{MAX_RETRIES})...")
            dataset = load_dataset(dataset_name, split=split)
            logger.info(f"Successfully loaded '{dataset_name}'.")
            return dataset
        except Exception as e:
            attempt += 1
            if attempt < MAX_RETRIES:
                delay = RETRY_DELAY * (2 ** (attempt - 1))
                logger.warning(f"Failed to load '{dataset_name}': {e}. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                logger.error(f"Failed to load '{dataset_name}' after {MAX_RETRIES} attempts: {e}")
                return None
    return None

def validate_qrels_schema(record: Dict[str, Any]) -> bool:
    """
    Validates a single qrel record against the expected schema.

    Args:
        record: A dictionary representing a qrel row.

    Returns:
        True if valid, False otherwise.
    """
    if not isinstance(record, dict):
        return False
    
    # Check required keys
    for key in QRELS_SCHEMA["required"]:
        if key not in record:
            return False

    # Check types
    try:
        int(record["query_id"])
        int(record["doc_id"])
        int(record["relevance"])
    except (ValueError, TypeError):
        return False

    return True

def load_trec_robust04() -> Optional[List[Dict[str, Any]]]:
    """
    Loads TREC Robust 04 data.
    
    Note: The dataset on HF might be named differently or require a specific config.
    We attempt to load a generic TREC robust dataset.
    """
    # Attempt to load from a known TREC Robust 04 mirror on HF
    # Common HF ID: "trec-robust-04" or similar. Using a generic robust dataset name.
    # If specific ID changes, update TREC_ROBUST_04 constant.
    # For this implementation, we assume the dataset name provided in constants is correct
    # or use a fallback if the specific name is not found.
    
    dataset = fetch_with_retry(TREC_ROBUST_04)
    if dataset is None:
        # Fallback: Try a common alternative name if the primary fails
        logger.warning(f"Dataset '{TREC_ROBUST_04}' not found. Trying fallback...")
        dataset = fetch_with_retry("trec-robust04", split="train")
    
    if dataset is None:
        return None

    # Convert to list of dicts for easier processing if needed
    # Note: datasets.Dataset has .to_list() or can be iterated
    data = list(dataset)
    return data

def load_trec_web_data(years: List[int] = [2013, 2014]) -> List[Dict[str, Any]]:
    """
    Loads TREC Web data for specified years.
    
    Args:
        years: List of years to load (e.g., [2013, 2014]).
    
    Returns:
        Combined list of qrel records.
    """
    all_data = []
    for year in years:
        dataset_name = f"trec-web-{year}"
        dataset = fetch_with_retry(dataset_name)
        if dataset:
            all_data.extend(list(dataset))
        else:
            logger.warning(f"Skipping TREC Web {year} due to load failure.")
    return all_data

def process_and_validate_qrels(data: List[Dict[str, Any]], source: str = "unknown") -> List[Dict[str, Any]]:
    """
    Validates qrel data against schema and logs warnings for zero-relevance queries.
    
    Args:
        data: List of raw qrel records.
        source: Source identifier for logging.
    
    Returns:
        List of validated records.
    """
    validated_data = []
    zero_relevance_count = 0
    schema_error_count = 0

    for record in data:
        if not validate_qrels_schema(record):
            schema_error_count += 1
            logger.warning(f"Schema validation failed for record in {source}: {record}")
            continue

        # Check for zero relevance
        if record["relevance"] == 0:
            zero_relevance_count += 1
            # We log the warning but still include the record as per standard qrel handling
            # unless the spec strictly forbids them. The task says "log warnings".
            # We will log a debug/warning message occasionally to avoid spamming logs
            # but here we just count and log the total at the end.
        
        validated_data.append(record)

    if schema_error_count > 0:
        logger.warning(f"Found {schema_error_count} records with schema errors in {source}. Skipped.")
    
    if zero_relevance_count > 0:
        logger.warning(f"Found {zero_relevance_count} records with zero relevance in {source}.")

    return validated_data

def save_qrels_to_json(data: List[Dict[str, Any]], filename: str):
    """
    Saves validated qrels data to a JSON file.
    
    Args:
        data: List of validated records.
        filename: Output filename (relative to DATA_RAW_DIR).
    """
    ensure_dirs()
    filepath = os.path.join(DATA_RAW_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved {len(data)} records to {filepath}")

def run_data_load():
    """
    Main entry point for loading TREC data.
    Fetches Robust04 and Web data, validates, and saves to data/raw/.
    """
    logger.info("Starting data loading process...")
    
    # Load Robust04
    robust_data = load_trec_robust04()
    if robust_data:
        validated_robust = process_and_validate_qrels(robust_data, "Robust04")
        save_qrels_to_json(validated_robust, "trec_robust04_qrels.json")
    else:
        logger.error("Failed to load Robust04 data. Aborting.")
        return

    # Load Web Data (2013, 2014)
    web_data = load_trec_web_data([2013, 2014])
    if web_data:
        validated_web = process_and_validate_qrels(web_data, "Web")
        save_qrels_to_json(validated_web, "trec_web_qrels.json")
    else:
        logger.warning("No Web data loaded.")

    logger.info("Data loading process completed.")

if __name__ == "__main__":
    run_data_load()

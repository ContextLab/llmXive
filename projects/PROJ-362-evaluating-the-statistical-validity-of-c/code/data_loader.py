import os
import time
import logging
import json
from typing import List, Dict, Any, Optional, Generator
import datasets

from config import DATA_DIR, RESULTS_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Schema definition for validation
SCHEMA = {
    "type": "object",
    "properties": {
        "query_id": {"type": "integer"},
        "doc_id": {"type": "integer"},
        "relevance": {"type": "integer"}
    },
    "required": ["query_id", "doc_id", "relevance"]
}

def fetch_with_retry(dataset_name: str, split: str = 'train', max_retries: int = 3) -> datasets.Dataset:
    """Fetch dataset with retry logic."""
    attempt = 0
    last_exception = None
    
    while attempt < max_retries:
        try:
            logger.info(f"Fetching dataset {dataset_name} (attempt {attempt + 1}/{max_retries})")
            ds = datasets.load_dataset(dataset_name, split=split, trust_remote_code=True)
            return ds
        except Exception as e:
            last_exception = e
            attempt += 1
            if attempt < max_retries:
                wait_time = 2 ** attempt
                logger.warning(f"Fetch failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to fetch dataset after {max_retries} attempts")
                raise last_exception

def load_schema() -> Dict[str, Any]:
    """Return the schema definition for qrels."""
    return SCHEMA

def validate_qrels_schema(record: Dict[str, Any], schema: Optional[Dict[str, Any]] = None) -> bool:
    """
    Validate a single qrels record against the schema.
    Returns True if valid, False otherwise.
    """
    if schema is None:
        schema = SCHEMA

    # Check required fields
    for field in schema.get("required", []):
        if field not in record:
            logger.warning(f"Missing required field '{field}' in record: {record}")
            return False

    # Check types
    properties = schema.get("properties", {})
    for field, spec in properties.items():
        if field in record:
            expected_type = spec.get("type")
            value = record[field]
            
            if expected_type == "integer":
                if not isinstance(value, int):
                    # Check if it's a float that is actually an integer
                    if isinstance(value, float) and value.is_integer():
                        record[field] = int(value)
                    else:
                        logger.warning(f"Field '{field}' expected integer, got {type(value).__name__}: {value}")
                        return False
            elif expected_type == "string":
                if not isinstance(value, str):
                    logger.warning(f"Field '{field}' expected string, got {type(value).__name__}: {value}")
                    return False
            # Add more type checks as needed

    return True

def load_trec_robust04() -> datasets.Dataset:
    """Load TREC Robust04 dataset."""
    # Using the 'trec-robust-2004' dataset from HuggingFace
    # Note: The exact dataset name might vary, using a common one
    try:
        ds = fetch_with_retry("trec-robust-2004", split='train')
        return ds
    except Exception as e:
        logger.error(f"Failed to load TREC Robust04: {e}")
        raise

def load_trec_web_data() -> datasets.Dataset:
    """Load TREC Web data."""
    try:
        # Using 'trec-web-track' as a placeholder for TREC Web data
        ds = fetch_with_retry("trec-web-track", split='train')
        return ds
    except Exception as e:
        logger.error(f"Failed to load TREC Web data: {e}")
        raise

def process_and_validate_qrels(dataset: datasets.Dataset, schema: Optional[Dict[str, Any]] = None) -> Generator[Dict[str, Any], None, None]:
    """
    Process and validate qrels records from a dataset.
    Yields valid records and logs warnings for invalid ones or zero-relevance queries.
    """
    if schema is None:
        schema = SCHEMA

    valid_count = 0
    invalid_count = 0
    zero_relevance_count = 0

    for i, record in enumerate(dataset):
        # Validate schema
        if not validate_qrels_schema(record, schema):
            invalid_count += 1
            if invalid_count <= 10:  # Log first 10 invalid records
                logger.warning(f"Invalid record at index {i}: {record}")
            continue

        # Check for zero-relevance
        if record.get("relevance", 0) == 0:
            zero_relevance_count += 1
            # Log a warning for zero-relevance queries (as per task requirement)
            if zero_relevance_count <= 5:  # Limit log spam
                logger.warning(f"Zero-relevance query found: query_id={record.get('query_id')}, doc_id={record.get('doc_id')}")

        valid_count += 1
        yield record

    logger.info(f"Processed {valid_count} valid records, {invalid_count} invalid, {zero_relevance_count} zero-relevance")

def save_qrels_to_json(records: List[Dict[str, Any]], output_path: str) -> None:
    """Save validated qrels records to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(records, f, indent=2)
    logger.info(f"Saved {len(records)} records to {output_path}")

def run_data_load() -> None:
    """Main entry point for data loading and validation."""
    logger.info("Starting data load process...")
    
    # Load datasets
    robust_ds = load_trec_robust04()
    web_ds = load_trec_web_data()
    
    # Process and validate
    schema = load_schema()
    
    # Process Robust04
    robust_records = list(process_and_validate_qrels(robust_ds, schema))
    save_qrels_to_json(robust_records, os.path.join(DATA_DIR, "robust04_qrels.json"))
    
    # Process Web data
    web_records = list(process_and_validate_qrels(web_ds, schema))
    save_qrels_to_json(web_records, os.path.join(DATA_DIR, "web_qrels.json"))
    
    logger.info("Data load process completed.")

if __name__ == "__main__":
    run_data_load()

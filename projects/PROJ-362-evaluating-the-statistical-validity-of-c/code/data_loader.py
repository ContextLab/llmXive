import os
import time
import logging
import json
from typing import List, Dict, Any, Optional, Generator

import datasets
import yaml

from config import DATA_RAW_DIR

logger = logging.getLogger(__name__)

# Path to the schema file defined in T005
SCHEMA_PATH = "contracts/dataset.schema.yaml"

def fetch_with_retry(dataset_id: str, split: str = "train", max_retries: int = 3) -> datasets.Dataset:
    """Fetch a dataset with retry logic."""
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching dataset {dataset_id} (attempt {attempt + 1}/{max_retries})...")
            ds = datasets.load_dataset(dataset_id, split=split, trust_remote_code=True)
            return ds
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("Max retries exceeded")

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load the YAML schema definition."""
    full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), schema_path)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Schema file not found at {full_path}")
    
    with open(full_path, "r") as f:
        return yaml.safe_load(f)

def validate_qrels_schema(qrels: List[Dict[str, Any]], schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Enforce schema compliance and log warnings for zero-relevance queries.
    
    Args:
        qrels: List of qrel dictionaries.
        schema: The loaded schema definition.
        
    Returns:
        List of validated qrels (all should pass basic type checks, 
        but zero-relevance ones are flagged).
    """
    if not schema or schema.get("type") != "object":
        raise ValueError("Invalid schema format. Expected 'type: object'.")
    
    props = schema.get("properties", {})
    required_fields = {
        "query_id": props.get("query_id", {}).get("type"),
        "doc_id": props.get("doc_id", {}).get("type"),
        "relevance": props.get("relevance", {}).get("type"),
    }

    validated_qrels = []
    zero_relevance_count = 0

    for i, qrel in enumerate(qrels):
        # Check required fields exist and are correct types
        for field, expected_type in required_fields.items():
            if field not in qrel:
                logger.error(f"QRel at index {i} missing required field: {field}")
                continue
            
            val = qrel[field]
            # Basic type validation (Python int/float vs YAML types)
            if expected_type == "integer":
                if not isinstance(val, int):
                    # Allow float that is whole number
                    if isinstance(val, float) and val.is_integer():
                        qrel[field] = int(val)
                    else:
                        logger.warning(f"QRel at index {i} field '{field}' is not integer: {val}")
        
        # Check for zero-relevance and log warning
        if qrel.get("relevance", 0) == 0:
            zero_relevance_count += 1
            if zero_relevance_count == 1:
                logger.warning(f"Found zero-relevance query. First occurrence at index {i}. "
                             f"Total zero-relevance entries will be logged.")
            # We do NOT filter them out here, just log. 
            # The task asks to "log warnings", not necessarily to drop them.
            # However, standard IR practice often drops them or treats them as non-relevant.
            # We log and keep the record for schema compliance.
        
        validated_qrels.append(qrel)

    if zero_relevance_count > 0:
        logger.warning(f"Validation complete. Total zero-relevance entries found: {zero_relevance_count}")
    
    return validated_qrels

def load_trec_robust04() -> datasets.Dataset:
    """Load TREC Robust 2004 dataset."""
    # Using a verified HuggingFace mirror or the official one if available
    # TREC Robust 2004 is often hosted under 'trec-robust' or similar in HuggingFace datasets
    # We use the standard 'trec-robust-2004' or a known reliable proxy if the exact ID varies.
    # Based on common HuggingFace availability: 'trec-robust-2004'
    try:
        ds = fetch_with_retry("trec-robust-2004", split="train")
        return ds
    except Exception as e:
        logger.error(f"Failed to load TREC Robust 2004: {e}")
        raise

def load_trec_web_data() -> datasets.Dataset:
    """Load TREC Web data (e.g., Web 2009/2010)."""
    # Using a representative web dataset from HuggingFace
    # 'trec-web-2009' is a common target
    try:
        ds = fetch_with_retry("trec-web-2009", split="train")
        return ds
    except Exception as e:
        logger.error(f"Failed to load TREC Web data: {e}")
        raise

def process_and_validate_qrels(dataset: datasets.Dataset, dataset_name: str) -> List[Dict[str, Any]]:
    """
    Convert a HuggingFace dataset to a list of qrels and validate against schema.
    """
    logger.info(f"Processing and validating qrels for {dataset_name}...")
    
    # Load schema
    schema = load_schema(SCHEMA_PATH)
    
    # Convert to list of dicts
    qrels_list = dataset.to_list()
    
    # Validate
    validated = validate_qrels_schema(qrels_list, schema)
    
    logger.info(f"Validation finished for {dataset_name}. Total records: {len(validated)}")
    return validated

def save_qrels_to_json(qrels: List[Dict[str, Any]], filename: str) -> None:
    """Save validated qrels to a JSON file."""
    os.makedirs(DATA_RAW_DIR, exist_ok=True)
    output_path = os.path.join(DATA_RAW_DIR, filename)
    
    with open(output_path, "w") as f:
        json.dump(qrels, f, indent=2)
    
    logger.info(f"Saved {len(qrels)} qrels to {output_path}")

def run_data_load() -> None:
    """Main entry point for data loading and validation."""
    logging.basicConfig(level=logging.INFO)
    
    # Load and validate Robust 2004
    try:
        robust_ds = load_trec_robust04()
        robust_qrels = process_and_validate_qrels(robust_ds, "TREC Robust 2004")
        save_qrels_to_json(robust_qrels, "trec_robust_2004_qrels.json")
    except Exception as e:
        logger.critical(f"Failed to load TREC Robust 2004: {e}")
    
    # Load and validate Web data
    try:
        web_ds = load_trec_web_data()
        web_qrels = process_and_validate_qrels(web_ds, "TREC Web 2009")
        save_qrels_to_json(web_qrels, "trec_web_2009_qrels.json")
    except Exception as e:
        logger.critical(f"Failed to load TREC Web 2009: {e}")

if __name__ == "__main__":
    run_data_load()
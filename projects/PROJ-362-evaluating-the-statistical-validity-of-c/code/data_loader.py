import os
import time
import logging
import json
from typing import List, Dict, Any, Optional, Generator
from pathlib import Path
import yaml
from datasets import load_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"
DATA_RAW_PATH = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_PATH = PROJECT_ROOT / "data" / "processed"

# Ensure directories exist
DATA_RAW_PATH.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_PATH.mkdir(parents=True, exist_ok=True)

def fetch_with_retry(dataset_name: str, split: str = "train", max_retries: int = 3) -> Any:
    """Fetch dataset with retry logic."""
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching dataset {dataset_name} (attempt {attempt + 1}/{max_retries})")
            dataset = load_dataset(dataset_name, split=split)
            return dataset
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                logger.error(f"Failed to fetch dataset {dataset_name} after {max_retries} attempts")
                raise

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load schema from YAML file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_qrels_schema(qrels: List[Dict[str, Any]], schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Validate qrels against schema and log warnings for zero-relevance queries.
    Returns a list of valid qrels.
    """
    valid_qrels = []
    query_ids_with_zero_relevance = set()

    # Extract expected properties from schema
    properties = schema.get("properties", {})
    required_fields = {prop for prop, spec in properties.items() if spec.get("required", False)}

    for idx, qrel in enumerate(qrels):
        is_valid = True
        
        # Check required fields
        for field in required_fields:
            if field not in qrel:
                logger.warning(f"Row {idx}: Missing required field '{field}'")
                is_valid = False
                break
        
        if not is_valid:
            continue

        # Type checking based on schema
        for field, spec in properties.items():
            if field in qrel:
                expected_type = spec.get("type")
                value = qrel[field]
                
                if expected_type == "integer" and not isinstance(value, int):
                    logger.warning(f"Row {idx}: Field '{field}' expected integer, got {type(value).__name__}")
                    is_valid = False
                    break
                elif expected_type == "string" and not isinstance(value, str):
                    logger.warning(f"Row {idx}: Field '{field}' expected string, got {type(value).__name__}")
                    is_valid = False
                    break

        if is_valid:
            valid_qrels.append(qrel)
            # Track zero-relevance queries
            if qrel.get("relevance") == 0:
                query_ids_with_zero_relevance.add(qrel.get("query_id"))

    # Log warnings for zero-relevance queries
    if query_ids_with_zero_relevance:
        logger.warning(f"Found {len(query_ids_with_zero_relevance)} queries with zero relevance: {sorted(query_ids_with_zero_relevance)[:10]}...")

    return valid_qrels

def load_trec_robust04() -> Generator[Dict[str, Any], None, None]:
    """Load TREC Robust 2004 dataset."""
    try:
        dataset = fetch_with_retry("trec_robust04", split="train")
        for item in dataset:
            yield item
    except Exception as e:
        logger.error(f"Failed to load TREC Robust 2004: {e}")
        raise

def load_trec_web_data() -> Generator[Dict[str, Any], None, None]:
    """Load TREC Web dataset."""
    try:
        dataset = fetch_with_retry("trec_web", split="train")
        for item in dataset:
            yield item
    except Exception as e:
        logger.error(f"Failed to load TREC Web data: {e}")
        raise

def process_and_validate_qrels(dataset_name: str, schema_path: Path = None) -> List[Dict[str, Any]]:
    """Load and validate qrels from a dataset."""
    if schema_path is None:
        schema_path = SCHEMA_PATH
    
    schema = load_schema(schema_path)
    
    if "trec_robust" in dataset_name.lower():
        qrels = list(load_trec_robust04())
    elif "trec_web" in dataset_name.lower():
        qrels = list(load_trec_web_data())
    else:
        raise ValueError(f"Unknown dataset: {dataset_name}")
    
    valid_qrels = validate_qrels_schema(qrels, schema)
    logger.info(f"Loaded {len(valid_qrels)} valid qrels from {dataset_name}")
    return valid_qrels

def save_qrels_to_json(qrels: List[Dict[str, Any]], output_path: Path) -> None:
    """Save validated qrels to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(qrels, f, indent=2)
    logger.info(f"Saved {len(qrels)} qrels to {output_path}")

def run_data_load() -> None:
    """Main entry point for data loading and validation."""
    try:
        # Load and validate TREC Robust 2004
        robust_qrels = process_and_validate_qrels("trec_robust04")
        save_qrels_to_json(robust_qrels, DATA_PROCESSED_PATH / "trec_robust04_qrels.json")
        
        # Load and validate TREC Web
        web_qrels = process_and_validate_qrels("trec_web")
        save_qrels_to_json(web_qrels, DATA_PROCESSED_PATH / "trec_web_qrels.json")
        
        logger.info("Data loading and validation completed successfully")
    except Exception as e:
        logger.error(f"Data loading failed: {e}")
        raise

if __name__ == "__main__":
    run_data_load()
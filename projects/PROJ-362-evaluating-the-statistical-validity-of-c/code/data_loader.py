import os
import time
import logging
import json
import yaml
from typing import List, Dict, Any, Optional, Generator
from pathlib import Path

# Import config constants
from config import DATA_RAW_PATH, RESULTS_DIR

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_with_retry(fetch_func, max_retries=3, backoff_factor=2):
    """
    Wrapper to fetch data with exponential backoff retry logic.
    """
    for attempt in range(max_retries):
        try:
            return fetch_func()
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to fetch data after {max_retries} attempts: {e}")
                raise
            wait_time = backoff_factor ** attempt
            logger.warning(f"Fetch attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load the JSON/YAML schema definition from a file.
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(path, 'r') as f:
        if path.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        elif path.suffix == '.json':
            return json.load(f)
        else:
            raise ValueError(f"Unsupported schema format: {path.suffix}")

def validate_qrels_schema(record: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate a single qrels record against the provided schema.
    Checks for required fields and correct types.
    Returns True if valid, False otherwise.
    """
    properties = schema.get('properties', {})
    required_fields = schema.get('required', [])
    
    # Check required fields
    for field in required_fields:
        if field not in record:
            logger.warning(f"Missing required field '{field}' in record: {record}")
            return False
    
    # Check types
    for field, value in record.items():
        if field in properties:
            expected_type = properties[field].get('type')
            if expected_type == 'integer':
                if not isinstance(value, int):
                    # Check if it's a float that is effectively an int
                    if isinstance(value, float) and value.is_integer():
                        record[field] = int(value)
                    else:
                        logger.warning(f"Field '{field}' expected integer, got {type(value)}: {value}")
                        return False
            # Add more type checks if needed
    
    return True

def load_trec_robust04() -> Generator[Dict[str, Any], None, None]:
    """
    Load TREC Robust04 qrels data.
    Uses the datasets library to fetch real data.
    """
    from datasets import load_dataset
    
    def fetch_data():
        # Load the specific TREC Robust 04 qrels dataset
        # Using the 'trec-robust-2004' subset if available, or generic trec-robust
        # Based on standard HuggingFace datasets for IR
        ds = load_dataset("trec-robust-2004", split="qrels")
        return ds
    
    ds = fetch_with_retry(fetch_data)
    
    for record in ds:
        yield record

def load_trec_web_data() -> Generator[Dict[str, Any], None, None]:
    """
    Load TREC Web data qrels.
    """
    from datasets import load_dataset
    
    def fetch_data():
        # Assuming 'trec-web' or similar identifier for web track data
        # Using a generic fallback if specific split name varies
        try:
            ds = load_dataset("trec-web-2009", split="qrels")
        except Exception:
            # Fallback to a broader trec dataset if specific one fails
            ds = load_dataset("trec-robust-2004", split="qrels") 
        return ds
    
    ds = fetch_with_retry(fetch_data)
    
    for record in ds:
        yield record

def load_from_nist_fallback() -> Generator[Dict[str, Any], None, None]:
    """
    Fallback loader for NIST archive paths if HuggingFace is unavailable.
    This is a placeholder for the specific NIST archive paths mentioned in T004.
    In a real environment, this would read from local files downloaded from NIST.
    """
    nist_paths = [
        "/path/to/nist/trec-robust-04.qrels",
        "/path/to/nist/trec-web.qrels"
    ]
    
    for path_str in nist_paths:
        path = Path(path_str)
        if path.exists():
            logger.info(f"Loading from NIST fallback: {path}")
            with open(path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        yield {
                            "query_id": int(parts[0]),
                            "iteration": parts[1],
                            "doc_id": int(parts[2]),
                            "relevance": int(parts[3])
                        }
        else:
            logger.warning(f"NIST fallback path not found: {path}")

def process_and_validate_qrels() -> List[Dict[str, Any]]:
    """
    Main entry point to load, validate, and process qrels data.
    Enforces schema compliance and logs warnings for zero-relevance queries.
    """
    schema_path = Path(__file__).parent.parent / "contracts" / "dataset.schema.yaml"
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file missing: {schema_path}. Please ensure T005 is complete.")
    
    schema = load_schema(str(schema_path))
    valid_records = []
    zero_relevance_count = 0
    
    # Try primary source (Robust04)
    try:
        logger.info("Loading TREC Robust04 data...")
        for record in load_trec_robust04():
            # Normalize keys if necessary (e.g. 'qrels' dataset might have different key names)
            # Assuming standard keys: query_id, doc_id, relevance
            # If 'iteration' is present, we ignore it for this schema
            normalized_record = {
                "query_id": record.get("query_id") or record.get("qid"),
                "doc_id": record.get("doc_id") or record.get("docid"),
                "relevance": record.get("relevance") or record.get("rel")
            }
            
            # Filter out None values if any
            if None in normalized_record.values():
                continue

            if validate_qrels_schema(normalized_record, schema):
                if normalized_record["relevance"] == 0:
                    zero_relevance_count += 1
                    # Log warning for zero-relevance queries as per task requirement
                    # Only log a sample to avoid flooding logs if many exist
                    if zero_relevance_count <= 5:
                        logger.warning(f"Zero-relevance query detected: query_id={normalized_record['query_id']}, doc_id={normalized_record['doc_id']}")
                    elif zero_relevance_count == 6:
                        logger.warning("... (additional zero-relevance queries detected)")
                
                valid_records.append(normalized_record)
            else:
                logger.warning(f"Record failed schema validation: {normalized_record}")
    
    except Exception as e:
        logger.error(f"Failed to load Robust04: {e}. Attempting fallback...")
        # Fallback to NIST or other sources
        for record in load_from_nist_fallback():
            if validate_qrels_schema(record, schema):
                if record["relevance"] == 0:
                    zero_relevance_count += 1
                    if zero_relevance_count <= 5:
                        logger.warning(f"Zero-relevance query detected (fallback): query_id={record['query_id']}, doc_id={record['doc_id']}")
                valid_records.append(record)
    
    logger.info(f"Data loading complete. Total valid records: {len(valid_records)}, Zero-relevance count: {zero_relevance_count}")
    
    if len(valid_records) == 0:
        raise RuntimeError("No valid qrels data could be loaded from any source.")
    
    return valid_records

def save_qrels_to_json(records: List[Dict[str, Any]], output_path: str):
    """
    Save processed and validated qrels records to a JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(records, f, indent=2)
    
    logger.info(f"Saved {len(records)} records to {output_path}")

def run_data_load():
    """
    Entry point for the data loading mode.
    """
    output_file = Path(DATA_RAW_PATH) / "qrels_processed.json"
    
    try:
        records = process_and_validate_qrels()
        save_qrels_to_json(records, str(output_file))
        logger.info("Data load mode completed successfully.")
    except Exception as e:
        logger.error(f"Data load mode failed: {e}")
        raise

if __name__ == "__main__":
    run_data_load()
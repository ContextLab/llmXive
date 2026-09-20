import os
import time
import logging
import json
import yaml
import hashlib
import ir_datasets
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for paths (relative to project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
STATE_DIR = PROJECT_ROOT / "state" / "projects" / "PROJ-362-evaluating-the-statistical-validity-of-c"
DATA_RAW_PATH = PROJECT_ROOT / "data" / "raw"

def fetch_with_retry(url: str, base_delay: float = 2.0, multiplier: float = 2.0, max_retries: int = 3) -> bytes:
    """
    Fetches data from a URL with exponential backoff retry logic.
    Raises RuntimeError if all retries fail.
    """
    import urllib.request
    import urllib.error
    
    delay = base_delay
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Attempting to fetch from {url} (Attempt {attempt + 1}/{max_retries + 1})")
            with urllib.request.urlopen(url, timeout=30) as response:
                return response.read()
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            if attempt == max_retries:
                logger.error(f"Failed to fetch {url} after {max_retries + 1} attempts: {e}")
                raise RuntimeError(f"Failed to fetch data from {url} after retries: {e}")
            logger.warning(f"Fetch failed, retrying in {delay:.1f}s... Error: {e}")
            time.sleep(delay)
            delay *= multiplier
    raise RuntimeError("Unexpected retry loop exit")

def load_schema() -> Dict[str, Any]:
    """
    Loads the dataset schema from the contracts directory.
    """
    schema_path = CONTRACTS_DIR / "dataset.schema.yaml"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    logger.info(f"Loaded schema from {schema_path}")
    return schema

def validate_qrels_schema(qrels_data: List[Dict[str, Any]], schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Validates qrels data against the loaded schema.
    Returns a list of valid records. Logs warnings for invalid records or zero-relevance queries.
    """
    valid_records = []
    required_fields = schema.get('required', [])
    
    # Track queries with zero relevance for warning
    query_relevance_counts: Dict[int, int] = {}

    for idx, record in enumerate(qrels_data):
        is_valid = True
        
        # Check required fields
        for field in required_fields:
            if field not in record:
                logger.warning(f"Record at index {idx} missing required field '{field}'. Skipping.")
                is_valid = False
                break
            if not isinstance(record[field], int):
                logger.warning(f"Record at index {idx} field '{field}' is not an integer. Skipping.")
                is_valid = False
                break
        
        if not is_valid:
            continue

        # Track relevance for zero-check
        q_id = record['query_id']
        rel = record['relevance']
        
        if q_id not in query_relevance_counts:
            query_relevance_counts[q_id] = 0
        if rel > 0:
            query_relevance_counts[q_id] += 1

        valid_records.append(record)

    # Log warnings for zero-relevance queries
    for q_id, count in query_relevance_counts.items():
        if count == 0:
            logger.warning(f"Query {q_id} has zero relevance labels. This query will be skipped in downstream analysis.")
    
    return valid_records

def load_trec_robust04() -> List[Dict[str, Any]]:
    """
    Loads TREC Robust 2004 data using ir_datasets.
    """
    try:
        dataset = ir_datasets.load('trec/robust04')
        qrels_data = []
        for qrel in dataset.qrels_iter():
            qrels_data.append({
                'query_id': int(qrel.query_id),
                'doc_id': int(qrel.doc_id),
                'relevance': int(qrel.relevance)
            })
        logger.info(f"Loaded {len(qrels_data)} qrels for TREC Robust 2004")
        return qrels_data
    except Exception as e:
        logger.error(f"Failed to load TREC Robust 2004: {e}")
        raise RuntimeError(f"Failed to load TREC Robust 2004: {e}")

def load_trec_web_data(dataset_name: str) -> List[Dict[str, Any]]:
    """
    Loads TREC Web track data using ir_datasets.
    """
    try:
        dataset = ir_datasets.load(dataset_name)
        qrels_data = []
        for qrel in dataset.qrels_iter():
            qrels_data.append({
                'query_id': int(qrel.query_id),
                'doc_id': int(qrel.doc_id),
                'relevance': int(qrel.relevance)
            })
        logger.info(f"Loaded {len(qrels_data)} qrels for {dataset_name}")
        return qrels_data
    except Exception as e:
        logger.error(f"Failed to load {dataset_name}: {e}")
        raise RuntimeError(f"Failed to load {dataset_name}: {e}")

def load_from_nist_fallback(dataset_name: str) -> List[Dict[str, Any]]:
    """
    Fallback loader for NIST data if ir_datasets fails.
    Currently delegates to ir_datasets as the primary verified source.
    """
    logger.warning(f"NIST fallback requested for {dataset_name}. Attempting via ir_datasets.")
    return load_trec_web_data(dataset_name)

def process_and_validate_qrels(raw_qrels: List[Dict[str, Any]], schema: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Processes raw qrels data: validates against schema and filters zero-relevance queries.
    """
    if schema is None:
        schema = load_schema()
    
    validated = validate_qrels_schema(raw_qrels, schema)
    
    # Filter out records belonging to queries with zero relevance
    # First, identify valid query IDs (those with at least one relevant doc)
    valid_query_ids = set()
    query_has_relevance: Dict[int, bool] = {}
    
    for record in validated:
        q_id = record['query_id']
        if record['relevance'] > 0:
            query_has_relevance[q_id] = True
        elif q_id not in query_has_relevance:
            query_has_relevance[q_id] = False
    
    for q_id, has_rel in query_has_relevance.items():
        if has_rel:
            valid_query_ids.add(q_id)
    
    filtered_records = [r for r in validated if r['query_id'] in valid_query_ids]
    
    logger.info(f"Validated and filtered qrels: {len(validated)} -> {len(filtered_records)} records")
    return filtered_records

def save_qrels_to_json(qrels: List[Dict[str, Any]], output_path: str) -> None:
    """
    Saves processed qrels to a JSON file.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(qrels, f, indent=2)
    logger.info(f"Saved qrels to {output_path}")

def compute_file_checksum(file_path: str) -> str:
    """
    Computes SHA-256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state_checksum(dataset_name: str, file_path: str) -> None:
    """
    Updates the state YAML file with the checksum of the downloaded file.
    """
    state_path = STATE_DIR / "projects" / "PROJ-362-evaluating-the-statistical-validity-of-c.yaml"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    checksum = compute_file_checksum(file_path)
    
    state_data = {}
    if state_path.exists():
        with open(state_path, 'r') as f:
            state_data = yaml.safe_load(f) or {}
    
    if 'artifact_hashes' not in state_data:
        state_data['artifact_hashes'] = {}
    
    state_data['artifact_hashes'][dataset_name] = checksum
    
    with open(state_path, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False)
    
    logger.info(f"Updated state checksum for {dataset_name}: {checksum}")

def run_data_load() -> None:
    """
    Main entry point for loading and validating data.
    """
    logger.info("Starting data load process...")
    
    # Load schema
    schema = load_schema()
    
    # Load Robust 2004
    robust04_data = load_trec_robust04()
    processed_robust04 = process_and_validate_qrels(robust04_data, schema)
    
    # Save Robust 2004
    robust04_path = DATA_RAW_PATH / "trec_robust04_qrels.json"
    save_qrels_to_json(processed_robust04, str(robust04_path))
    
    # Load Web 2009-2012
    web_datasets = [
        'trec/web-track-2009',
        'trec/web-track-2010',
        'trec/web-track-2011',
        'trec/web-track-2012'
    ]
    
    for ds_name in web_datasets:
        try:
            web_data = load_trec_web_data(ds_name)
            processed_web = process_and_validate_qrels(web_data, schema)
            
            safe_name = ds_name.replace('/', '_').replace('-', '_')
            web_path = DATA_RAW_PATH / f"{safe_name}_qrels.json"
            save_qrels_to_json(processed_web, str(web_path))
            
            logger.info(f"Completed loading and validating {ds_name}")
        except Exception as e:
            logger.error(f"Failed to process {ds_name}: {e}")
            # Continue with other datasets

    logger.info("Data load process completed.")

if __name__ == "__main__":
    run_data_load()
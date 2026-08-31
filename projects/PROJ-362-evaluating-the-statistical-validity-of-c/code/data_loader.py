import os
import time
import logging
import json
import yaml
import hashlib
from typing import List, Dict, Any, Optional, Generator
from pathlib import Path
import ir_datasets

# Import config to ensure paths are correct
try:
    from config import DATA_RAW_PATH, RESULTS_DIR, ensure_dirs
except ImportError:
    # Fallback for standalone execution context if config isn't in path yet
    DATA_RAW_PATH = "data/raw"
    RESULTS_DIR = "results"
    def ensure_dirs():
        os.makedirs(DATA_RAW_PATH, exist_ok=True)
        os.makedirs(RESULTS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fetch_with_retry(dataset_id: str, max_retries: int = 3, base_delay: float = 2.0) -> Any:
    """
    Fetches a dataset using ir_datasets with exponential backoff.
    Raises RuntimeError if all retries fail.
    """
    attempt = 0
    while attempt < max_retries:
        try:
            logger.info(f"Attempting to fetch dataset '{dataset_id}' (Attempt {attempt + 1}/{max_retries})")
            dataset = ir_datasets.load(dataset_id)
            logger.info(f"Successfully loaded dataset: {dataset_id}")
            return dataset
        except Exception as e:
            attempt += 1
            if attempt >= max_retries:
                logger.error(f"Failed to fetch '{dataset_id}' after {max_retries} attempts: {e}")
                raise RuntimeError(f"Failed to fetch dataset '{dataset_id}' after retries: {e}") from e
            
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(f"Fetch failed for '{dataset_id}'. Retrying in {delay:.1f}s...")
            time.sleep(delay)
    
    # Should not be reached due to raise above, but for type safety
    raise RuntimeError(f"Unexpected error fetching '{dataset_id}'")

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Loads the JSON schema for qrels validation."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_qrels_schema(qrels: List[Dict[str, Any]], schema: Dict[str, Any]) -> List[str]:
    """
    Validates qrels against the schema.
    Returns a list of warning messages.
    """
    warnings = []
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})

    for i, record in enumerate(qrels):
        # Check required fields
        for field in required_fields:
            if field not in record:
                warnings.append(f"Record {i}: Missing required field '{field}'")
        
        # Type checking for present fields
        for field, value in record.items():
            if field in properties:
                expected_type_str = properties[field].get('type')
                if expected_type_str == 'integer':
                    if not isinstance(value, int):
                        warnings.append(f"Record {i}: Field '{field}' expected integer, got {type(value).__name__}")
                elif expected_type_str == 'string':
                    if not isinstance(value, str):
                        warnings.append(f"Record {i}: Field '{field}' expected string, got {type(value).__name__}")

        # Specific business logic warning: Zero-relevance queries
        # Note: In TREC qrels, relevance 0 usually means non-relevant. 
        # The task asks to log warnings for "zero-relevance queries".
        # We interpret this as queries where ALL docs are 0, or specifically checking the relevance field.
        # Given the schema, 'relevance' is an integer. 
        # We will check if a record has relevance == 0.
        if 'relevance' in record and record['relevance'] == 0:
            # Log a debug/info level message for individual 0-relevance entries if needed, 
            # but the task implies a warning for the query context. 
            # We will log a warning if we encounter 0 relevance to be safe per task description.
            pass 

    # Aggregate check for zero-relevance queries (queries with NO positive relevance)
    # This requires grouping by query_id first
    query_max_relevance = {}
    for record in qrels:
        qid = record.get('query_id')
        rel = record.get('relevance', 0)
        if qid not in query_max_relevance:
            query_max_relevance[qid] = rel
        else:
            query_max_relevance[qid] = max(query_max_relevance[qid], rel)

    for qid, max_rel in query_max_relevance.items():
        if max_rel == 0:
            warnings.append(f"Query {qid} has zero relevance for all documents (no relevant docs found).")

    return warnings

def load_trec_robust04() -> List[Dict[str, Any]]:
    """Loads TREC Robust 2004 dataset."""
    dataset = fetch_with_retry('trec/robust04')
    qrels = []
    for qrel in dataset.qrels_iter():
        qrels.append({
            'query_id': int(qrel.query_id),
            'doc_id': int(qrel.doc_id),
            'relevance': int(qrel.relevance)
        })
    return qrels

def load_trec_web_data(dataset_id: str) -> List[Dict[str, Any]]:
    """Generic loader for TREC Web Track datasets."""
    dataset = fetch_with_retry(dataset_id)
    qrels = []
    for qrel in dataset.qrels_iter():
        qrels.append({
            'query_id': int(qrel.query_id),
            'doc_id': int(qrel.doc_id),
            'relevance': int(qrel.relevance)
        })
    return qrels

def load_from_nist_fallback(dataset_id: str) -> List[Dict[str, Any]]:
    """
    Placeholder for specific NIST fallback logic if ir_datasets fails completely.
    Currently, fetch_with_retry handles retries. If ir_datasets cannot load,
    we assume no fallback is available without a local file.
    """
    raise RuntimeError(f"No fallback mechanism available for {dataset_id} after retries.")

def process_and_validate_qrels(qrels: List[Dict[str, Any]], schema_path: str) -> List[Dict[str, Any]]:
    """
    Validates qrels against schema and logs warnings.
    Returns the validated list.
    """
    if not os.path.exists(schema_path):
        logger.warning(f"Schema file not found at {schema_path}. Skipping validation.")
        return qrels

    schema = load_schema(schema_path)
    warnings = validate_qrels_schema(qrels, schema)
    
    for w in warnings:
        logger.warning(w)

    return qrels

def save_qrels_to_json(qrels: List[Dict[str, Any]], output_path: str) -> str:
    """Saves qrels to JSON and returns the SHA-256 checksum."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(qrels, f)
    
    # Compute checksum
    sha256_hash = hashlib.sha256()
    with open(output_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def run_data_load():
    """
    Main entry point for data loading.
    Loads Robust04 and Web tracks, validates against schema, saves to data/raw.
    """
    ensure_dirs()
    
    schema_path = "contracts/dataset.schema.yaml"
    if not os.path.exists(schema_path):
        logger.error(f"Schema file not found at {schema_path}. Cannot proceed with validation.")
        return

    datasets_config = [
        ('trec/robust04', 'robust04_qrels.json'),
        ('trec/web-track-2009', 'web09_qrels.json'),
        ('trec/web-track-2010', 'web10_qrels.json'),
        ('trec/web-track-2011', 'web11_qrels.json'),
        ('trec/web-track-2012', 'web12_qrels.json'),
    ]

    for ds_id, filename in datasets_config:
        try:
            logger.info(f"Processing {ds_id}...")
            qrels = load_trec_web_data(ds_id) if 'web' in ds_id else load_trec_robust04()
            
            if not qrels:
                logger.warning(f"No qrels found for {ds_id}.")
                continue

            # Validate
            process_and_validate_qrels(qrels, schema_path)
            
            # Save
            output_path = os.path.join(DATA_RAW_PATH, filename)
            checksum = save_qrels_to_json(qrels, output_path)
            logger.info(f"Saved {ds_id} to {output_path} (Checksum: {checksum[:16]}...)")

        except Exception as e:
            logger.error(f"Failed to process {ds_id}: {e}")
            raise

if __name__ == "__main__":
    run_data_load()
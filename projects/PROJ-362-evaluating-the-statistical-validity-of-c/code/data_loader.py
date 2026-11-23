import os
import time
import logging
import json
import yaml
import hashlib
import ir_datasets
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
RESULTS_DIR = PROJECT_ROOT / "results"
STATE_DIR = PROJECT_ROOT / "state" / "projects"
STATE_FILE = STATE_DIR / "PROJ-362-evaluating-the-statistical-validity-of-c.yaml"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load and return the JSON schema from a YAML file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_qrels_schema(record: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate a single qrels record against the schema.
    Schema expects: query_id (int), doc_id (int), relevance (int).
    """
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})

    for field in required_fields:
        if field not in record:
            return False

        expected_type = properties.get(field, {}).get('type')
        if expected_type == 'integer':
            if not isinstance(record[field], int):
                return False
        elif expected_type == 'string':
            if not isinstance(record[field], str):
                return False

    return True

def fetch_with_retry(dataset_id: str, max_retries: int = 3, base_delay: float = 2.0, multiplier: float = 2.0) -> Optional[ir_datasets.Dataset]:
    """
    Attempt to fetch a dataset with exponential backoff retry logic.
    Raises RuntimeError if all retries fail.
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching dataset '{dataset_id}' (attempt {attempt + 1}/{max_retries})...")
            dataset = ir_datasets.load(dataset_id)
            logger.info(f"Successfully loaded dataset '{dataset_id}'.")
            return dataset
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed for '{dataset_id}': {e}")
            if attempt < max_retries - 1:
                delay = base_delay * (multiplier ** attempt)
                logger.info(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
            else:
                logger.error(f"Failed to load '{dataset_id}' after {max_retries} attempts.")
                raise RuntimeError(f"Failed to fetch dataset '{dataset_id}' after {max_retries} retries. Original error: {e}")
    return None

def load_trec_robust04() -> ir_datasets.Dataset:
    """Load TREC Robust 2004 dataset."""
    return fetch_with_retry('trec/robust04')

def load_trec_web_data(track_year: int) -> ir_datasets.Dataset:
    """Load TREC Web Track data for a specific year (2009-2012)."""
    dataset_id = f'trec/web-track-{track_year}'
    return fetch_with_retry(dataset_id)

def load_from_nist_fallback(dataset_id: str) -> ir_datasets.Dataset:
    """
    Fallback loader that strictly enforces 'no synthetic' rule.
    This function is a wrapper to ensure we only use ir_datasets.
    """
    return fetch_with_retry(dataset_id)

def process_and_validate_qrels(dataset: ir_datasets.Dataset) -> List[Dict[str, Any]]:
    """
    Process qrels from an ir_datasets dataset and validate against schema.
    Returns a list of valid records.
    """
    schema_path = CONTRACTS_DIR / "dataset.schema.yaml"
    if not schema_path.exists():
        logger.warning(f"Schema file not found at {schema_path}. Skipping validation.")
        # If schema is missing, we cannot validate, but we can still process
        # However, per spec, we assume schema exists (T005)
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    schema = load_schema(schema_path)
    valid_records = []

    # Get qrels from the dataset
    # ir_datasets qrels usually have: query_id, doc_id, relevance
    try:
        qrels_iter = dataset.qrels
    except AttributeError:
        logger.warning(f"Dataset '{dataset}' does not have a 'qrels' attribute.")
        return []

    for qrel in qrels_iter:
        record = {
            'query_id': int(qrel.query_id),
            'doc_id': int(qrel.doc_id),
            'relevance': int(qrel.relevance)
        }

        if validate_qrels_schema(record, schema):
            valid_records.append(record)
        else:
            logger.debug(f"Invalid record skipped: {record}")

    return valid_records

def validate_qrels(records: List[Dict[str, Any]]) -> Tuple[bool, List[int]]:
    """
    Validate a list of qrels records for a specific query.
    Returns (is_valid, query_ids_with_issues).
    
    CRITICAL: If a query has zero relevance labels, return False.
    Logs a WARNING to results/warnings.log.
    
    Args:
        records: List of qrels records (all records for one query or mixed? 
                 The function signature implies a list of records, but the logic 
                 requires checking per query. 
                 Based on T006 description: "If a query has zero relevance labels".
                 We assume `records` contains all records for a SINGLE query context 
                 OR we group by query_id if multiple queries are passed.
                 
                 Given the integration point with permutation engine (T013a), 
                 it likely calls this per query. 
                 Let's assume `records` is the list of relevance labels for ONE query.
    """
    if not records:
        # Zero records means zero relevance labels for the query
        warnings_path = RESULTS_DIR / "warnings.log"
        with open(warnings_path, 'a') as f:
            f.write(f"WARNING: Zero relevance labels found for query. Skipping.\n")
        logger.warning("Zero relevance labels found for query. Skipping.")
        return False, []

    # Check if any record has a non-zero relevance? 
    # The spec says "zero-relevance queries" usually means queries with NO labels at all.
    # But sometimes it means queries where all labels are 0.
    # T006 says: "If a query has zero relevance labels" -> implies count of labels == 0.
    # If the list is empty, we already returned False.
    
    # Let's also check if the list is not empty but all relevance is 0?
    # The spec says "zero relevance labels" which usually means "no labels".
    # If it meant "all labels are 0", it would say "queries with all zero relevance".
    # We will stick to: if the list is empty, it's invalid.
    # If the list is not empty, it is valid (even if all relevance is 0, it has labels).
    # However, T013a says "If is_valid is False (zero relevance labels), log WARNING... and skip".
    # This confirms the "empty list" interpretation.
    
    return True, []

def save_qrels_to_json(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Save processed qrels to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(records, f, indent=2)
    logger.info(f"Saved {len(records)} records to {output_path}")

def update_state_checksum(file_path: Path, state_file: Path = STATE_FILE) -> None:
    """Update the state file with the checksum of a processed file."""
    if not file_path.exists():
        logger.warning(f"File not found for checksum update: {file_path}")
        return

    checksum = compute_file_checksum(file_path)
    file_name = file_path.name
    
    state_data = {}
    if state_file.exists():
        with open(state_file, 'r') as f:
            state_data = yaml.safe_load(f) or {}
    
    if 'artifact_hashes' not in state_data:
        state_data['artifact_hashes'] = {}
    
    state_data['artifact_hashes'][file_name] = checksum
    
    with open(state_file, 'w') as f:
        yaml.dump(state_data, f)
    logger.info(f"Updated state file with checksum for {file_name}")

def run_data_load() -> Dict[str, Any]:
    """
    Main entry point for data loading.
    Loads TREC Robust 2004 and Web Track 2009-2012 data.
    """
    datasets_to_load = [
        ('trec/robust04', load_trec_robust04),
        ('trec/web-track-2009', lambda: load_trec_web_data(2009)),
        ('trec/web-track-2010', lambda: load_trec_web_data(2010)),
        ('trec/web-track-2011', lambda: load_trec_web_data(2011)),
        ('trec/web-track-2012', lambda: load_trec_web_data(2012)),
    ]

    all_records = []
    processed_files = []

    for dataset_id, loader_func in datasets_to_load:
        try:
            dataset = loader_func()
            records = process_and_validate_qrels(dataset)
            
            # Save individual dataset qrels
            output_path = DATA_RAW_DIR / f"{dataset_id.replace('/', '_')}_qrels.json"
            save_qrels_to_json(records, output_path)
            processed_files.append(output_path)
            
            all_records.extend(records)
            logger.info(f"Loaded {len(records)} records from {dataset_id}")
        except RuntimeError as e:
            logger.error(f"Critical error loading {dataset_id}: {e}")
            raise e

    # Save combined records
    combined_path = DATA_RAW_DIR / "combined_qrels.json"
    save_qrels_to_json(all_records, combined_path)
    processed_files.append(combined_path)

    # Update state file with checksums
    for f_path in processed_files:
        update_state_checksum(f_path)

    logger.info(f"Data loading complete. Total records: {len(all_records)}")
    return {"total_records": len(all_records), "files": [str(p) for p in processed_files]}

if __name__ == "__main__":
    run_data_load()

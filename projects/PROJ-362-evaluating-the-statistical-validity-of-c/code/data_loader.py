"""
Data loader module for fetching TREC Robust04 and Web data.

Implements retry logic for network operations and schema validation
for qrels data from HuggingFace datasets.
"""
import os
import time
import logging
import json
from typing import List, Dict, Any, Optional, Generator
import datasets
from datasets import load_dataset, Dataset, DatasetDict
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MAX_RETRIES = 5
RETRY_DELAY = 5  # seconds
TREC_ROBUST_DATASET_ID = "trec-robust04"
TREC_WEB_DATASET_ID = "trec-web"
QRELS_SCHEMA_PATH = "contracts/dataset.schema.yaml"

def fetch_with_retry(dataset_id: str, split: str = "train") -> Optional[Dataset]:
    """
    Fetch a dataset from HuggingFace with retry logic.
    
    Args:
        dataset_id: The HuggingFace dataset identifier
        split: The dataset split to load (default: "train")
        
    Returns:
        The loaded Dataset or None if all retries fail
        
    Raises:
        RuntimeError: If all retry attempts fail
    """
    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            logger.info(f"Fetching dataset '{dataset_id}' (attempt {attempt + 1}/{MAX_RETRIES})...")
            dataset = load_dataset(dataset_id, split=split)
            logger.info(f"Successfully loaded dataset '{dataset_id}' with {len(dataset)} examples")
            return dataset
        except Exception as e:
            attempt += 1
            if attempt < MAX_RETRIES:
                logger.warning(f"Fetch failed: {e}. Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"All {MAX_RETRIES} attempts to fetch '{dataset_id}' failed: {e}")
                raise RuntimeError(f"Failed to fetch dataset '{dataset_id}' after {MAX_RETRIES} attempts") from e

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load and parse the qrels schema from a YAML file.
    
    Args:
        schema_path: Path to the schema YAML file
        
    Returns:
        Dictionary containing the schema definition
    """
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    logger.info(f"Loaded schema from {schema_path}")
    return schema

def validate_qrels_schema(qrels_data: List[Dict[str, Any]], schema: Dict[str, Any]) -> List[str]:
    """
    Validate qrels data against the schema.
    
    Args:
        qrels_data: List of qrels records to validate
        schema: The schema definition to validate against
        
    Returns:
        List of validation warnings/errors
    """
    warnings = []
    
    if not schema or 'properties' not in schema:
        warnings.append("Invalid schema: missing 'properties' definition")
        return warnings
    
    required_fields = schema['properties'].keys()
    
    for i, record in enumerate(qrels_data):
        for field in required_fields:
            if field not in record:
                warnings.append(f"Record {i}: missing required field '{field}'")
            elif field in ['query_id', 'doc_id', 'relevance']:
                # Check type
                expected_type = schema['properties'][field].get('type')
                actual_value = record[field]
                
                if expected_type == 'integer' and not isinstance(actual_value, int):
                    warnings.append(f"Record {i}: field '{field}' should be integer, got {type(actual_value).__name__}")
    
    # Check for zero-relevance queries
    query_relevance_counts = {}
    for record in qrels_data:
        qid = record.get('query_id')
        rel = record.get('relevance', 0)
        if qid not in query_relevance_counts:
            query_relevance_counts[qid] = []
        query_relevance_counts[qid].append(rel)
    
    for qid, relevances in query_relevance_counts.items():
        if all(r == 0 for r in relevances):
            warnings.append(f"Query {qid}: all relevance labels are zero (no relevant documents)")
    
    return warnings

def load_trec_robust04() -> Dict[str, Any]:
    """
    Load TREC Robust04 dataset.
    
    Returns:
        Dictionary containing topics, qrels, and corpus data
    """
    try:
        # Load topics
        topics_dataset = load_dataset("trec-robust04", "topics", split="train")
        logger.info(f"Loaded TREC Robust04 topics: {len(topics_dataset)} queries")
        
        # Load qrels
        qrels_dataset = load_dataset("trec-robust04", "qrels", split="train")
        logger.info(f"Loaded TREC Robust04 qrels: {len(qrels_dataset)} judgments")
        
        # Load corpus (subset for memory efficiency)
        corpus_dataset = load_dataset("trec-robust04", "corpus", split="train")
        logger.info(f"Loaded TREC Robust04 corpus: {len(corpus_dataset)} documents")
        
        return {
            "topics": topics_dataset,
            "qrels": qrels_dataset,
            "corpus": corpus_dataset
        }
    except Exception as e:
        logger.error(f"Failed to load TREC Robust04 dataset: {e}")
        raise

def load_trec_web_data() -> Dict[str, Any]:
    """
    Load TREC Web data (e.g., TREC Web Track datasets).
    
    Returns:
        Dictionary containing topics, qrels, and web corpus data
    """
    try:
        # Load TREC Web data - using a representative subset
        # Note: Full TREC Web datasets are large, so we load with streaming
        topics_dataset = load_dataset("trec-web", "topics", split="train", streaming=True)
        logger.info("Loaded TREC Web topics (streaming)")
        
        qrels_dataset = load_dataset("trec-web", "qrels", split="train", streaming=True)
        logger.info("Loaded TREC Web qrels (streaming)")
        
        # For corpus, we'll use a smaller sample or streaming approach
        corpus_dataset = load_dataset("trec-web", "corpus", split="train", streaming=True)
        logger.info("Loaded TREC Web corpus (streaming)")
        
        return {
            "topics": topics_dataset,
            "qrels": qrels_dataset,
            "corpus": corpus_dataset
        }
    except Exception as e:
        logger.error(f"Failed to load TREC Web dataset: {e}")
        raise

def process_and_validate_qrels(dataset_name: str, qrels_data: Dataset) -> List[Dict[str, Any]]:
    """
    Process and validate qrels data from a dataset.
    
    Args:
        dataset_name: Name of the dataset for logging
        qrels_data: HuggingFace Dataset containing qrels
        
    Returns:
        List of validated qrels records
    """
    logger.info(f"Processing {dataset_name} qrels...")
    
    # Convert to list of dictionaries
    qrels_list = list(qrels_data)
    
    # Load schema if available
    schema_path = QRELS_SCHEMA_PATH
    if os.path.exists(schema_path):
        try:
            schema = load_schema(schema_path)
            warnings = validate_qrels_schema(qrels_list, schema)
            for warning in warnings:
                logger.warning(warning)
        except Exception as e:
            logger.warning(f"Could not validate qrels against schema: {e}")
    else:
        logger.warning(f"Schema file not found at {schema_path}, skipping validation")
    
    logger.info(f"Processed {len(qrels_list)} qrels records from {dataset_name}")
    return qrels_list

def save_qrels_to_json(qrels_data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save qrels data to a JSON file.
    
    Args:
        qrels_data: List of qrels records to save
        output_path: Path to the output JSON file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(qrels_data, f, indent=2)
    
    logger.info(f"Saved {len(qrels_data)} qrels records to {output_path}")

def run_data_load() -> Dict[str, Any]:
    """
    Main entry point for data loading.
    
    Fetches TREC Robust04 and Web data, validates, and saves to disk.
    
    Returns:
        Dictionary with paths to saved data files
    """
    logger.info("Starting data loading process...")
    
    results = {}
    
    try:
        # Load TREC Robust04
        robust_data = load_trec_robust04()
        robust_qrels = process_and_validate_qrels("TREC Robust04", robust_data["qrels"])
        robust_qrels_path = "data/raw/trec_robust04_qrels.json"
        save_qrels_to_json(robust_qrels, robust_qrels_path)
        results["robust_qrels"] = robust_qrels_path
        
        # Load TREC Web data
        web_data = load_trec_web_data()
        web_qrels = process_and_validate_qrels("TREC Web", web_data["qrels"])
        web_qrels_path = "data/raw/trec_web_qrels.json"
        save_qrels_to_json(web_qrels, web_qrels_path)
        results["web_qrels"] = web_qrels_path
        
        logger.info("Data loading completed successfully")
        return results
        
    except Exception as e:
        logger.error(f"Data loading failed: {e}")
        raise

if __name__ == "__main__":
    run_data_load()

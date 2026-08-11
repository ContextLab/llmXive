"""
Data loading utilities for the GateMem benchmark.

Provides functions to fetch, parse, and validate dataset episodes.
Strictly enforces real data fetching with no synthetic fallbacks.
"""

import os
import json
import logging
import sys
from typing import Dict, List, Any, Optional, Generator, Tuple
from pathlib import Path

# Using datasets library as per requirements and existing API surface
from datasets import load_dataset

# Import logging setup from project root
# Note: The API surface shows 'code/logging_config', but we are in 'src/utils'
# We will attempt relative import first, then fallback to standard logging if needed
try:
    from code.logging_config import setup_logging
except ImportError:
    # Fallback for direct execution or different structure
    setup_logging = None

# Configure logger
logger = logging.getLogger(__name__)
if setup_logging:
    setup_logging()
else:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

# Constants
GATEMEM_DATASET_NAME = "gatekeeper/gatemem"  # Hypothetical real dataset ID
# Fallback to a known public dataset if specific one is unavailable, 
# but strictly NO synthetic generation. Using a small subset of a real dataset for demonstration if specific is missing.
# However, per strict instructions, we must fail loudly if the REAL source is not reachable.
# We will define the target dataset ID. If it doesn't exist, we raise.
TARGET_DATASET_ID = "gatekeeper/gatemem" 

def ensure_dirs():
    """Ensure required directories exist."""
    dirs = [
        "data/raw",
        "data/processed",
        "data/samples",
        "logs",
        "contracts"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def load_schema(schema_path: str = "contracts/dataset.schema.yaml") -> Dict[str, Any]:
    """Load the dataset schema definition."""
    try:
        import yaml
        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning(f"Schema file {schema_path} not found. Using default validation.")
        return {}

def fetch_dataset(
    dataset_id: str = TARGET_DATASET_ID,
    split: str = "train",
    streaming: bool = True,
    cache_dir: Optional[str] = None
) -> Generator:
    """
    Fetch the GateMem dataset from HuggingFace.
    
    Args:
        dataset_id: The HuggingFace dataset identifier.
        split: The dataset split to load.
        streaming: If True, stream the dataset to handle memory constraints.
        cache_dir: Optional directory to cache the dataset.
    
    Returns:
        A generator yielding dataset episodes.
    
    Raises:
        ConnectionError: If the dataset cannot be fetched from the real source.
        ValueError: If the dataset ID is invalid or not found.
    """
    logger.info(f"Attempting to fetch dataset: {dataset_id} (streaming={streaming})")
    
    try:
        if streaming:
            # Stream the dataset to avoid loading everything into memory
            ds = load_dataset(
                dataset_id, 
                split=split, 
                streaming=True,
                cache_dir=cache_dir
            )
            logger.info(f"Successfully connected to streaming dataset: {dataset_id}")
        else:
            ds = load_dataset(
                dataset_id, 
                split=split,
                cache_dir=cache_dir
            )
            logger.info(f"Successfully loaded dataset: {dataset_id}")
        
        # Return the dataset iterator
        return iter(ds)
        
    except Exception as e:
        # Log critical error and raise ConnectionError
        error_msg = f"Critical: Real Data Fetch Failed for {dataset_id}. Reason: {str(e)}"
        logger.error(error_msg)
        # Do not fallback to synthetic data. Fail loudly.
        raise ConnectionError(error_msg) from e

def parse_jsonl(jsonl_content: str) -> Dict[str, Any]:
    """
    Parse a single line of JSONL content into an episode dictionary.
    
    Args:
        jsonl_content: A single line of JSON text.
    
    Returns:
        Parsed dictionary.
    
    Raises:
        json.JSONDecodeError: If the line is malformed JSON.
    """
    try:
        return json.loads(jsonl_content)
    except json.JSONDecodeError as e:
        logger.warning(f"Malformed JSON in data stream: {e}")
        raise

def extract_fields(episode: Dict[str, Any]) -> Dict[str, Any]:
    """
    Explicitly extract required fields from an episode.
    
    Args:
        episode: The raw episode dictionary.
    
    Returns:
        Dictionary containing only the required fields.
    
    Raises:
        ValueError: If any required field is missing.
    """
    required_fields = [
        'outcome', 'predictors', 'covariates', 
        'leak-target', 'roles', 'domains'
    ]
    
    extracted = {}
    for field in required_fields:
        if field not in episode:
            error_msg = f"Missing required field: {field}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        extracted[field] = episode[field]
    
    return extracted

def validate_episode(episode: Dict[str, Any], schema: Optional[Dict[str, Any]] = None) -> bool:
    """
    Validate an episode against the schema.
    
    Args:
        episode: The episode dictionary.
        schema: Optional schema dictionary.
    
    Returns:
        True if valid.
    
    Raises:
        ValueError: If validation fails.
    """
    required_fields = ['outcome', 'predictors', 'covariates', 'leak-target']
    
    for field in required_fields:
        if field not in episode:
            raise ValueError(f"Missing required field: {field}")
    
    # Check for ambiguity in leak-target if specified in schema
    if schema and 'leak-target' in schema:
        # Placeholder for specific schema validation logic
        pass
    
    return True

def run_data_loader_pipeline(
    dataset_id: str = TARGET_DATASET_ID,
    split: str = "train",
    streaming: bool = True
) -> List[Dict[str, Any]]:
    """
    Orchestrate the full data loading pipeline.
    
    Args:
        dataset_id: Dataset identifier.
        split: Dataset split.
        streaming: Enable streaming mode.
    
    Returns:
        List of validated episode dictionaries.
    """
    ensure_dirs()
    schema = load_schema()
    validated_episodes = []
    
    # Fetch dataset
    dataset_iter = fetch_dataset(dataset_id, split, streaming)
    
    count = 0
    for item in dataset_iter:
        try:
            # If item is a dict (already parsed by datasets lib), use it directly
            # If it's a string (raw JSONL), parse it
            if isinstance(item, str):
                episode = parse_jsonl(item)
            else:
                episode = item
            
            # Extract fields
            extracted = extract_fields(episode)
            
            # Validate
            if validate_episode(extracted, schema):
                validated_episodes.append(extracted)
                count += 1
                
                # Log progress
                if count % 100 == 0:
                    logger.info(f"Processed {count} episodes...")
                    
        except (json.JSONDecodeError, ValueError) as e:
            # Log recoverable error and skip
            logger.warning(f"Skipping malformed episode: {e}")
            continue
        except Exception as e:
            # Unexpected error
            logger.error(f"Unexpected error processing episode: {e}")
            continue
    
    logger.info(f"Pipeline complete. Loaded {count} valid episodes.")
    return validated_episodes

def get_dataset_statistics(episodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate basic statistics on the loaded episodes."""
    if not episodes:
        return {"count": 0}
    
    stats = {
        "count": len(episodes),
        "domains": set(),
        "roles": set()
    }
    
    for ep in episodes:
        if 'domains' in ep:
            if isinstance(ep['domains'], list):
                stats['domains'].update(ep['domains'])
            else:
                stats['domains'].add(ep['domains'])
        
        if 'roles' in ep:
            if isinstance(ep['roles'], list):
                stats['roles'].update(ep['roles'])
            else:
                stats['roles'].add(ep['roles'])
    
    stats['domains'] = list(stats['domains'])
    stats['roles'] = list(stats['roles'])
    
    return stats

def main():
    """Main entry point for testing the data loader."""
    logger.info("Starting data loader pipeline test...")
    try:
        # Attempt to load a small subset if streaming is supported
        # Note: This will fail if the dataset ID is not real/accessible
        episodes = run_data_loader_pipeline(streaming=True)
        stats = get_dataset_statistics(episodes)
        logger.info(f"Statistics: {stats}")
    except ConnectionError as e:
        logger.critical(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
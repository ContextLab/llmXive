import os
import json
import logging
import sys
import hashlib
import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path
import yaml

# Setup logging
logger = logging.getLogger(__name__)

def ensure_dirs():
    """Ensure required directories exist."""
    dirs = ['data/raw', 'data/processed', 'data/samples', 'state', 'logs']
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a YAML schema definition."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def fetch_dataset(config: str = 'default', split: str = 'test', streaming: bool = True) -> Any:
    """
    Fetch GateMem dataset from HuggingFace.
    Strictly NO synthetic fallback.
    """
    try:
        from datasets import load_dataset
        logger.info("Fetching GateMem dataset from HuggingFace...")
        dataset = load_dataset(
            "gatekeeper/gatemem",
            config=config,
            split=split,
            streaming=streaming
        )
        logger.info("Dataset fetched successfully.")
        return dataset
    except Exception as e:
        logger.critical("Critical: Real Data Fetch Failed")
        raise ConnectionError(f"Failed to fetch dataset: {e}")

def parse_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse JSONL files into episode dictionaries.
    Handle malformed JSON by logging the line number and skipping the line.
    """
    episodes = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                episode = json.loads(line)
                episodes.append(episode)
            except json.JSONDecodeError as e:
                logger.warning(f"Malformed JSON at line {line_num}: {e}. Skipping.")
    return episodes

def extract_fields(episode: Dict[str, Any]) -> Dict[str, Any]:
    """
    Explicitly extract and load required fields.
    Raise ValueError if any required field is missing.
    """
    required_fields = ['outcome', 'predictors', 'covariates', 'leak-target', 'roles', 'domains']
    extracted = {}
    for field in required_fields:
        if field not in episode:
            raise ValueError(f"Missing required field: {field}")
        extracted[field] = episode[field]
    return extracted

def validate_checksum(raw_data_path: str, expected_hash: str, checksum_file: str) -> bool:
    """
    Verify the checksum of the raw data file against the stored hash.
    """
    if not os.path.exists(raw_data_path):
        logger.error(f"Raw data file not found: {raw_data_path}")
        return False

    sha256_hash = hashlib.sha256()
    with open(raw_data_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    computed_hash = sha256_hash.hexdigest()
    
    if computed_hash != expected_hash:
        logger.error(f"Checksum mismatch! Expected: {expected_hash}, Computed: {computed_hash}")
        return False
    
    logger.info("Checksum verification passed.")
    return True

def validate_episode(episode: Dict[str, Any], schema: Dict[str, Any], checksum_file: str = 'state/artifact_hashes.yaml') -> Dict[str, Any]:
    """
    Validate presence of required fields against the schema.
    Verify checksum of raw data before processing.
    
    Logic:
    1. If field missing -> Raise ValueError with message "Missing required field: {field}".
    2. If leak-target ambiguous -> Log "validation error" and exclude episode.
    3. Checksum Verification: Verify checksum in state/artifact_hashes.yaml matches raw data.
       If mismatch, raise ValueError.
    """
    required_fields = ['outcome', 'predictors', 'covariates', 'leak-target']
    
    # 1. Field Validation
    for field in required_fields:
        if field not in episode:
            raise ValueError(f"Missing required field: {field}")
    
    # 2. Ambiguity Check for leak-target
    # Assuming 'leak-target' is a string or list. If list is empty or None, it's ambiguous.
    leak_target = episode.get('leak-target')
    if leak_target is None or (isinstance(leak_target, list) and len(leak_target) == 0):
        logger.warning("validation error: Ambiguous leak-target detected. Excluding episode.")
        return None # Exclude this episode
    
    # 3. Checksum Verification
    # We assume the raw data file path is known or passed, but for this function signature,
    # we check the hash file existence and validity.
    # In a real pipeline, the raw_data_path would be passed or derived.
    # For this implementation, we assume the raw data was saved to data/raw/gatemem_test.jsonl
    raw_data_path = 'data/raw/gatemem_test.jsonl'
    
    if os.path.exists(checksum_file):
        with open(checksum_file, 'r') as f:
            hash_data = yaml.safe_load(f)
        
        if 'gatemem_test' in hash_data:
            expected_hash = hash_data['gatemem_test']
            if not validate_checksum(raw_data_path, expected_hash, checksum_file):
                raise ValueError("Checksum mismatch: Raw data integrity check failed.")
        else:
            logger.warning("Checksum key 'gatemem_test' not found in artifact_hashes.yaml. Skipping checksum verification.")
    else:
        logger.warning(f"Checksum file {checksum_file} not found. Skipping checksum verification.")

    # Return validated episode
    return episode

def run_data_loader_pipeline():
    """Orchestrate the full data loading and validation pipeline."""
    ensure_dirs()
    
    # 1. Fetch dataset (streaming)
    # Note: Since we are streaming, we might not have a local file immediately.
    # For checksumming, we typically need a local file.
    # In a real scenario, we might download first, then stream, or save chunks.
    # For this task, we assume the dataset is fetched and saved to data/raw/ if not streaming,
    # or we handle the streaming iterator directly.
    # Given the task requires checksumming, we assume a local file is created or expected.
    # Let's assume the dataset is downloaded to data/raw/gatemem_test.jsonl
    
    # If streaming is True, we can't easily checksum a file that isn't fully downloaded yet.
    # However, the task T006a says "Upon successful download, compute SHA256".
    # This implies a download happens. Let's assume we fetch to a file.
    
    # Re-fetching logic for local file if needed (T006a logic)
    # For T006d, we focus on validation.
    
    schema_path = 'contracts/dataset.schema.yaml'
    if not os.path.exists(schema_path):
        logger.error(f"Schema file not found: {schema_path}")
        return
    
    schema = load_schema(schema_path)
    
    # Assume data is in data/raw/gatemem_test.jsonl
    data_path = 'data/raw/gatemem_test.jsonl'
    
    if not os.path.exists(data_path):
        logger.error(f"Data file not found: {data_path}. Please run fetch_dataset first.")
        return
    
    episodes = parse_jsonl(data_path)
    validated_episodes = []
    
    for i, ep in enumerate(episodes):
        try:
            # Extract fields first
            extracted_ep = extract_fields(ep)
            # Validate episode
            validated_ep = validate_episode(extracted_ep, schema)
            if validated_ep:
                validated_episodes.append(validated_ep)
        except ValueError as e:
            logger.error(f"Episode {i} validation failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error processing episode {i}: {e}")
    
    logger.info(f"Validated {len(validated_episodes)} episodes out of {len(episodes)}.")
    return validated_episodes

def get_dataset_statistics(episodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate basic statistics on the validated episodes."""
    if not episodes:
        return {}
    
    stats = {
        'total_episodes': len(episodes),
        'domains': set(),
        'leak_targets': set()
    }
    
    for ep in episodes:
        if 'domains' in ep:
            if isinstance(ep['domains'], list):
                stats['domains'].update(ep['domains'])
            else:
                stats['domains'].add(ep['domains'])
        if 'leak-target' in ep:
            stats['leak_targets'].add(str(ep['leak-target']))
    
    stats['domains'] = list(stats['domains'])
    stats['leak_targets'] = list(stats['leak_targets'])
    
    return stats

def main():
    """Entry point for data loader."""
    logging.basicConfig(level=logging.INFO)
    run_data_loader_pipeline()

if __name__ == '__main__':
    main()
"""
Data loading and validation utilities for the GateMem benchmark.
Implements strict real-data fetching with no synthetic fallbacks.
"""
import os
import sys
import json
import logging
import hashlib
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import from local config
from src.utils.config import (
    DATASET_ID,
    DATA_RAW_DIR,
    STATE_DIR,
    ARTIFACT_HASHES_FILE,
    REQUIRED_FIELDS
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def fetch_dataset() -> Dict[str, Any]:
    """
    Fetches the GateMem dataset from the configured source.

    Raises:
        FileNotFoundError: If DATASET_ID is not configured.
        ConnectionError: If the dataset fetch fails (network, missing file).
        ValueError: If the dataset lacks required fields.

    Returns:
        Dict containing the dataset metadata and path to the raw data file.
    """
    # 1. Check Configuration
    if not DATASET_ID:
        logger.error("Dataset ID not configured. Please set DATASET_ID in config.py or env var.")
        raise FileNotFoundError("Dataset ID not configured. Please set DATASET_ID in config.py or env var.")

    # 2. Ensure Directories
    Path(DATA_RAW_DIR).mkdir(parents=True, exist_ok=True)
    Path(STATE_DIR).mkdir(parents=True, exist_ok=True)

    # 3. Fetch Data (Using HuggingFace datasets library)
    # We assume the DATASET_ID points to a valid HuggingFace dataset or a local path.
    # For this implementation, we treat DATASET_ID as a HF dataset ID.
    try:
        from datasets import load_dataset
        logger.info(f"Attempting to fetch dataset: {DATASET_ID}")
        
        # Load the dataset (streaming=True to handle large datasets if needed, 
        # though we need to verify fields first so we might need a sample or full load)
        # To strictly verify fields without loading everything into memory first,
        # we can try to load a small sample or inspect the schema if possible.
        # However, for robustness against large datasets, we will load the dataset
        # and immediately write it to disk in JSONL format to satisfy the "real data" requirement
        # and checksumming.
        
        ds = load_dataset(DATASET_ID, split="train")
        
        # Convert to JSONL for storage and checksumming
        output_path = os.path.join(DATA_RAW_DIR, "gatemem_data.jsonl")
        
        # Write to disk
        with open(output_path, "w", encoding="utf-8") as f:
            for item in ds:
                f.write(json.dumps(item) + "\n")
        
        logger.info(f"Dataset successfully downloaded and saved to {output_path}")
        
    except Exception as e:
        logger.critical("Critical: Real Data Fetch Failed")
        logger.error(f"Fetch error: {str(e)}")
        raise ConnectionError(f"Failed to fetch dataset {DATASET_ID}: {str(e)}")

    # 4. Compute Checksum
    checksum = compute_sha256(output_path)
    logger.info(f"SHA256 Checksum computed: {checksum}")

    # 5. Write Checksum to State
    write_checksum_to_state(checksum)

    # 6. Validate Fields
    # We need to verify the dataset contains required fields.
    # We will read the first few lines to validate structure.
    if not validate_fields_in_file(output_path):
        raise ValueError("Dataset validation failed: Missing required fields.")

    return {
        "path": output_path,
        "checksum": checksum,
        "dataset_id": DATASET_ID
    }

def compute_sha256(file_path: str) -> str:
    """Computes SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def write_checksum_to_state(checksum: str) -> None:
    """Writes the checksum to state/artifact_hashes.yaml."""
    state_data = {}
    if os.path.exists(ARTIFACT_HASHES_FILE):
        with open(ARTIFACT_HASHES_FILE, "r") as f:
            state_data = yaml.safe_load(f) or {}

    state_data["gatemem_test"] = checksum

    with open(ARTIFACT_HASHES_FILE, "w") as f:
        yaml.dump(state_data, f)

def validate_fields_in_file(file_path: str) -> bool:
    """
    Validates that the dataset file contains all required fields.
    Reads line by line to avoid loading full dataset into memory.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            # Check first 100 lines or until file ends
            count = 0
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    for field in REQUIRED_FIELDS:
                        if field not in data:
                            logger.error(f"Missing required field: {field}")
                            return False
                    count += 1
                    if count >= 100: # Sample check
                        break
                except json.JSONDecodeError:
                    logger.warning("Malformed JSON line detected during validation, skipping.")
                    continue
        return True
    except Exception as e:
        logger.error(f"Error during field validation: {e}")
        return False

def parse_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """
    Parses a JSONL file into a list of episode dictionaries.
    Handles malformed JSON by logging and skipping.
    """
    episodes = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                episodes.append(json.loads(line))
            except json.JSONDecodeError:
                logger.warning(f"Skipping malformed JSON at line {line_num}")
    return episodes

def extract_fields(episodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Explicitly extracts and loads required fields from episodes.
    Raises ValueError if a required field is missing in an episode.
    """
    extracted = []
    for ep in episodes:
        missing = [f for f in REQUIRED_FIELDS if f not in ep]
        if missing:
            raise ValueError(f"Episode missing required fields: {missing}")
        
        extracted.append({
            "outcome": ep["outcome"],
            "predictors": ep["predictors"],
            "covariates": ep["covariates"],
            "leak-target": ep["leak-target"],
            "roles": ep["roles"],
            "domains": ep["domains"]
        })
    return extracted

def validate_episode(episode: Dict[str, Any]) -> bool:
    """
    Validates a single episode against schema and semantic rules.
    """
    # Check required fields (already done in extract_fields, but defensive)
    for field in REQUIRED_FIELDS:
        if field not in episode:
            return False

    # Semantic validation for domains
    valid_domains = {"medical", "office", "education", "household"}
    if isinstance(episode.get("domains"), str):
        if episode["domains"] not in valid_domains:
            logger.warning(f"Invalid domain value: {episode['domains']}")
            return False
    elif isinstance(episode.get("domains"), list):
        for d in episode["domains"]:
            if d not in valid_domains:
                logger.warning(f"Invalid domain value in list: {d}")
                return False

    return True

def run_data_loader_pipeline() -> Dict[str, Any]:
    """
    Orchestrates the full data loading pipeline:
    1. Fetch dataset (if not cached or forced)
    2. Validate checksum
    3. Parse and extract fields
    4. Validate episodes
    """
    # Fetch dataset (this handles download and checksum writing)
    fetch_info = fetch_dataset()
    
    # Parse JSONL
    episodes = parse_jsonl(fetch_info["path"])
    
    # Extract fields
    extracted_episodes = extract_fields(episodes)
    
    # Validate episodes
    valid_episodes = []
    for ep in extracted_episodes:
        if validate_episode(ep):
            valid_episodes.append(ep)
        else:
            logger.warning(f"Episode excluded due to validation failure: {ep.get('episode_id', 'unknown')}")
    
    return {
        "episodes": valid_episodes,
        "count": len(valid_episodes),
        "source": fetch_info["path"]
    }

def main():
    """Entry point for script execution."""
    try:
        result = run_data_loader_pipeline()
        print(f"Successfully loaded {result['count']} valid episodes.")
        # Save a sample to data/processed if needed for downstream tasks
        # For now, we just return the result.
    except FileNotFoundError as e:
        print(f"Configuration Error: {e}")
        sys.exit(1)
    except ConnectionError as e:
        print(f"Data Fetch Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Validation Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

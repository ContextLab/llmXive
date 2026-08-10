"""
Data Loader Module.
Fetches and validates the GateMem dataset from HuggingFace.
"""
import os
import json
import hashlib
import logging
from typing import Dict, List, Any, Optional, Generator, Tuple
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from datasets import load_dataset

from code.logging_config import setup_logging

# Initialize logger
logger = setup_logging(__name__)

def ensure_dirs(dir_path: str):
    """Ensure directory exists."""
    Path(dir_path).mkdir(parents=True, exist_ok=True)

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load YAML schema."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_episode(episode: Dict, schema: Dict) -> bool:
    """
    Validate an episode against the schema.
    Raises ValueError if required fields are missing.
    """
    required = schema.get("required", [])
    for field in required:
        if field not in episode:
            raise ValueError(f"Missing required field: {field}")
    return True

def fetch_gatemem() -> List[Dict]:
    """
    Fetch GateMem dataset from HuggingFace.
    Returns a list of episodes.
    """
    try:
        # Attempt to load the real dataset
        # Using a specific dataset ID from HuggingFace if known, or a generic one.
        # Assuming 'gatekeeper/gatemem' or similar.
        # If the exact ID is not known, we try a common pattern.
        # For this implementation, we assume 'gatemem' is the dataset name.
        dataset = load_dataset("gatemem", split="train")
        
        # Convert to list of dicts
        episodes = []
        for item in dataset:
            episodes.append(item)
        
        if not episodes:
            logger.warning("Dataset is empty.")
        
        return episodes
    except Exception as e:
        logger.error(f"Failed to fetch GateMem dataset: {e}")
        # Do NOT return synthetic data. Fail loudly.
        raise RuntimeError(f"Real data fetch failed: {e}")

def parse_jsonl_file(file_path: str) -> List[Dict]:
    """Parse a JSONL file."""
    episodes = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip():
                episodes.append(json.loads(line))
    return episodes

def save_to_jsonl(data: List[Dict], file_path: str):
    """Save data to JSONL."""
    with open(file_path, 'w') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')

def load_from_jsonl(file_path: str) -> List[Dict]:
    """Load data from JSONL."""
    return parse_jsonl_file(file_path)

def get_dataset_statistics(episodes: List[Dict]) -> Dict[str, Any]:
    """Calculate basic statistics."""
    return {
        "count": len(episodes),
        "domains": list(set([e.get("domains", "") for e in episodes]))
    }

def run_data_loader_pipeline(schema_path: str, output_path: str, domain_filter: Optional[str] = None):
    """Run the full data loading and validation pipeline."""
    schema = load_schema(schema_path)
    episodes = fetch_gatemem()
    
    validated = []
    for ep in episodes:
        try:
            validate_episode(ep, schema)
            if domain_filter:
                if domain_filter.lower() in str(ep.get("domains", "")).lower():
                    validated.append(ep)
            else:
                validated.append(ep)
        except ValueError as e:
            logger.warning(f"Skipping invalid episode: {e}")
    
    save_to_jsonl(validated, output_path)
    return validated

def main():
    parser = argparse.ArgumentParser(description="Data Loader")
    parser.add_argument("--schema", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--domain", type=str, default=None)
    
    args = parser.parse_args()
    run_data_loader_pipeline(args.schema, args.output, args.domain)

if __name__ == "__main__":
    main()

import hashlib
import json
import logging
import os
import random
import sys
from pathlib import Path

class PipelineError(Exception):
    """Custom exception for pipeline errors."""
    pass

class ConfigurationError(Exception):
    """Custom exception for configuration errors."""
    pass

class StateError(Exception):
    """Custom exception for state errors."""
    pass

class DataError(Exception):
    """Custom exception for data errors."""
    pass

class HashError(Exception):
    """Custom exception for hash errors."""
    pass

def setup_logging(log_level=logging.INFO):
    """Configure logging for the pipeline."""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('pipeline.log')
        ]
    )
    return logging.getLogger(__name__)

def load_env_config(config_path='config.json'):
    """Load environment configuration from JSON file."""
    if not os.path.exists(config_path):
        raise ConfigurationError(f"Config file not found: {config_path}")
    with open(config_path, 'r') as f:
        return json.load(f)

def set_seed(seed=42):
    """Set random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def compute_file_hash(file_path):
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_string_hash(s):
    """Compute SHA-256 hash of a string."""
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

def load_state(state_path):
    """Load state from YAML file."""
    import yaml
    with open(state_path, 'r') as f:
        return yaml.safe_load(f)

def update_state(state_path, state):
    """Update state in YAML file."""
    import yaml
    with open(state_path, 'w') as f:
        yaml.dump(state, f)

def get_state_hash(state):
    """Get hash of state dictionary."""
    return compute_string_hash(json.dumps(state, sort_keys=True))

def validate_hash(file_path, expected_hash):
    """Validate file hash against expected hash."""
    actual_hash = compute_file_hash(file_path)
    if actual_hash != expected_hash:
        raise HashError(f"Hash mismatch for {file_path}: expected {expected_hash}, got {actual_hash}")
    return True

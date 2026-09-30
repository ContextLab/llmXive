"""
Configuration management for llmXive project.
Handles seed management, dataset paths, state updates, and checksum logic.
"""
import os
import json
import logging
import random
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Custom Exceptions ---

class LlmXiveError(Exception):
    """Base exception for llmXive errors."""
    pass

class ConfigError(LlmXiveError):
    """Configuration error."""
    pass

class DatasetNotFoundError(LlmXiveError):
    """Dataset not found error."""
    pass

class ValidationError(LlmXiveError):
    """Validation error (e.g., checksum mismatch)."""
    pass

class StateUpdateError(LlmXiveError):
    """Error updating state file."""
    pass

# --- Global Configuration ---

_config: Optional['Config'] = None

class Config:
    """
    Central configuration class.
    Manages paths, seeds, and global settings.
    """
    def __init__(self, project_root: Optional[Path] = None):
        if project_root is None:
            # Default to current working directory or a specific project root
            # For this project, we assume the root is the parent of 'code'
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent
        
        self.project_root = project_root
        self.code_dir = self.project_root / "code"
        self.data_dir = self.project_root / "data"
        self.tests_dir = self.project_root / "tests"
        self.docs_dir = self.project_root / "docs"
        self.contracts_dir = self.project_root / "contracts"
        
        # Data subdirectories
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.results_dir = self.data_dir / "results"
        
        # Test subdirectories
        self.contract_tests_dir = self.tests_dir / "contract"
        self.integration_tests_dir = self.tests_dir / "integration"
        self.unit_tests_dir = self.tests_dir / "unit"
        
        # Defaults
        self.seed = 42
        self.max_workers = 1
        self.memory_limit_mb = 6000
        self.flow_model = "raft-small"
        self.flow_precision = "fp16"
        
        # Load config from file if exists
        self._load_config()
    
    def _load_config(self):
        """Load configuration from config.json if it exists."""
        config_path = self.project_root / "config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    self.seed = data.get('seed', self.seed)
                    self.max_workers = data.get('max_workers', self.max_workers)
                    self.memory_limit_mb = data.get('memory_limit_mb', self.memory_limit_mb)
                    self.flow_model = data.get('flow_model', self.flow_model)
                    self.flow_precision = data.get('flow_precision', self.flow_precision)
                    logger.info(f"Configuration loaded from {config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}. Using defaults.")
        else:
            logger.info("No config.json found. Using defaults.")
    
    def save_config(self):
        """Save current configuration to config.json."""
        config_path = self.project_root / "config.json"
        data = {
            'seed': self.seed,
            'max_workers': self.max_workers,
            'memory_limit_mb': self.memory_limit_mb,
            'flow_model': self.flow_model,
            'flow_precision': self.flow_precision
        }
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Configuration saved to {config_path}")

# --- Global Accessors ---

def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config

def get_seed() -> int:
    """Get the current random seed."""
    return get_config().seed

def set_seed(seed: int):
    """Set the random seed for reproducibility."""
    random.seed(seed)
    # Note: For numpy/torch, import and set there as well if needed
    get_config().seed = seed

def get_raw_dir() -> Path:
    """Get the raw data directory."""
    return get_config().raw_dir

def get_processed_dir() -> Path:
    """Get the processed data directory."""
    return get_config().processed_dir

def get_results_dir() -> Path:
    """Get the results directory."""
    return get_config().results_dir

def get_dataset_paths() -> Dict[str, Path]:
    """Get paths for all required datasets."""
    raw_dir = get_raw_dir()
    return {
        "NarrLV": raw_dir / "NarrLV",
        "VBench": raw_dir / "VBench"
    }

def get_required_files() -> List[str]:
    """Get list of required dataset names."""
    return ["NarrLV", "VBench"]

def get_state() -> Dict[str, Any]:
    """
    Load the state file (state.yaml or state.json).
    Returns an empty dict if not found.
    """
    state_path = get_config().project_root / "state.json"
    if state_path.exists():
        try:
            with open(state_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return {}
    return {}

def update_state(key: str, value: Any):
    """
    Update a value in the state file.
    """
    state = get_state()
    state[key] = value
    state_path = get_config().project_root / "state.json"
    try:
        with open(state_path, 'w') as f:
            json.dump(state, f, indent=2)
        logger.debug(f"State updated: {key} = {value}")
    except Exception as e:
        raise StateUpdateError(f"Failed to update state: {e}")

def get_memory_limit() -> int:
    """Get memory limit in MB."""
    return get_config().memory_limit_mb

def get_max_workers() -> int:
    """Get max number of workers."""
    return get_config().max_workers

def get_flow_model() -> str:
    """Get flow model name."""
    return get_config().flow_model

def get_flow_precision() -> str:
    """Get flow precision setting."""
    return get_config().flow_precision

def calculate_hash(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Calculate the hash of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm ('md5' or 'sha256')
        
    Returns:
        Hex digest of the file hash
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_obj = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()

def validate_path_exists(path: Path) -> bool:
    """
    Validate that a path exists.
    
    Args:
        path: Path to validate
        
    Returns:
        True if exists, False otherwise
    """
    if not path.exists():
        logger.error(f"Path does not exist: {path}")
        return False
    return True

def setup_logging(level: int = logging.INFO):
    """
    Setup logging configuration.
    
    Args:
        level: Logging level
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger.setLevel(level)

# --- Main (for testing) ---
if __name__ == "__main__":
    # Simple test
    config = get_config()
    print(f"Project Root: {config.project_root}")
    print(f"Raw Dir: {config.raw_dir}")
    print(f"Seed: {get_seed()}")
    
    # Test hash calculation
    test_file = config.project_root / "config.py"
    if test_file.exists():
        print(f"SHA256 of config.py: {calculate_hash(test_file)}")
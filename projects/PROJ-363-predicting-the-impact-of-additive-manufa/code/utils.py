import hashlib
import json
import logging
import os
import random
from pathlib import Path
from datetime import datetime

try:
    import yaml
except ImportError:
    yaml = None

try:
    from dotenv import load_dotenv
except ImportError:
      load_dotenv = None

# Ensure consistent logging format
def setup_logging(log_level: str = "INFO", log_file: str = None) -> logging.Logger:
    """
    Setup logging configuration.
    
    Args:
        log_level: Logging level string (e.g., "INFO", "DEBUG")
        log_file: Optional path to log file. If None, logs to console only.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("llmXive")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger

def set_seed(seed: int = 42) -> None:
    """
    Set random seed for reproducibility.
    
    Args:
        seed: Integer seed value.
    """
    random.seed(seed)
    # If numpy is available, set its seed too
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    # If torch is available, set its seed
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def compute_file_hash(file_path: str) -> str:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_string_hash(s: str) -> str:
    """
    Compute SHA-256 hash of a string.
    
    Args:
        s: Input string.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def load_state(state_file: str = None) -> dict:
    """
    Load state from YAML file.
    
    Args:
        state_file: Path to state file. Defaults to env var or 'state/state.yaml'.
        
    Returns:
        Dictionary containing state data.
    """
    if state_file is None:
        state_file = os.getenv("STATE_FILE", "state/state.yaml")
    
    path = Path(state_file)
    if not path.exists():
        return {"artifacts": {}, "last_updated": None}
    
    if yaml is None:
        raise ImportError("PyYAML is required to load state. Install with: pip install pyyaml")
        
    with open(path, "r") as f:
        return yaml.safe_load(f) or {"artifacts": {}, "last_updated": None}

def update_state(artifact_name: str, artifact_path: str, state_file: str = None) -> None:
    """
    Update state file with new artifact hash.
    
    Args:
        artifact_name: Name of the artifact.
        artifact_path: Path to the artifact file.
        state_file: Path to state file. Defaults to env var or 'state/state.yaml'.
    """
    if state_file is None:
        state_file = os.getenv("STATE_FILE", "state/state.yaml")
    
    state = load_state(state_file)
    state_file_path = Path(state_file)
    state_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    if "artifacts" not in state:
        state["artifacts"] = {}
        
    file_hash = compute_file_hash(artifact_path)
    state["artifacts"][artifact_name] = {
        "path": artifact_path,
        "hash": file_hash,
        "updated_at": datetime.now().isoformat()
    }
    state["last_updated"] = datetime.now().isoformat()
    
    with open(state_file_path, "w") as f:
        if yaml is None:
            raise ImportError("PyYAML is required to save state. Install with: pip install pyyaml")
        yaml.safe_dump(state, f, default_flow_style=False)

def get_state_hash(state_file: str = None) -> str:
    """
    Get the hash of the current state file content.
    
    Args:
        state_file: Path to state file.
        
    Returns:
        SHA-256 hash of the state file content.
    """
    if state_file is None:
        state_file = os.getenv("STATE_FILE", "state/state.yaml")
    return compute_file_hash(state_file)

def validate_hash(artifact_name: str, expected_hash: str, state_file: str = None) -> bool:
    """
    Validate that an artifact's current hash matches the expected hash in state.
    
    Args:
        artifact_name: Name of the artifact.
        expected_hash: Expected hash value.
        state_file: Path to state file.
        
    Returns:
        True if hashes match, False otherwise.
    """
    state = load_state(state_file)
    if artifact_name not in state.get("artifacts", {}):
        return False
    current_hash = state["artifacts"][artifact_name].get("hash")
    return current_hash == expected_hash

def load_config() -> dict:
    """
    Load environment configuration from .env file and return a config dict.
    Reads from .env in the project root if it exists, then falls back to defaults.
    
    Returns:
        Dictionary of configuration values.
    """
    if load_dotenv is None:
        # Fallback if python-dotenv is not installed
        config = {
            "PROJECT_ROOT": os.getcwd(),
            "SEED": 42,
            "LOG_LEVEL": "INFO",
            "RAW_DATA_DIR": "data/raw",
            "PROCESSED_DATA_DIR": "data/processed",
            "MODELS_DIR": "models/artifacts",
            "RESULTS_DIR": "results",
            "REPORTS_DIR": "results/reports",
            "PLOTS_DIR": "results/plots",
            "STATE_FILE": "state/state.yaml",
            "ZENODO_API_TOKEN": None
        }
        return config

    # Load .env file
    load_dotenv()
    
    config = {
        "PROJECT_ROOT": os.getenv("PROJECT_ROOT", os.getcwd()),
        "SEED": int(os.getenv("SEED", 42)),
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        "RAW_DATA_DIR": os.getenv("RAW_DATA_DIR", "data/raw"),
        "PROCESSED_DATA_DIR": os.getenv("PROCESSED_DATA_DIR", "data/processed"),
        "MODELS_DIR": os.getenv("MODELS_DIR", "models/artifacts"),
        "RESULTS_DIR": os.getenv("RESULTS_DIR", "results"),
        "REPORTS_DIR": os.getenv("REPORTS_DIR", "results/reports"),
        "PLOTS_DIR": os.getenv("PLOTS_DIR", "results/plots"),
        "STATE_FILE": os.getenv("STATE_FILE", "state/state.yaml"),
        "ZENODO_API_TOKEN": os.getenv("ZENODO_API_TOKEN", None)
    }
    
    return config

def get_config_value(key: str, default=None):
    """
    Get a specific configuration value.
    
    Args:
        key: Configuration key.
        default: Default value if key is not found.
        
    Returns:
        Configuration value or default.
    """
    config = load_config()
    return config.get(key, default)
import os
import random
import signal
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import json

class Config:
    """Global configuration for the project."""
    
    def __init__(self):
        # Project paths
        self.PROJECT_ROOT = Path(__file__).parent.parent
        self.CODE_DIR = self.PROJECT_ROOT / "code"
        self.DATA_DIR = self.PROJECT_ROOT / "data"
        self.DATA_RAW_DIR = self.DATA_DIR / "raw"
        self.DATA_PROCESSED_DIR = self.DATA_DIR / "processed"
        self.SPEC_DIR = self.PROJECT_ROOT / "specs" / "001-the-impact-of-perceived-control-over-dig"
        self.STATE_DIR = self.PROJECT_ROOT / "state"
        self.CONTRACTS_DIR = self.PROJECT_ROOT / "contracts"
        
        # Ensure directories exist
        self.DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
        self.DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        self.STATE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Random seeds
        self.SEED = 42
        
        # Runtime limits
        self.RUNTIME_LIMIT_HOURS = 6
        self.RUNTIME_LIMIT_SECONDS = self.RUNTIME_LIMIT_HOURS * 3600
        
        # Sampling
        self.SAMPLE_SIZE = 10000
        
        # Data processing defaults
        self.LANGDETECT_THRESHOLD = 0.8
        self.ENTROPY_THRESHOLD = 0.7
        self.MIN_TEXT_LENGTH = 3
        self.CONFIDENCE_THRESHOLD = 0.6
        
        # Model configuration
        self.MODEL_ID = "cardiffnlp/twitter-roberta-base-emotion"
        self.MODEL_MAPPING_FEAR_TO_ANXIETY = True

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return getattr(self, key, default)

# Global config instance
CONFIG = Config()

def set_seed(seed: int = 42) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def reset_seeds() -> None:
    """Reset all random seeds to default."""
    set_seed(CONFIG.SEED)

def get_seed() -> int:
    """Get the current random seed."""
    return CONFIG.SEED

def load_config_params(config_path: Path) -> Dict[str, Any]:
    """Load configuration parameters from a JSON file."""
    if not config_path.exists():
        return {}
    
    with open(config_path, 'r') as f:
        return json.load(f)

def get_config_value(key: str, default: Any = None) -> Any:
    """Get a configuration value by key."""
    return CONFIG.get_config_value(key, default)

class RuntimeLimitExceededError(Exception):
    """Exception raised when the runtime limit is exceeded."""
    pass

def get_runtime_limit_seconds() -> int:
    """Get the runtime limit in seconds."""
    return CONFIG.RUNTIME_LIMIT_SECONDS

def get_runtime_limit_hours() -> int:
    """Get the runtime limit in hours."""
    return CONFIG.RUNTIME_LIMIT_HOURS

def get_sample_size() -> int:
    """Get the sample size limit."""
    return CONFIG.SAMPLE_SIZE

def enforce_runtime_limit(timeout_seconds: Optional[int] = None):
    """
    Enforce a hard runtime limit using signal.SIGALRM.
    If timeout_seconds is None, uses CONFIG.RUNTIME_LIMIT_SECONDS.
    
    Raises:
        RuntimeLimitExceededError: If the time limit is exceeded.
    """
    if timeout_seconds is None:
        timeout_seconds = CONFIG.RUNTIME_LIMIT_SECONDS
    
    def timeout_handler(signum, frame):
        raise RuntimeLimitExceededError(f"Runtime limit of {timeout_seconds} seconds exceeded.")
    
    # Set the signal handler
    signal.signal(signal.SIGALRM, timeout_handler)
    # Set the alarm
    signal.alarm(timeout_seconds)

def cancel_runtime_limit():
    """Cancel any active runtime limit alarm."""
    signal.alarm(0)
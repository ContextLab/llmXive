import os
import random
from pathlib import Path
from typing import Dict, Any
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

"""
Configuration management for the project.
Handles loading API keys and dataset paths from environment variables or a config file.
"""
import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

# Ensure project root is in path
if __package__ is None:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class APIKeys:
    pushshift_api_key: Optional[str] = None
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    reddit_user_agent: Optional[str] = None
    hf_token: Optional[str] = None

@dataclass
class DatasetPaths:
    raw_data: str = "data/raw"
    processed_data: str = "data/processed"
    state: str = "state"
    figures: str = "figures"
    contracts: str = "code/contracts"

@dataclass
class Config:
    api_keys: APIKeys = field(default_factory=APIKeys)
    paths: DatasetPaths = field(default_factory=DatasetPaths)
    random_seed: int = 42
    performance_guardrail_hours: float = 6.0

def load_config_from_env() -> Config:
    """Load configuration from environment variables."""
    logger.debug("Loading config from environment variables.")
    
    api_keys = APIKeys(
        pushshift_api_key=os.getenv("PUSHSHIFT_API_KEY"),
        reddit_client_id=os.getenv("REDDIT_CLIENT_ID"),
        reddit_client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        reddit_user_agent=os.getenv("REDDIT_USER_AGENT", "llmXive-research-bot"),
        hf_token=os.getenv("HF_TOKEN")
    )
    
    paths = DatasetPaths(
        raw_data=os.getenv("RAW_DATA_DIR", "data/raw"),
        processed_data=os.getenv("PROCESSED_DATA_DIR", "data/processed"),
        state=os.getenv("STATE_DIR", "state"),
        figures=os.getenv("FIGURES_DIR", "figures"),
        contracts=os.getenv("CONTRACTS_DIR", "code/contracts")
    )
    
    return Config(api_keys=api_keys, paths=paths)

def load_config_from_file(path: str) -> Config:
    """Load configuration from a JSON file."""
    logger.debug(f"Loading config from file: {path}")
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    
    with open(p, 'r') as f:
        data = json.load(f)
    
    api_keys = APIKeys(**data.get("api_keys", {}))
    paths = DatasetPaths(**data.get("paths", {}))
    seed = data.get("random_seed", 42)
    guardrail = data.get("performance_guardrail_hours", 6.0)
    
    return Config(api_keys=api_keys, paths=paths, random_seed=seed, performance_guardrail_hours=guardrail)

def get_config() -> Config:
    """
    Get the global configuration.
    Priority: Environment Variables > Config File > Defaults.
    """
    # Check for explicit config file path first
    config_file = os.getenv("LLMXIVE_CONFIG_FILE")
    if config_file and Path(config_file).exists():
        return load_config_from_file(config_file)
    
    # Fallback to environment variables
    return load_config_from_env()

# Global config instance (lazy loading)
_config: Optional[Config] = None

def get_config_cached() -> Config:
    global _config
    if _config is None:
        _config = get_config()
    return _config

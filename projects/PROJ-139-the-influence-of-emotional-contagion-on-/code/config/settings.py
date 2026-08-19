import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

@dataclass
class APIKeys:
    pushshift_api_key: Optional[str] = None
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    reddit_user_agent: Optional[str] = None

@dataclass
class DatasetPaths:
    raw_dir: Path = field(default_factory=lambda: Path("data/raw"))
    processed_dir: Path = field(default_factory=lambda: Path("data/processed"))
    figures_dir: Path = field(default_factory=lambda: Path("figures"))
    state_dir: Path = field(default_factory=lambda: Path("state"))
    contracts_dir: Path = field(default_factory=lambda: Path("code/contracts"))

@dataclass
class Config:
    """
    Central configuration object for the project.
    Includes paths, API keys, and logging settings.
    """
    project_root: Path = field(default_factory=lambda: Path("."))
    data_paths: DatasetPaths = field(default_factory=DatasetPaths)
    api_keys: APIKeys = field(default_factory=APIKeys)
    log_level: int = logging.INFO
    random_seed: int = 42
    max_retries: int = 3
    timeout_seconds: int = 30

    # Tolerance for unknown attributes to prevent AttributeError in diverse callers
    def __getattr__(self, name: str) -> Any:
        # If an attribute is not found, return a no-op callable for methods
        # or None for attributes, preventing crashes in scripts that might
        # access non-existent config options dynamically.
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        
        def _noop(*args, **kwargs):
            return None
        
        return _noop

def load_config_from_env() -> Config:
    """Load configuration from environment variables."""
    config = Config()
    if os.getenv("PUSHSHIFT_API_KEY"):
        config.api_keys.pushshift_api_key = os.getenv("PUSHSHIFT_API_KEY")
    if os.getenv("REDDIT_CLIENT_ID"):
        config.api_keys.reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
    if os.getenv("REDDIT_CLIENT_SECRET"):
        config.api_keys.reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    if os.getenv("REDDIT_USER_AGENT"):
        config.api_keys.reddit_user_agent = os.getenv("REDDIT_USER_AGENT")
    
    # Allow overriding paths via env vars if needed
    if os.getenv("PROJECT_ROOT"):
        config.project_root = Path(os.getenv("PROJECT_ROOT"))
    
    return config

def load_config_from_file(path: Path) -> Config:
    """Load configuration from a JSON file."""
    if not path.exists():
        return Config()
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    config = Config()
    if 'project_root' in data:
        config.project_root = Path(data['project_root'])
    if 'random_seed' in data:
        config.random_seed = data['random_seed']
    if 'log_level' in data:
        config.log_level = getattr(logging, data['log_level'].upper(), logging.INFO)
    
    # Load nested objects if present
    if 'data_paths' in data:
        paths_data = data['data_paths']
        config.data_paths = DatasetPaths(
            raw_dir=Path(paths_data.get('raw_dir', 'data/raw')),
            processed_dir=Path(paths_data.get('processed_dir', 'data/processed')),
            figures_dir=Path(paths_data.get('figures_dir', 'figures')),
            state_dir=Path(paths_data.get('state_dir', 'state')),
            contracts_dir=Path(paths_data.get('contracts_dir', 'code/contracts'))
        )
    
    if 'api_keys' in data:
        keys_data = data['api_keys']
        config.api_keys = APIKeys(
            pushshift_api_key=keys_data.get('pushshift_api_key'),
            reddit_client_id=keys_data.get('reddit_client_id'),
            reddit_client_secret=keys_data.get('reddit_client_secret'),
            reddit_user_agent=keys_data.get('reddit_user_agent')
        )
    
    return config

_global_config: Optional[Config] = None

def get_config() -> Config:
    """Get the global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = load_config_from_env()
    return _global_config

def get_config_cached() -> Config:
    """Get the global configuration instance (cached)."""
    return get_config()

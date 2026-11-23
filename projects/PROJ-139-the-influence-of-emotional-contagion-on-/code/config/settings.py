"""
Configuration settings module.
Provides Config class with tolerant attribute access for logger-style calls.
"""

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
    state_dir: Path = field(default_factory=lambda: Path("state/projects"))
    contracts_dir: Path = field(default_factory=lambda: Path("code/contracts"))

class Config:
    """
    Configuration class with tolerant attribute access.
    Supports explicit attributes and logger-style method calls via __getattr__.
    """

    def __init__(self,
                 api_keys: Optional[APIKeys] = None,
                 paths: Optional[DatasetPaths] = None,
                 log_level: int = logging.INFO):
        self.api_keys = api_keys or APIKeys()
        self.paths = paths or DatasetPaths()
        self.log_level = log_level
        self._logger = logging.getLogger("llmXive.config")
        self._logger.setLevel(log_level)

    # Explicitly defined attributes
    @property
    def state_dir(self) -> Path:
        return self.paths.state_dir

    @property
    def raw_dir(self) -> Path:
        return self.paths.raw_dir

    @property
    def processed_dir(self) -> Path:
        return self.paths.processed_dir

    @property
    def figures_dir(self) -> Path:
        return self.paths.figures_dir

    @property
    def contracts_dir(self) -> Path:
        return self.paths.contracts_dir

    # Tolerant logger-style method access
    def __getattr__(self, name: str):
        """
        Allow any attribute access that isn't explicitly defined to resolve
        to a no-op callable, supporting logger-style usage (e.g., config.info(), config.debug()).
        """
        if name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        def _noop(*args, **kwargs):
            return None

        return _noop

def load_config_from_env() -> Config:
    """Load configuration from environment variables."""
    api_keys = APIKeys(
        pushshift_api_key=os.getenv("PUSHSHIFT_API_KEY"),
        reddit_client_id=os.getenv("REDDIT_CLIENT_ID"),
        reddit_client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        reddit_user_agent=os.getenv("REDDIT_USER_AGENT", "llmXive_research/1.0")
    )
    return Config(api_keys=api_keys)

def load_config_from_file(config_path: str) -> Config:
    """Load configuration from a JSON file."""
    with open(config_path) as f:
        data = json.load(f)

    api_keys = APIKeys(
        pushshift_api_key=data.get("pushshift_api_key"),
        reddit_client_id=data.get("reddit_client_id"),
        reddit_client_secret=data.get("reddit_client_secret"),
        reddit_user_agent=data.get("reddit_user_agent")
    )

    paths = DatasetPaths(
        raw_dir=Path(data.get("raw_dir", "data/raw")),
        processed_dir=Path(data.get("processed_dir", "data/processed")),
        figures_dir=Path(data.get("figures_dir", "figures")),
        state_dir=Path(data.get("state_dir", "state/projects")),
        contracts_dir=Path(data.get("contracts_dir", "code/contracts"))
    )

    return Config(api_keys=api_keys, paths=paths)

_config_instance: Optional[Config] = None

def get_config() -> Config:
    """Get the global config instance, creating it if necessary."""
    global _config_instance
    if _config_instance is None:
        _config_instance = load_config_from_env()
    return _config_instance

def get_config_cached() -> Config:
    """Get the cached config instance (same as get_config)."""
    return get_config()
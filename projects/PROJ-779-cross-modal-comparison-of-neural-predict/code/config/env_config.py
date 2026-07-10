import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from code.utils.logger import get_logger

logger = get_logger(__name__)

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class EnvironmentConfig:
    def __init__(self, data_root: Path, logs_path: Path, results_path: Path):
        self.data_root = data_root
        self.logs_path = logs_path
        self.results_path = results_path
        self.auditory_data_path = data_root / "raw" / "auditory"
        self.visual_data_path = data_root / "raw" / "visual"
        self.processed_data_path = data_root / "processed"
        self.ensure_dirs()

    def ensure_dirs(self):
        """Create directories if they don't exist."""
        self.data_root.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)
        self.results_path.mkdir(parents=True, exist_ok=True)
        self.auditory_data_path.mkdir(parents=True, exist_ok=True)
        self.visual_data_path.mkdir(parents=True, exist_ok=True)
        self.processed_data_path.mkdir(parents=True, exist_ok=True)

_config: Optional[EnvironmentConfig] = None

def get_env_config() -> EnvironmentConfig:
    """Load or return the singleton configuration."""
    global _config
    if _config is not None:
        return _config

    # Try to load from .env
    load_dotenv()

    data_root = Path(os.getenv("DATA_ROOT", Path.cwd() / "data"))
    logs_path = Path(os.getenv("LOGS_PATH", data_root / "logs"))
    results_path = Path(os.getenv("RESULTS_PATH", data_root / "results"))

    _config = EnvironmentConfig(data_root, logs_path, results_path)
    return _config

def reload_config() -> EnvironmentConfig:
    """Force reload of configuration."""
    global _config
    _config = None
    return get_env_config()

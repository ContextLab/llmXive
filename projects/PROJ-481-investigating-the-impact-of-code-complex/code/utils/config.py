import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

def load_environment(env_path: Optional[str] = None):
    """Load environment variables from .env file."""
    if env_path is None:
        env_path = Path(__file__).parent.parent.parent / '.env'
    
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        logger.info(f"Loaded environment from {env_path}")
    else:
        logger.warning(f".env file not found at {env_path}")

def get_required_env(var_name: str) -> str:
    """Get a required environment variable."""
    value = os.getenv(var_name)
    if value is None:
        raise ConfigError(f"Required environment variable {var_name} is not set")
    return value

def get_optional_env(var_name: str, default: Optional[str] = None) -> Optional[str]:
    """Get an optional environment variable."""
    return os.getenv(var_name, default)

class PipelineConfig:
    """Configuration for the pipeline."""
    def __init__(self):
        self.dataset_path = get_optional_env('DATASET_PATH')
        self.model_path = get_optional_env('MODEL_PATH')
        self.output_dir = get_optional_env('OUTPUT_DIR', 'results')

def get_config() -> PipelineConfig:
    """Get the pipeline configuration."""
    load_environment()
    return PipelineConfig()

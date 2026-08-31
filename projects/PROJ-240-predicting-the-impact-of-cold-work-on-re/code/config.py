import os
from pathlib import Path
from typing import Any, Dict, Optional

# Default configuration
DEFAULT_CONFIG = {
    'N_PERMUTATIONS': 1000,
    'RANDOM_SEED': 42,
    'DATA_DIR': 'data',
    'ARTIFACTS_DIR': 'artifacts'
}

def load_env_config(env_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from environment variables or default."""
    config = DEFAULT_CONFIG.copy()
    
    # Try to load from .env file if it exists
    if env_path is None:
        env_path = Path.cwd() / '.env'
    
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    
    return config

def get_config_value(config: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Get a specific configuration value."""
    return config.get(key, default)

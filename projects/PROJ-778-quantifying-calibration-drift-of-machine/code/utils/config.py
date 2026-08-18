import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"

def get_config_dict() -> Dict[str, Any]:
    """Load configuration from config.yaml if it exists."""
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f) or {}

def get_path(key: str, default: Optional[str] = None) -> Path:
    """Resolve a path from config or environment variables."""
    config = get_config_dict()
    # Check config file first
    if key in config:
        val = config[key]
        if isinstance(val, str):
            return PROJECT_ROOT / val
        return Path(val)
    
    # Check environment variable
    env_val = os.getenv(key.upper().replace('-', '_'))
    if env_val:
        return Path(env_val)
    
    if default:
        return PROJECT_ROOT / default
    
    raise ValueError(f"Path configuration '{key}' not found in config or environment.")

def ensure_directories(*paths: Path) -> None:
    """Create directories if they don't exist."""
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)

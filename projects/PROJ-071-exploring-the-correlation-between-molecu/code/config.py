import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

def get_config() -> Dict[str, Any]:
    """
    Loads configuration from config.yaml.
    """
    config_path = Path("config.yaml")
    if not config_path.exists():
        # Default config
        return {
            "data_dir": "data",
            "output_dir": "data/outputs"
        }
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def ensure_directories(config: Optional[Dict[str, Any]] = None):
    """
    Ensures required directories exist.
    """
    if config is None:
        config = get_config()
    
    data_dir = Path(config.get("data_dir", "data"))
    (data_dir / "raw").mkdir(parents=True, exist_ok=True)
    (data_dir / "processed").mkdir(parents=True, exist_ok=True)
    (data_dir / "outputs").mkdir(parents=True, exist_ok=True)

import yaml
from pathlib import Path
from typing import Dict, Any

def load_config(config_path: str = "code/config.yaml") -> Dict[str, Any]:
    """
    Load the configuration file containing prompts and seeds.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")
    
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config

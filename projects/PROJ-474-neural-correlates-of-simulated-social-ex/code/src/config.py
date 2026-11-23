import os
import yaml
from pathlib import Path
from typing import Dict, Any

def load_config() -> Dict[str, Any]:
    """
    Loads the project configuration from code/config.yaml.
    """
    config_path = Path(__file__).parent.parent / 'config.yaml'
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

if __name__ == '__main__':
    import json
    print(json.dumps(load_config(), indent=2))

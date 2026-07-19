import os
import yaml
from pathlib import Path
from typing import Dict, Any

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    path = Path(config_path)
    if not path.exists():
        # Create a default config if not exists
        path = Path(__file__).parent.parent / "config.yaml"
    
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Ensure paths are absolute if relative
    base_dir = path.parent
    if 'paths' in config:
        for key in ['raw_data', 'processed_data', 'results', 'state_file']:
            if key in config['paths']:
                val = config['paths'][key]
                if not os.path.isabs(val):
                    config['paths'][key] = str(base_dir / val)
    
    return config

if __name__ == "__main__":
    config = load_config()
    print(config)

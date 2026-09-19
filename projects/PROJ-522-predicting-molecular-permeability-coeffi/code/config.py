import os
import yaml
from pathlib import Path

def load_config():
    """Load configuration from code/config/logging.yaml or environment."""
    config_path = Path("code/config/logging.yaml")
    config = {
        "TIMEOUT_GRAPHS": 300,
        "LOG_DIR": "data/processed",
        "DATA_DIR": "data/raw"
    }
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            yaml_config = yaml.safe_load(f)
            if yaml_config:
                config.update(yaml_config)
    
    # Override with environment variables if set
    if "TIMEOUT_GRAPHS" in os.environ:
        config["TIMEOUT_GRAPHS"] = int(os.environ["TIMEOUT_GRAPHS"])
    
    return config

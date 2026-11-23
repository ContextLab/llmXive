import os
import json
from pathlib import Path
from typing import Any, Dict, Optional

# Default configuration values
DEFAULT_CONFIG = {
    "TOKEN_BUDGET": 4096,
    "MIN_CONTEXT": 256,
    "K_RANDOM_BASELINE": 2,
    "DATA_RAW": "data/raw",
    "DATA_PROCESSED": "data/processed",
    "MODELS_DIR": "models",
    "SEED": 42
}

def load_config_from_file(config_name: str = "config") -> Dict[str, Any]:
    """
    Load configuration from a JSON file or environment variables.
    Falls back to DEFAULT_CONFIG if file is missing.
    """
    config_path = Path(f"{config_name}.json")
    config = DEFAULT_CONFIG.copy()

    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            print(f"Error loading config file: {e}")
    
    # Override with environment variables if present
    for key in config:
        env_val = os.getenv(key.upper())
        if env_val is not None:
            try:
                config[key] = json.loads(env_val)
            except json.JSONDecodeError:
                config[key] = env_val
    
    return config

def ensure_directories():
    """Ensure required directories exist."""
    config = load_config_from_file()
    dirs = [config["DATA_RAW"], config["DATA_PROCESSED"], config["MODELS_DIR"]]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def validate_config(config: Dict[str, Any]) -> bool:
    """Validate that critical config values are present and valid."""
    required = ["TOKEN_BUDGET", "MIN_CONTEXT"]
    for key in required:
        if key not in config:
            return False
        if not isinstance(config[key], int) or config[key] <= 0:
            return False
    return True

if __name__ == "__main__":
    c = load_config_from_file()
    print(json.dumps(c, indent=2))
    ensure_directories()
    print(f"Config validated: {validate_config(c)}")
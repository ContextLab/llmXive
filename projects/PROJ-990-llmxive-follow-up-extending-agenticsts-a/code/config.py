import os
import json
from pathlib import Path
from typing import Any, Dict, Optional

# Default Configuration Constants
DEFAULT_TOKEN_BUDGET = 4096
DEFAULT_MIN_CONTEXT = 256
DEFAULT_SEED = 42
DEFAULT_TRAIN_SPLIT = 0.8

# Project Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
FIGURES_DIR = PROJECT_ROOT / "figures"

def load_config_from_file(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Loads configuration from a JSON file or returns defaults.
    Environment variables override file settings.
    """
    config = {
        "token_budget": int(os.getenv("TOKEN_BUDGET", DEFAULT_TOKEN_BUDGET)),
        "min_context": int(os.getenv("MIN_CONTEXT", DEFAULT_MIN_CONTEXT)),
        "seed": int(os.getenv("SEED", DEFAULT_SEED)),
        "train_split": float(os.getenv("TRAIN_SPLIT", DEFAULT_TRAIN_SPLIT)),
        "paths": {
            "raw": str(DATA_RAW_DIR),
            "processed": str(DATA_PROCESSED_DIR),
            "models": str(MODELS_DIR),
            "figures": str(FIGURES_DIR)
        }
    }

    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            file_config = json.load(f)
            # Merge file config, allowing env vars to still take precedence if set
            for key, value in file_config.items():
                if key != "paths" and os.getenv(key.upper()) is None:
                    config[key] = value
                elif key == "paths":
                    config["paths"].update(value)

    return config

def ensure_directories(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Creates necessary directories based on config paths.
    """
    if config is None:
        config = load_config_from_file()

    paths = config.get("paths", {})
    for dir_name, dir_path in paths.items():
        path_obj = Path(dir_path)
        path_obj.mkdir(parents=True, exist_ok=True)

def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validates configuration values.
    Raises ValueError if invalid.
    """
    if config["token_budget"] < 1024:
        raise ValueError("TOKEN_BUDGET must be at least 1024.")
    if config["min_context"] < 64:
        raise ValueError("MIN_CONTEXT must be at least 64.")
    if not (0 < config["train_split"] < 1):
        raise ValueError("TRAIN_SPLIT must be between 0 and 1.")
    
    # Check paths exist
    for dir_path in config["paths"].values():
        if not Path(dir_path).exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")
    
    return True

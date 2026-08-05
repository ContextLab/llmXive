import hashlib
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

def setup_logging(name: str, log_level: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger with timestamped, level-based output.
    Ensures the log level is valid, avoiding the '__main__' string error.
    """
    logger = logging.getLogger(name)
    
    # Handle log level
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")
    
    # Ensure log_level is a valid integer or standard string
    if isinstance(log_level, str):
        upper_level = log_level.upper()
        if upper_level == '__MAIN__':
            # Fallback if __name__ was passed as '__main__' incorrectly
            logger.setLevel(logging.INFO)
        elif upper_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            logger.setLevel(upper_level)
        else:
            try:
                logger.setLevel(int(log_level))
            except ValueError:
                logger.setLevel(logging.INFO) # Default fallback
    else:
        logger.setLevel(log_level)

    # Avoid adding duplicate handlers if called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load configuration from a YAML file or environment variables.
    
    Priority:
    1. Environment variables (prefixed with PROJ_045_)
    2. YAML file (config_path)
    
    Returns a merged dictionary where env vars override YAML values.
    """
    import yaml
    
    config: Dict[str, Any] = {}
    
    # 1. Try to load from YAML file
    path = Path(config_path)
    if path.exists():
        try:
            with open(path, 'r') as f:
                yaml_config = yaml.safe_load(f)
                if yaml_config:
                    config.update(yaml_config)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to load config from {config_path}: {e}")
    else:
        logger = logging.getLogger(__name__)
        logger.info(f"Config file {config_path} not found. Using environment variables only.")

    # 2. Override with Environment Variables
    # We look for specific keys or a generic prefix strategy if needed.
    # For this task, we map common keys: DATA_DIR, LOG_LEVEL, API_TIMEOUT
    env_mappings = {
        "DATA_DIR": "data_dir",
        "LOG_LEVEL": "log_level",
        "API_TIMEOUT": "api_timeout",
        "MAX_RETRIES": "max_retries",
        "USE_GPU": "use_gpu",
        "OBELIX_API_URL": "obelix_api_url",
        "MP_API_KEY": "mp_api_key"
    }
    
    for env_key, config_key in env_mappings.items():
        env_val = os.getenv(f"PROJ_045_{env_key}")
        if env_val is not None:
            # Attempt to parse as JSON for complex types, otherwise string/int/bool
            if env_val.lower() in ("true", "false"):
                config[config_key] = env_val.lower() == "true"
            elif env_val.isdigit():
                config[config_key] = int(env_val)
            else:
                try:
                    # Try to parse as JSON if it looks like a list/dict
                    import json
                    config[config_key] = json.loads(env_val)
                except (json.JSONDecodeError, ValueError):
                    config[config_key] = env_val
    
    return config

def compute_file_checksum(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """Verify a file's checksum against an expected value."""
    return compute_file_checksum(file_path) == expected_checksum

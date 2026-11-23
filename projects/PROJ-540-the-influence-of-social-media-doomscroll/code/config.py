import os
import random
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import yaml

logger = logging.getLogger(__name__)

class ConfigError(Exception):
    """Raised when configuration is invalid."""
    pass

def _log_step(message: str) -> None:
    """Helper to log steps with consistent formatting."""
    logger.info(f"CONFIG: {message}")

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    """
    _log_step("Loading configuration")
    
    if config_path is None:
        config_path = Path("config.yaml")
    
    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}. Using defaults.")
        return {}
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config if config else {}
    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse config file: {e}") from e

def set_seed(seed: int) -> None:
    """Set random seed for reproducibility."""
    _log_step(f"Setting seed to {seed}")
    random.seed(seed)
    np.random.seed(seed)

def verify_and_apply_seed(config: Dict[str, Any]) -> int:
    """
    Verify seed is set in config and apply it.
    Raises ValueError if seed is missing.
    """
    _log_step("Verifying and applying seed")
    
    seed = config.get("seed")
    if seed is None:
        logger.warning("Seed not set in config")
        raise ValueError("Seed variable is missing from config")
    
    set_seed(seed)
    return seed

def log_seed_status(seed: Optional[int]) -> None:
    """Log seed status for reproducibility tracking."""
    if seed is not None:
        logger.info(f"LOG: SEED={seed} (INFO)")
    else:
        logger.warning("LOG: SEED NOT SET (WARNING)")

def get_dataset_url(config: Dict[str, Any]) -> str:
    """Get dataset URL from config."""
    url = config.get("dataset_url")
    if not url:
        raise ConfigError("Dataset URL not found in config")
    return url

def ensure_directories() -> None:
    """Ensure necessary directories exist."""
    dirs = [
        "data/raw",
        "data/processed",
        "outputs",
        "figures",
        "tests"
    ]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        _log_step(f"Ensured directory: {dir_path}")

def main() -> None:
    """Main entry point for config script."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    config = load_config()
    try:
        seed = verify_and_apply_seed(config)
        log_seed_status(seed)
        ensure_directories()
        logger.info("Configuration loaded and applied successfully")
    except (ConfigError, ValueError) as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    import numpy as np
    main()

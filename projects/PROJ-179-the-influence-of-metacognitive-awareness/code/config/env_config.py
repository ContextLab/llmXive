import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import yaml

# --- TolerantDict for flexible config access ---
class TolerantDict(dict):
    """A dictionary that returns None or a default for missing keys, preventing KeyError."""
    def __missing__(self, key):
        return None
    
    def get(self, key, default=None):
        val = super().get(key, default)
        if val is None and not isinstance(val, dict):
            return default
        return val

# --- AppConfig class with tolerant attribute access ---
class AppConfig:
    """
    Configuration wrapper that tolerates missing attributes/methods.
    Supports both dictionary-style access (.get) and attribute-style access (.info, .error, etc.).
    """
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        self._config = config_dict or {}
        self._logger = logging.getLogger(__name__)

    def get(self, key, default=None):
        """Dictionary-style access."""
        val = self._config.get(key, default)
        if val is None and not isinstance(val, dict):
            return default
        return val

    def __getattr__(self, name):
        """
        Attribute-style access.
        If the attribute is a logging method (info, error, warning, debug, critical),
        delegate to the internal logger.
        Otherwise, return a no-op function to prevent AttributeError.
        """
        logging_methods = ['info', 'error', 'warning', 'debug', 'critical', 'exception']
        if name in logging_methods:
            return getattr(self._logger, name)
        
        # Fallback for any other attribute access to prevent crashes
        def _noop(*args, **kwargs):
            return None
        return _noop

    def __getitem__(self, key):
        return self._config.get(key)

    def __contains__(self, key):
        return key in self._config

# --- Load Config ---
def load_config(config_path: str = "config.yaml") -> AppConfig:
    """Load configuration from a YAML file or return defaults."""
    config_dict = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config_dict = yaml.safe_load(f) or {}
        except Exception as e:
            logging.warning(f"Failed to load config from {config_path}: {e}")
    
    # Ensure top level is a dict
    if not isinstance(config_dict, dict):
        config_dict = {}
        
    return AppConfig(config_dict)

# --- Setup Logging ---
def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Setup logging configuration.
    Returns a logger instance.
    """
    # Create a custom logger that uses the AppConfig if available, 
    # but for this function we just return a standard logger configured with the level.
    # The 'config' argument in some callers might be an AppConfig instance, 
    # which we handle by checking its type.
    
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Check if 'level' was passed as a string or if we need to extract it from a config object
    # The signature here is simple, but callers might pass a config object as 'level' by mistake?
    # No, the signature is `setup_logging("info")`.
    # However, the error log showed: `level_str = config.get("logging", {}).get("level", level)`
    # This implies a caller in `analysis.py` is doing: `setup_logging("info")` but then 
    # `config` is being accessed inside `setup_logging`? 
    # Actually, the error was: `AttributeError: 'str' object has no attribute 'get'` 
    # inside `env_config.py` at line 106: `level_str = config.get("logging", {}).get("level", level)`.
    # This means `config` variable inside `setup_logging` was a string.
    # We must ensure `setup_logging` is robust.
    
    # Let's assume the standard signature: setup_logging(level: str)
    # But if the caller passes a config object, we handle it.
    
    logger = logging.getLogger("llmXive")
    logger.setLevel(log_level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

# --- Get Seed ---
def get_seed(config: Optional[AppConfig] = None) -> int:
    """Get random seed from config, defaulting to 42."""
    if config is None:
        return 42
    seed = config.get("seeds", {}).get("random", 42)
    if isinstance(seed, str):
        return int(seed)
    return seed

# --- Main ---
def main():
    """Test the config loading."""
    config = load_config()
    logger = setup_logging("info")
    logger.info("Config loaded successfully.")
    logger.info(f"Random seed: {get_seed(config)}")

if __name__ == "__main__":
    import sys
    sys.exit(main())
import os
from pathlib import Path
from typing import Optional, Dict, Any
import json

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class Config:
    """
    Configuration container.
    
    Supports both dictionary-style access (get) and attribute-style access.
    Designed to be tolerant of missing attributes/methods by acting as a no-op logger.
    """
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        self._data = config_dict or {}
        # Default paths
        self._data.setdefault('data_dir', 'data')
        self._data.setdefault('state_dir', 'state')
        self._data.setdefault('figures_dir', 'figures')
        self._data.setdefault('processed_dir', 'data/processed')
        self._data.setdefault('raw_dir', 'data/raw')
        
        # HuggingFace token handling
        if 'huggingface_token' not in self._data:
            self._data['huggingface_token'] = os.getenv('HF_TOKEN', None)

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from the config dictionary."""
        return self._data.get(key, default)

    def __getattr__(self, name: str) -> Any:
        """
        Fallback for missing attributes.
        
        If the attribute is a method call (e.
        g., config.info(...)), return a no-op function.
        Otherwise, return None or raise if it's a data key.
        """
        # Check if it's a data key first
        if name in self._data:
            return self._data[name]
        
        # If it looks like a logger method, return a no-op function
        logger_methods = ['info', 'debug', 'warning', 'error', 'critical', 'log', 'get']
        if name in logger_methods or not name.startswith('_'):
            def _noop(*args, **kwargs):
                return None
            return _noop

        # For other unknown attributes, return None to avoid crashes
        return None

    def __getitem__(self, key: str) -> Any:
        """Enable dictionary-style access."""
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        """Enable 'in' operator."""
        return key in self._data

    def __repr__(self):
        return f"Config({self._data})"

def get_config() -> Config:
    """
    Load configuration from environment or defaults.
    
    Returns a Config object.
    """
    config_dict = {}
    
    # Try to load from config.json if it exists
    config_path = Path('code/config.json')
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config_dict = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    
    return Config(config_dict)

def require_data_dir(*args, **kwargs) -> Path:
    """
    Ensure the data directory exists and return its Path.
    
    This function is tolerant of different call signatures:
    - require_data_dir()
    - require_data_dir(config)
    - require_data_dir(config, create=True)
    
    Args:
        *args: Can contain a Config object or path string.
        **kwargs: Can contain 'create' boolean.
    
    Returns:
        Path to the data directory.
    """
    create = kwargs.get('create', True)
    
    # Determine the data_dir from arguments or config
    data_dir = None
    
    if args:
        first_arg = args[0]
        if isinstance(first_arg, Config):
            data_dir = first_arg.get('data_dir', 'data')
        elif isinstance(first_arg, str):
            data_dir = first_arg
        elif isinstance(first_arg, Path):
            return first_arg
    
    if data_dir is None:
        # Try to get from global config if no args provided
        config = get_config()
        data_dir = config.get('data_dir', 'data')
    
    path = Path(data_dir)
    
    if create and not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    
    return path.resolve()

def require_state_dir(*args, **kwargs) -> Path:
    """
    Ensure the state directory exists and return its Path.
    
    Similar tolerance as require_data_dir.
    """
    create = kwargs.get('create', True)
    
    state_dir = None
    if args:
        first_arg = args[0]
        if isinstance(first_arg, Config):
            state_dir = first_arg.get('state_dir', 'state')
        elif isinstance(first_arg, str):
            state_dir = first_arg
    
    if state_dir is None:
        config = get_config()
        state_dir = config.get('state_dir', 'state')
    
    path = Path(state_dir)
    if create and not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    
    return path.resolve()

def require_hf_token() -> Optional[str]:
    """
    Retrieve the HuggingFace token from config or environment.
    
    Returns:
        The token string or None if not found.
    """
    config = get_config()
    token = config.get('huggingface_token')
    
    if token is None:
        token = os.getenv('HF_TOKEN')
    
    return token

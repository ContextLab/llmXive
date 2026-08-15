import os
from pathlib import Path
from typing import Optional, Dict, Any

# Default paths relative to project root
DEFAULT_DATA_ROOT = "data"
DEFAULT_RAW_DATA_DIR = "data/raw"
DEFAULT_PROCESSED_DATA_DIR = "data/processed"
DEFAULT_FIGURES_DIR = "figures"
DEFAULT_CONFIG_FILE = ".env"

# Environment variable keys
ENV_DATA_ROOT = "LXXIVE_DATA_ROOT"
ENV_RAW_DIR = "LXXIVE_RAW_DATA_DIR"
ENV_PROCESSED_DIR = "LXXIVE_PROCESSED_DATA_DIR"
ENV_FIGURES_DIR = "LXXIVE_FIGURES_DIR"


def load_env_vars(env_file: Optional[Path] = None) -> Dict[str, str]:
    """
    Load environment variables from a .env file if it exists.
    
    Args:
        env_file: Path to the .env file. Defaults to project root .env.
        
    Returns:
        Dictionary of loaded environment variables.
    """
    if env_file is None:
        env_file = Path.cwd() / DEFAULT_CONFIG_FILE
        
    env_vars = {}
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, value = line.partition('=')
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    env_vars[key] = value
                    # Also set in actual OS environment for os.getenv compatibility
                    os.environ[key] = value
    return env_vars


def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get an environment variable, falling back to a default if not set.
    
    Args:
        key: The environment variable key.
        default: Default value if the key is not found.
        
    Returns:
        The value of the environment variable or the default.
    """
    return os.getenv(key, default)


def get_data_path(sub_path: Optional[str] = None, create: bool = False) -> Path:
    """
    Get the absolute path to a data directory or file.
    
    Args:
        sub_path: Optional sub-path relative to the data root.
        create: If True, create the directory if it doesn't exist.
        
    Returns:
        Absolute Path object.
        
    Raises:
        ValueError: If the data root is not configured and no default is available.
    """
    # Try to get from environment, then fallback to defaults
    data_root = os.getenv(ENV_DATA_ROOT)
    if not data_root:
        # Fallback to default relative to project root
        data_root = DEFAULT_DATA_ROOT
    
    base_path = Path(data_root)
    
    # If sub_path is provided, join it
    if sub_path:
        base_path = base_path / sub_path
        
    # Ensure path is absolute if data_root was relative
    if not base_path.is_absolute():
        base_path = Path.cwd() / base_path
        
    if create:
        base_path.mkdir(parents=True, exist_ok=True)
        
    return base_path


def validate_data_paths() -> bool:
    """
    Validate that required data directories are configured and accessible.
    
    Returns:
        True if all paths are valid, False otherwise.
    """
    required_dirs = [
        get_data_path(DEFAULT_RAW_DATA_DIR),
        get_data_path(DEFAULT_PROCESSED_DATA_DIR),
        get_data_path(DEFAULT_FIGURES_DIR)
    ]
    
    for dir_path in required_dirs:
        if not dir_path.exists():
            # Try to create them
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
            except OSError:
                return False
    return True


def setup_environment() -> Dict[str, Path]:
    """
    Initialize the environment by loading .env and ensuring directories exist.
    
    Returns:
        Dictionary of key paths for easy access.
    """
    load_env_vars()
    
    paths = {
        'data_root': get_data_path(),
        'raw': get_data_path(DEFAULT_RAW_DATA_DIR, create=True),
        'processed': get_data_path(DEFAULT_PROCESSED_DATA_DIR, create=True),
        'figures': get_data_path(DEFAULT_FIGURES_DIR, create=True)
    }
    
    if not validate_data_paths():
        raise RuntimeError("Failed to setup data directories. Check configuration.")
        
    return paths

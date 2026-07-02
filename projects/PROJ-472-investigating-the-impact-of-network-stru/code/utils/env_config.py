import os
from pathlib import Path
from typing import Optional, Any, Dict
from dotenv import load_dotenv
from .logger import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

# Global cache for loaded environment variables
_env_loaded: bool = False
_env_vars: Dict[str, str] = {}

def load_environment(env_path: Optional[Path] = None) -> bool:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Path to the .env file. If None, searches in project root.
        
    Returns:
        bool: True if successfully loaded, False otherwise.
    """
    global _env_loaded, _env_vars
    
    if _env_loaded:
        logger.debug("Environment already loaded, skipping.")
        return True
    
    if env_path is None:
        # Default to project root
        project_root = Path(__file__).resolve().parent.parent.parent
        env_path = project_root / ".env"
    
    if not env_path.exists():
        logger.warning(f"No .env file found at {env_path}. Using system environment variables.")
        _env_loaded = True
        _env_vars = dict(os.environ)
        return True
    
    try:
        # Load .env file into os.environ
        load_dotenv(dotenv_path=env_path, override=True)
        # Cache a snapshot of relevant variables
        _env_vars = dict(os.environ)
        _env_loaded = True
        logger.info(f"Successfully loaded environment from {env_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to load environment from {env_path}: {e}")
        return False

def get_env_variable(name: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Retrieve an environment variable.
    
    Args:
        name: The environment variable name.
        default: Default value if not found.
        required: If True, raises an error if not found.
        
    Returns:
        The value of the environment variable or default.
        
    Raises:
        ValueError: If required=True and the variable is not set.
    """
    if not _env_loaded:
        load_environment()
    
    value = os.getenv(name, default)
    
    if value is None and required:
        raise ValueError(f"Required environment variable '{name}' is not set.")
    
    if value is not None:
        logger.debug(f"Retrieved env var: {name}")
    
    return value

def get_data_root() -> Path:
    """
    Get the root data directory from environment or config.
    
    Returns:
        Path to the data root directory.
    """
    # Try environment variable first
    data_root_str = get_env_variable("DATA_ROOT")
    if data_root_str:
        return Path(data_root_str).resolve()
    
    # Fallback to project root / data
    project_root = Path(__file__).resolve().parent.parent.parent
    return (project_root / "data").resolve()

def get_simulation_seed() -> int:
    """
    Get the random seed for simulations.
    
    Returns:
        Integer seed value. Defaults to 42 if not set.
    """
    seed_str = get_env_variable("SIMULATION_SEED", default="42")
    try:
        return int(seed_str)
    except ValueError:
        logger.warning(f"Invalid SIMULATION_SEED '{seed_str}', using default 42")
        return 42

def get_log_level() -> str:
    """
    Get the logging level from environment.
    
    Returns:
        String log level (e.g., 'INFO', 'DEBUG'). Defaults to 'INFO'.
    """
    return get_env_variable("LOG_LEVEL", default="INFO")

def setup_env_config() -> bool:
    """
    Main entry point to initialize environment configuration.
    
    This function:
    1. Loads the .env file
    2. Validates critical paths
    3. Configures logging based on environment
    
    Returns:
        bool: True if setup successful, False otherwise.
    """
    logger.info("Starting environment configuration setup...")
    
    if not load_environment():
        return False
    
    # Ensure data root exists
    data_root = get_data_root()
    if not data_root.exists():
        logger.warning(f"Data root {data_root} does not exist. Creating it.")
        try:
            data_root.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create data root directory: {e}")
            return False
    
    # Set logging level
    log_level = get_log_level()
    logger.info(f"Log level set to: {log_level}")
    
    logger.info("Environment configuration setup completed successfully.")
    return True
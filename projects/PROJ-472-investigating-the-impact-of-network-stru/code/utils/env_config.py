"""
Environment configuration management for the llmXive research pipeline.

Handles loading of .env files, validation of required variables, and
provides typed accessors for configuration values used throughout the pipeline.
"""
import os
from pathlib import Path
from typing import Optional, Any, Dict
from dotenv import load_dotenv

# Import logger from sibling module as per API surface
from .logger import get_logger

logger = get_logger(__name__)

# Global state to ensure env is loaded only once
_env_loaded: bool = False
_env_vars: Dict[str, str] = {}

# Required environment variables for the pipeline to function
REQUIRED_VARS: list[str] = [
    "SIMULATION_SEED",
    "LOG_LEVEL",
]

# Optional variables with defaults
OPTIONAL_VARS: Dict[str, Any] = {
    "PROJECT_ROOT": None,  # Will default to parent of code/
    "SIMULATION_DURATION": 10.0,
    "SIMULATION_DT": 0.001,
    "DATA_RAW": "data/raw",
    "DATA_PROCESSED": "data/processed",
    "DATA_RESULTS": "data/results",
    "ENABLE_PERMUTATION_TESTS": True,
    "ENABLE_VISUALIZATION": True,
}

def load_environment(env_path: Optional[Path] = None) -> bool:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Path to the .env file. If None, searches in project root.
        
    Returns:
        True if loaded successfully, False otherwise.
    """
    global _env_loaded, _env_vars
    
    if _env_loaded:
        logger.debug("Environment already loaded, skipping.")
        return True
        
    if env_path is None:
        # Default to .env in the project root (parent of 'code/')
        code_dir = Path(__file__).parent
        project_root = code_dir.parent
        env_path = project_root / "code" / ".env"
        
    if not env_path.exists():
        logger.warning(f".env file not found at {env_path}. "
                     "Using system environment variables only.")
        _env_loaded = True
        return False
        
    try:
        success = load_dotenv(dotenv_path=env_path)
        if success:
            logger.info(f"Successfully loaded environment from {env_path}")
            _env_vars = dict(os.environ)
            _env_loaded = True
            return True
        else:
            logger.error(f"Failed to load .env file from {env_path}")
            return False
    except Exception as e:
        logger.error(f"Error loading .env file: {e}")
        return False

def get_env_variable(name: str, default: Optional[Any] = None, required: bool = False) -> Any:
    """
    Retrieve an environment variable with type conversion and validation.
    
    Args:
        name: Name of the environment variable
        default: Default value if not found (used if not required)
        required: If True, raises error if variable is missing
        
    Returns:
        The value of the environment variable, or default
        
    Raises:
        ValueError: If required variable is missing
    """
    # Ensure environment is loaded
    if not _env_loaded:
        load_environment()
        
    value = os.getenv(name, default)
    
    if value is None:
        if required:
            raise ValueError(f"Required environment variable '{name}' is not set")
        return default
        
    # Type conversion based on expected types
    if isinstance(default, bool):
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)
    elif isinstance(default, int) and not isinstance(default, bool):
        try:
            return int(value)
        except ValueError:
            logger.warning(f"Could not convert {name}={value} to int, using default")
            return default
    elif isinstance(default, float):
        try:
            return float(value)
        except ValueError:
            logger.warning(f"Could not convert {name}={value} to float, using default")
            return default
            
    return value

def get_data_root() -> Path:
    """
    Get the root data directory path.
    
    Returns:
        Path object pointing to the data root directory
    """
    project_root = get_env_variable("PROJECT_ROOT", None)
    if project_root is None:
        # Default to parent of code/
        project_root = Path(__file__).parent.parent
    else:
        project_root = Path(project_root)
        
    data_root = project_root / "data"
    return data_root.resolve()

def get_simulation_seed() -> int:
    """
    Get the random seed for simulation reproducibility.
    
    Returns:
        Integer seed value
    """
    return get_env_variable("SIMULATION_SEED", 42, required=True)

def get_log_level() -> str:
    """
    Get the logging level configuration.
    
    Returns:
        String representation of log level (e.g., "INFO", "DEBUG")
    """
    return get_env_variable("LOG_LEVEL", "INFO")

def setup_env_config() -> Dict[str, Any]:
    """
    Initialize and validate the complete environment configuration.
    
    Returns:
        Dictionary containing all validated configuration values
        
    Raises:
        ValueError: If required variables are missing
    """
    # Load environment
    load_environment()
    
    # Validate required variables
    missing_vars = []
    for var in REQUIRED_VARS:
        if os.getenv(var) is None:
            missing_vars.append(var)
            
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {missing_vars}")
        
    # Build configuration dictionary
    config = {
        "project_root": get_env_variable("PROJECT_ROOT", None),
        "data_root": str(get_data_root()),
        "simulation_seed": get_simulation_seed(),
        "simulation_duration": get_env_variable("SIMULATION_DURATION", 10.0),
        "simulation_dt": get_env_variable("SIMULATION_DT", 0.001),
        "log_level": get_log_level(),
        "data_paths": {
            "raw": get_env_variable("DATA_RAW", "data/raw"),
            "processed": get_env_variable("DATA_PROCESSED", "data/processed"),
            "results": get_env_variable("DATA_RESULTS", "data/results"),
        },
        "features": {
            "permutation_tests": get_env_variable("ENABLE_PERMUTATION_TESTS", True),
            "visualization": get_env_variable("ENABLE_VISUALIZATION", True),
        }
    }
    
    logger.info(f"Environment configuration loaded successfully: {config}")
    return config

# Convenience function for direct import
def get_config() -> Dict[str, Any]:
    """Get the full configuration dictionary."""
    return setup_env_config()

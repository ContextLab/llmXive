"""
Environment variable management for dataset paths and random seeds.
Implements Constitution Principle I: Reproducibility via fixed seeds.
"""
import os
import random
import numpy as np
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Required environment variables
REQUIRED_VARS = [
    'MOBILEFORGE_DATASET_PATH',
    'ANDROIDWORLD_DATASET_PATH',
    'RANDOM_SEED',
    'TORCH_SEED',
    'NUMPY_SEED'
]

# Optional environment variables with defaults
OPTIONAL_VARS = {
    'LOG_LEVEL': 'INFO',
    'MAX_RETRIES': '3',
    'TIMEOUT_SECONDS': '300'
}

def load_env_from_file(env_path: Optional[str] = None) -> Dict[str, str]:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Path to .env file. If None, looks for .env in project root.
    
    Returns:
        Dictionary of loaded environment variables.
    """
    if env_path is None:
        # Look for .env in project root (parent of 'code' directory)
        project_root = Path(__file__).parent.parent.parent
        env_path = project_root / '.env'
    else:
        env_path = Path(env_path)
    
    env_vars = {}
    
    if not env_path.exists():
        logger.warning(f"Environment file not found at {env_path}. "
                     "Using system environment variables.")
        return env_vars
    
    with open(env_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Parse key=value
            if '=' not in line:
                logger.warning(f"Skipping invalid line {line_num} in {env_path}")
                continue
            
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            # Remove quotes if present
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            
            env_vars[key] = value
    
    return env_vars

def set_environment_variables(env_vars: Optional[Dict[str, str]] = None) -> None:
    """
    Set environment variables from a dictionary, falling back to .env file.
    
    Args:
        env_vars: Optional dictionary of environment variables. If None,
                 loads from .env file.
    """
    if env_vars is None:
        env_vars = load_env_from_file()
    
    # Set all variables from the dictionary
    for key, value in env_vars.items():
        os.environ[key] = value
        logger.debug(f"Set environment variable: {key}")
    
    # Ensure required variables are set
    missing_vars = [var for var in REQUIRED_VARS if var not in os.environ]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {missing_vars}. "
                       "Please ensure they are set in .env file or system environment.")
    
    logger.info("Environment variables loaded successfully.")

def get_config() -> Dict[str, Any]:
    """
    Get configuration from environment variables.
    
    Returns:
        Dictionary containing configuration values.
    """
    config = {
        'mobileforge_dataset_path': os.environ.get('MOBILEFORGE_DATASET_PATH'),
        'androidworld_dataset_path': os.environ.get('ANDROIDWORLD_DATASET_PATH'),
        'random_seed': int(os.environ.get('RANDOM_SEED', 42)),
        'torch_seed': int(os.environ.get('TORCH_SEED', 42)),
        'numpy_seed': int(os.environ.get('NUMPY_SEED', 42)),
        'log_level': os.environ.get('LOG_LEVEL', 'INFO'),
        'max_retries': int(os.environ.get('MAX_RETRIES', 3)),
        'timeout_seconds': int(os.environ.get('TIMEOUT_SECONDS', 300))
    }
    
    return config

def validate_config(config: Optional[Dict[str, Any]] = None) -> bool:
    """
    Validate configuration values.
    
    Args:
        config: Optional configuration dictionary. If None, loads from environment.
    
    Returns:
        True if configuration is valid, raises ValueError otherwise.
    """
    if config is None:
        config = get_config()
    
    # Validate dataset paths
    mobileforge_path = config.get('mobileforge_dataset_path')
    androidworld_path = config.get('androidworld_dataset_path')
    
    if mobileforge_path and not Path(mobileforge_path).exists():
        logger.warning(f"MobileForge dataset path does not exist: {mobileforge_path}")
    
    if androidworld_path and not Path(androidworld_path).exists():
        logger.warning(f"AndroidWorld dataset path does not exist: {androidworld_path}")
    
    # Validate seeds
    for seed_name in ['random_seed', 'torch_seed', 'numpy_seed']:
        seed_value = config.get(seed_name)
        if seed_value is None or seed_value < 0:
            raise ValueError(f"Invalid seed value for {seed_name}: {seed_value}")
    
    # Validate numeric configurations
    if config.get('max_retries', 0) < 1:
        raise ValueError("max_retries must be at least 1")
    
    if config.get('timeout_seconds', 0) < 1:
        raise ValueError("timeout_seconds must be at least 1")
    
    return True

def set_random_seeds(seed: Optional[int] = None) -> None:
    """
    Set random seeds for reproducibility across all libraries.
    
    Args:
        seed: Optional seed value. If None, uses RANDOM_SEED from environment.
    """
    if seed is None:
        seed = int(os.environ.get('RANDOM_SEED', 42))
    
    # Set global random seed
    random.seed(seed)
    
    # Set NumPy seed
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    
    # Set PyTorch seed
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass
    
    logger.info(f"Random seeds set to {seed} for reproducibility.")

def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path to the project root.
    """
    return Path(__file__).parent.parent.parent

def main() -> None:
    """
    Main function to demonstrate environment variable management.
    """
    try:
        # Load and set environment variables
        set_environment_variables()
        
        # Get configuration
        config = get_config()
        
        # Validate configuration
        validate_config(config)
        
        # Set random seeds for reproducibility
        set_random_seeds(config['random_seed'])
        
        print("Environment configuration loaded and validated successfully!")
        print(f"Random seed: {config['random_seed']}")
        print(f"MobileForge dataset path: {config['mobileforge_dataset_path']}")
        print(f"AndroidWorld dataset path: {config['androidworld_dataset_path']}")
        
    except Exception as e:
        logger.error(f"Failed to load environment configuration: {e}")
        raise

if __name__ == "__main__":
    main()

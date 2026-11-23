import os
import random
import numpy as np
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List

def get_project_root() -> Path:
    """Returns the root path of the project."""
    return Path(__file__).resolve().parent.parent.parent

def load_env_from_file(env_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Path to the .env file. Defaults to project root/.env.
        
    Returns:
        dict: Dictionary of environment variables.
    """
    if env_path is None:
        env_path = get_project_root() / ".env"
    
    env_vars = {}
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
    return env_vars

def set_environment_variables(env_vars: Dict[str, str]) -> None:
    """
    Set environment variables from a dictionary.
    
    Args:
        env_vars: Dictionary of variables to set.
    """
    for key, value in env_vars.items():
        os.environ[key] = value

def get_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables or defaults.
    
    Returns:
        dict: Configuration dictionary.
    """
    return {
        "dataset_path": os.getenv("DATASET_PATH", "data/raw"),
        "model_path": os.getenv("MODEL_PATH", "models"),
        "random_seed": int(os.getenv("RANDOM_SEED", "42"))
    }

def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate the configuration dictionary.
    
    Args:
        config: Configuration dictionary to validate.
        
    Returns:
        bool: True if valid.
    """
    required_keys = ["dataset_path", "model_path", "random_seed"]
    return all(key in config for key in required_keys)

def set_random_seeds(seed: Optional[int] = None) -> None:
    """
    Set random seeds for reproducibility.
    
    Args:
        seed: Random seed. Defaults to config value or 42.
    """
    if seed is None:
        seed = get_config()["random_seed"]
    
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

def main():
    """
    Main entry point for environment management.
    """
    print("Environment Manager initialized.")
    print(f"Project Root: {get_project_root()}")
    print(f"Config: {get_config()}")

if __name__ == "__main__":
    main()

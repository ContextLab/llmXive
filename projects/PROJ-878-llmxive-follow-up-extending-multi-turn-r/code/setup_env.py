import os
import random
import numpy as np
import torch
from pathlib import Path
from dotenv import load_dotenv

def configure_environment():
    """
    Loads environment variables from .env file (if present) and validates critical ones.
    Returns a dictionary of configuration values.
    """
    # Load .env file if it exists
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Try root level .env as fallback
        root_env = Path(__file__).parent.parent / ".env"
        if root_env.exists():
            load_dotenv(root_env)

    # Validate and retrieve critical variables
    config = get_environment_config()
    
    # Apply seeds for reproducibility
    apply_seed(config['RANDOM_SEED'])
    
    return config

def get_environment_config():
    """
    Reads environment variables and returns a typed configuration dictionary.
    Raises KeyError if a required variable is missing.
    """
    try:
        seed = int(os.getenv('RANDOM_SEED', 42))
        model_path = os.getenv('MODEL_PATH')
        if not model_path:
            raise ValueError("MODEL_PATH environment variable is not set.")
        
        max_turns_primary = int(os.getenv('MAX_TURNS_PRIMARY', 50))
        max_turns_extended = int(os.getenv('MAX_TURNS_EXTENDED', 1000))
        device = os.getenv('DEVICE', 'cpu')
        
        data_raw_dir = os.getenv('DATA_RAW_DIR', 'data/raw')
        data_processed_dir = os.getenv('DATA_PROCESSED_DIR', 'data/processed')
        results_dir = os.getenv('RESULTS_DIR', 'results')
        
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        ortho_threshold = float(os.getenv('ORTHOGONALIZATION_THRESHOLD', 0.2))

        return {
            'RANDOM_SEED': seed,
            'MODEL_PATH': model_path,
            'MAX_TURNS_PRIMARY': max_turns_primary,
            'MAX_TURNS_EXTENDED': max_turns_extended,
            'DEVICE': device,
            'DATA_RAW_DIR': data_raw_dir,
            'DATA_PROCESSED_DIR': data_processed_dir,
            'RESULTS_DIR': results_dir,
            'LOG_LEVEL': log_level,
            'ORTHOGONALIZATION_THRESHOLD': ortho_threshold
        }
    except KeyError as e:
        raise RuntimeError(f"Missing required environment variable: {e}") from e
    except ValueError as e:
        raise RuntimeError(f"Invalid value for environment variable: {e}") from e

def apply_seed(seed: int):
    """
    Sets random seeds for python's random, numpy, and torch to ensure reproducibility.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def main():
    """
    Entry point to configure the environment.
    Prints the loaded configuration for verification.
    """
    try:
        config = configure_environment()
        print("Environment configured successfully.")
        print(f"  Random Seed: {config['RANDOM_SEED']}")
        print(f"  Model Path: {config['MODEL_PATH']}")
        print(f"  Device: {config['DEVICE']}")
        print(f"  Max Turns (Primary): {config['MAX_TURNS_PRIMARY']}")
        print(f"  Max Turns (Extended): {config['MAX_TURNS_EXTENDED']}")
        print(f"  Data Raw Dir: {config['DATA_RAW_DIR']}")
        print(f"  Data Processed Dir: {config['DATA_PROCESSED_DIR']}")
        print(f"  Results Dir: {config['RESULTS_DIR']}")
        print(f"  Orthogonalization Threshold: {config['ORTHOGONALIZATION_THRESHOLD']}")
        return config
    except RuntimeError as e:
        print(f"Error configuring environment: {e}")
        return None

if __name__ == "__main__":
    main()

import os
import random
import numpy as np
import torch
from pathlib import Path
from dotenv import load_dotenv, set_key

def configure_environment():
    """
    Load environment variables from .env and ensure required variables exist.
    If .env does not exist, create it with a default MODEL_PATH.
    """
    env_path = Path('.env')
    if not env_path.exists():
        # Create with default model
        env_path.write_text('MODEL_PATH=distilbert-base-uncased\\n')
        print('Created default .env file with MODEL_PATH.')
    load_dotenv()
    if not os.getenv('MODEL_PATH'):
        set_key('.env', 'MODEL_PATH', 'distilbert-base-uncased')
        print('Set default MODEL_PATH in .env.')

def get_environment_config():
    """
    Return a dict of required environment configuration.
    Raises KeyError if a required variable is missing.
    """
    load_dotenv()
    model_path = os.getenv('MODEL_PATH')
    if not model_path:
        raise KeyError('MODEL_PATH not set in .env')
    return {
        'MODEL_PATH': model_path,
    }

def apply_seed(seed: int):
    """
    Apply deterministic seeds across random, numpy, and torch.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def main():
    configure_environment()
    config = get_environment_config()
    print('Environment configuration loaded:')
    for k, v in config.items():
        print(f'  {k} = {v}')

if __name__ == '__main__':
    main()
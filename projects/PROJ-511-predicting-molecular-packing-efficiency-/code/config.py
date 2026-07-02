"""
Project configuration and utility functions.
"""
import os
from typing import Optional

def ensure_directories() -> str:
    """
    Ensure all required project directories exist.
    
    Returns:
        Path to the project root directory
    """
    # Get the project root (parent of code/)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Define required directories
    directories = [
        'code',
        'data',
        'data/raw_cif',
        'models',
        'results',
        'contracts',
        'specs',
        'tests',
        'tests/unit',
        'tests/integration',
        'tests/contract'
    ]
    
    for directory in directories:
        full_path = os.path.join(project_root, directory)
        os.makedirs(full_path, exist_ok=True)
    
    return project_root

# Default configuration values
DEFAULT_CONFIG = {
    'seed': 42,
    'max_non_h_atoms': 50,
    'batch_size': 100,
    'retry_delay': 1.0,
    'max_retries': 3,
    'train_test_split': 0.8,
    'max_permutation_shuffles': 10000
}

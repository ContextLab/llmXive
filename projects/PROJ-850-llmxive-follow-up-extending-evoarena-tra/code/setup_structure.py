"""
Project setup and directory structure creation.

This script initializes the project directory structure required for the
EvoMem-Conflict filtering project.
"""
import os
from pathlib import Path
from src.utils.seeding import set_deterministic_seed


def create_directories(seed: int = 42):
    """
    Create the required project directory structure.
    
    Args:
        seed (int): Random seed for reproducibility (used for logging).
    """
    # Set deterministic seed
    set_deterministic_seed(seed)
    
    # Define directory structure
    directories = [
        'src',
        'src/agents',
        'src/heuristics',
        'src/data/generators',
        'src/data/benchmarks',
        'src/analysis',
        'src/utils',
        'src/cli',
        'tests',
        'tests/unit',
        'tests/integration',
        'tests/contract',
        'specs',
        'specs/001-evoconflict-filtering',
        'specs/001-evoconflict-filtering/contracts',
        'data',
        'data/raw',
        'data/processed',
        'data/logs',
        'docs',
        'figures'
    ]
    
    # Create directories
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    print("Project directory structure created successfully.")


if __name__ == '__main__':
    create_directories()

import os
import sys
from pathlib import Path
from typing import Dict, Any

# Ensure project root is in path for imports if running from code/
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def get_config() -> Dict[str, Any]:
    """
    Returns the project configuration dictionary.
    Defines paths and parameters for the pipeline.
    """
    root = Path(__file__).resolve().parent.parent.parent
    
    config = {
        'paths': {
            'root': root,
            'code': root / 'code',
            'data': root / 'data',
            'data_raw': root / 'data' / 'raw',
            'data_processed': root / 'data' / 'processed',
            'results': root / 'results',
            'logs': root / 'code' / 'logs',
            'raw_data': root / 'data' / 'raw' / 'dssc_dataset.csv',
            'processed_data': root / 'data' / 'processed',
        },
        'params': {
            'seed': 42,
            'device': 'cpu',  # Force CPU as per constraints
            'salt_pattern': '[#1,#6,#7,#8,#9,#15,#16,#17,#35,#53]', # Placeholder for RDKit default
        }
    }
    
    return config

def ensure_dirs(config: Dict[str, Any]) -> None:
    """
    Creates necessary directories defined in the config if they don't exist.
    """
    paths = config['paths']
    
    dirs_to_create = [
        paths['data_raw'],
        paths['data_processed'],
        paths['results'],
        paths['logs']
    ]
    
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
        if not dir_path.exists():
            raise OSError(f"Failed to create directory: {dir_path}")

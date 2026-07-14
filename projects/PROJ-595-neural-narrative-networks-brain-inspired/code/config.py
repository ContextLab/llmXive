import os
from typing import Dict, Any

def get_config() -> Dict[str, Any]:
    """
    Returns configuration dictionary with project settings.
    
    Returns:
        dict with keys:
            - random_seed (int): Random seed for reproducibility
            - cpu_only (bool): Whether to run on CPU only (default True)
            - max_ram_gb (int): Maximum RAM usage in GB (default 7)
    """
    return {
        'random_seed': 42,
        'cpu_only': True,
        'max_ram_gb': 7
    }

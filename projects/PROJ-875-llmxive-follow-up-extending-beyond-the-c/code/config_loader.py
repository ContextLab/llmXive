"""
Configuration Loader for Seeds.
"""
import os
import yaml
from typing import List, Optional, Dict, Any

_seeds: List[int] = []
_config_path: Optional[str] = None

def load_seeds_config(path: str) -> List[int]:
    """
    Loads seeds from a YAML configuration file.
    """
    global _seeds, _config_path
    _config_path = path
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Seeds config file not found: {path}")
    
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    
    if 'seeds' not in config:
        raise ValueError("YAML config must contain 'seeds' key")
    
    _seeds = config['seeds']
    return _seeds

def get_seeds() -> List[int]:
    """Returns the loaded list of seeds."""
    if not _seeds:
        # Default fallback if not loaded, though T009 implies it should be loaded
        # T009 says "Create config/seeds.yaml... and implement code/config_loader.py"
        # We assume T009 created the file.
        default_seeds = list(range(1, 21)) # 1 to 20 for N=20
        return default_seeds
    return _seeds

def set_seeds(seeds: List[int]):
    """Manually sets seeds (for testing)."""
    global _seeds
    _seeds = seeds

def reset_config():
    """Resets the configuration state."""
    global _seeds, _config_path
    _seeds = []
    _config_path = None

if __name__ == "__main__":
    # Test
    pass

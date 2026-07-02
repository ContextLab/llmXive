import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
import hashlib
import random
import numpy as np
import logging

# Global configuration state
_config = {
    'data_dir': 'data',
    'output_dir': 'outputs',
    'random_seed': None,
    'log_level': 'INFO',
    'simulation': {
        'sample_sizes': [10, 20, 30],
        'n_replications': 1000,
        'confidence_levels': [0.95]
    },
    'datasets': []
}

def load_config(config_path: str = 'config/simulation_config.yaml') -> Dict[str, Any]:
    """Load configuration from a YAML or JSON file."""
    path = Path(config_path)
    if not path.exists():
        logging.warning(f"Config file {config_path} not found. Using defaults.")
        return _config
    
    # Simple JSON loader for this implementation (YAML requires PyYAML)
    # Assuming the project uses JSON for simplicity in this context
    if path.suffix == '.json':
        with open(path, 'r') as f:
            loaded = json.load(f)
            _config.update(loaded)
    elif path.suffix in ['.yaml', '.yml']:
        # Fallback for YAML if PyYAML is available
        try:
            import yaml
            with open(path, 'r') as f:
                loaded = yaml.safe_load(f)
                _config.update(loaded)
        except ImportError:
            logging.warning("PyYAML not installed. Skipping YAML config.")
    return _config

def save_config(config: Dict[str, Any], config_path: str = 'config/simulation_config.yaml'):
    """Save configuration to a file."""
    path = Path(config_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(config, f, indent=2)

def get_random_seed() -> Optional[int]:
    return _config.get('random_seed')

def set_random_seed(seed: int):
    _config['random_seed'] = seed
    random.seed(seed)
    np.random.seed(seed)
    logging.info(f"Random seed set to {seed}")

def initialize_random_state(seed: int):
    """Initialize all random number generators."""
    set_random_seed(seed)

def get_data_dir(config: Dict[str, Any] = None) -> str:
    if config:
        return config.get('data_dir', _config['data_dir'])
    return _config['data_dir']

def get_output_dir(config: Dict[str, Any] = None) -> str:
    if config:
        return config.get('output_dir', _config['output_dir'])
    return _config['output_dir']

def get_log_level() -> str:
    return _config.get('log_level', 'INFO')

def get_simulation_config(config: Dict[str, Any] = None) -> Dict[str, Any]:
    if config:
        return config.get('simulation', _config['simulation'])
    return _config['simulation']

def main():
    """Test config module."""
    # Create a test config
    test_config = {
        'data_dir': 'test_data',
        'random_seed': 42,
        'simulation': {
            'n_replications': 500
        }
    }
    save_config(test_config, 'test_config.json')
    
    loaded = load_config('test_config.json')
    print(f"Loaded config: {loaded}")
    
    set_random_seed(123)
    print(f"Random seed: {get_random_seed()}")
    
    import os
    os.remove('test_config.json')

if __name__ == "__main__":
    main()

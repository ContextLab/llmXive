"""
Configuration management module.

Implements T004b: Seed injection logic and configuration loading.
"""
import logging
import random
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import yaml

logger = logging.getLogger(__name__)

def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    T004b: This function validates the schema and returns the config dict.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Validate required keys
    required_keys = ['global_seed', 'stratification_params', 'topology_targets']
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required configuration key: {key}")
    
    return config

def get_global_config() -> Dict[str, Any]:
    """
    Get the global configuration with seed injection applied.
    
    T004b: This function sets numpy.random.seed, random.seed, and
    passes random_state to NetworkX generators.
    """
    config = load_config('code/config.yaml')
    seed = config.get('global_seed', 42)
    
    # T004b: Inject seed into all random number generators
    np.random.seed(seed)
    random.seed(seed)
    
    logger.info(f"Global seed set to {seed}")
    
    return config

def set_seed_for_generator(seed: int):
    """
    Set seed for a specific generator run.
    
    T004b: Ensures reproducibility by setting seeds before generation.
    """
    np.random.seed(seed)
    random.seed(seed)

def get_generator_params(config: Dict[str, Any], topology_type: str) -> Dict[str, Any]:
    """
    Get parameters for a specific topology generator.
    
    T004b: Returns params with random_state set for NetworkX functions.
    """
    if topology_type not in config.get('simulation_params', {}):
        raise ValueError(f"Unknown topology type: {topology_type}")
    
    params = config['simulation_params'][topology_type].copy()
    
    # T004b: Ensure random_state is set for NetworkX generators
    # NetworkX functions like watts_strogatz_graph, barabasi_albert_graph,
    # and erdos_renyi_graph accept a 'seed' or 'random_state' parameter.
    # We pass the global seed here.
    params['seed'] = config.get('global_seed', 42)
    
    return params

def validate_config_schema(config: Dict[str, Any]) -> bool:
    """
    Validate configuration against required schema.
    
    T007: Base configuration loader validation.
    """
    required = {
        'global_seed': int,
        'stratification_params': dict,
        'topology_targets': list,
        'simulation_params': dict
    }
    
    for key, expected_type in required.items():
        if key not in config:
            logger.error(f"Missing required key: {key}")
            return False
        if not isinstance(config[key], expected_type):
            logger.error(f"Invalid type for {key}: expected {expected_type}, "
                       f"got {type(config[key])}")
            return False
    
    # Validate stratification_params
    strat = config['stratification_params']
    if 'bins' not in strat or not isinstance(strat['bins'], list):
        logger.error("stratification_params must contain 'bins' list")
        return False
    
    if 'target_counts' not in strat or not isinstance(strat['target_counts'], dict):
        logger.error("stratification_params must contain 'target_counts' dict")
        return False
    
    return True

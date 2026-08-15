"""
Sweep logic for violation magnitudes to generate bias curves (T021b).

This module provides configuration and iteration logic for systematically
varying violation parameters (contamination rates, AR coefficients, etc.)
to generate bias curves as required by SC-001.
"""
import logging
from typing import List, Dict, Any, Generator, Tuple
import json
from pathlib import Path

from config import VIOLATION_SWEEP_CONFIG, RANDOM_SEED

logger = logging.getLogger(__name__)

def get_sweep_configs(violation_type: str) -> List[Dict[str, Any]]:
    """
    Retrieve the list of configuration dictionaries for a specific violation type.
    
    Args:
        violation_type: One of 'heavy_tailed', 'ar1_autocorrelation', 'effect_size_heterogeneity'
    
    Returns:
        List of dicts, each representing a specific parameter setting for the sweep.
    """
    if violation_type not in VIOLATION_SWEEP_CONFIG:
        raise ValueError(f"Unknown violation type: {violation_type}. "
                       f"Available types: {list(VIOLATION_SWEEP_CONFIG.keys())}")
    
    config = VIOLATION_SWEEP_CONFIG[violation_type]
    param_name = config["parameter"]
    values = config["values"]
    
    configs = []
    for val in values:
        cfg = {
            "violation_type": violation_type,
            "parameter_name": param_name,
            "parameter_value": val,
            "description": config["description"]
        }
        
        # Add fixed parameters if present (e.g., for effect_size_heterogeneity)
        if "fixed_separation" in config:
            cfg["fixed_separation"] = config["fixed_separation"]
        if "fixed_ratio" in config:
            cfg["fixed_ratio"] = config["fixed_ratio"]
            
        configs.append(cfg)
    
    return configs

def run_sweep_for_violation(violation_type: str) -> Generator[Dict[str, Any], None, None]:
    """
    Generator that yields configuration dictionaries for a full sweep of a violation type.
    
    This is the primary interface for T022 (main.py extension) to iterate over
    violation configurations.
    
    Args:
        violation_type: The type of violation to sweep.
    
    Yields:
        Dict containing the full configuration for one iteration of the sweep.
    """
    configs = get_sweep_configs(violation_type)
    logger.info(f"Starting sweep for {violation_type}: {len(configs)} configurations")
    
    for i, cfg in enumerate(configs):
        logger.debug(f"Emitting config {i+1}/{len(configs)}: {cfg}")
        yield cfg

def generate_all_sweep_configs() -> List[Dict[str, Any]]:
    """
    Generate a combined list of all configurations for all violation types.
    
    Useful for running a full batch of experiments or generating a master
    configuration file.
    
    Returns:
        List of all configuration dictionaries across all violation types.
    """
    all_configs = []
    for v_type in VIOLATION_SWEEP_CONFIG.keys():
        configs = get_sweep_configs(v_type)
        all_configs.extend(configs)
    
    logger.info(f"Generated {len(all_configs)} total sweep configurations")
    return all_configs

def save_sweep_configs(output_path: str = "data/results/sweep_config.json"):
    """
    Save the generated sweep configurations to a JSON file for reproducibility.
    
    Args:
        output_path: Path where the JSON file will be saved.
    """
    configs = generate_all_sweep_configs()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(configs, f, indent=2)
    
    logger.info(f"Sweep configurations saved to {output_path}")
    return output_path

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Generating sweep configurations...")
    save_sweep_configs()
    print("Done.")

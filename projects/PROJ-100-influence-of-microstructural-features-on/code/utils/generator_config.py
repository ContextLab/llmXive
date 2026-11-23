"""
Configuration for synthetic data generation.
Defines statistical parameters for generating realistic aluminum alloy fatigue data.
"""
import os
import json
from typing import Dict, Any, List

def get_generator_config() -> Dict[str, Any]:
    """
    Returns the configuration dictionary for the synthetic data generator.
    Includes means, standard deviations, and correlation structures.
    """
    return {
        "n_samples": 150,
        "random_seed": 42,
        "grain_size": {
            "mean": 25.0,
            "std": 5.0,
            "unit": "um"
        },
        "secondary_phase": {
            "mean": 0.15,
            "std": 0.05,
            "unit": "fraction"
        },
        "dislocation_proxy": {
            "mean": 1e8,
            "std": 2e7,
            "unit": "m^-2"
        },
        "fatigue_life": {
            "mean": 1e6,
            "std": 2e5,
            "unit": "cycles"
        },
        "groups": {
            "batches": 5,
            "heat_treatments": 3
        }
    }

def save_config_to_file(filepath: str, config: Dict[str, Any]) -> None:
    """
    Saves the generator configuration to a JSON file.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(config, f, indent=4)
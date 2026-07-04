"""
Configuration for synthetic data generation.
Defines statistical parameters and schema for generating synthetic aluminum alloy fatigue data.
"""
import os
import json
from typing import Dict, Any, List

def get_generator_config() -> Dict[str, Any]:
    """
    Returns the configuration dictionary for synthetic data generation.
    
    Returns:
        Dict containing statistical parameters, correlation matrix, and schema definitions.
    """
    return {
        "random_seed": 42,
        "n_records": 150,
        "statistical_params": {
            "grain_size_mean": 25.0,
            "grain_size_std": 5.0,
            "secondary_phase_mean": 0.15,
            "secondary_phase_std": 0.05,
            "dislocation_proxy_mean": 1e9,
            "dislocation_proxy_std": 2e8,
            "fatigue_cycles_mean": 1e5,
            "fatigue_cycles_std": 2e4
        },
        "correlation_matrix": {
            "grain_size": {"fatigue_cycles": -0.6, "secondary_phase": 0.2},
            "secondary_phase": {"dislocation_proxy": 0.4, "fatigue_cycles": -0.3},
            "dislocation_proxy": {"fatigue_cycles": -0.5}
        },
        "categorical_values": {
            "alloy_batch_id": ["BATCH_A", "BATCH_B", "BATCH_C", "BATCH_D", "BATCH_E"],
            "heat_treatment_group": ["HT_1", "HT_2", "HT_3"]
        },
        "missing_rate_threshold": 0.20
    }

def save_config_to_file(config: Dict[str, Any], filepath: str) -> None:
    """
    Saves the generator configuration to a JSON file.
    
    Args:
        config: The configuration dictionary.
        filepath: Path to save the JSON file.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(config, f, indent=2)
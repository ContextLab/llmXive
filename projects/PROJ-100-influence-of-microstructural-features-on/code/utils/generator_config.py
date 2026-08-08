import os
import json
from typing import Dict, Any, List

def get_generator_config() -> Dict[str, Any]:
    """
    Returns the statistical configuration for synthetic data generation.
    Includes mean/std for microstructural features and correlation matrix.
    """
    config = {
        "random_seed": 42,
        "n_samples": 150,
        "features": {
            "grain_size_mean": 15.0,
            "grain_size_std": 4.0,
            "secondary_phase_mean": 0.08,
            "secondary_phase_std": 0.03,
            "dislocation_proxy_mean": 0.6,
            "dislocation_proxy_std": 0.15,
            "fatigue_life_mean_log": 5.5,
            "fatigue_life_std_log": 0.4
        },
        "correlations": [
            {"col1": "grain_size", "col2": "fatigue_life", "corr": 0.6},
            {"col1": "secondary_phase", "col2": "fatigue_life", "corr": -0.4},
            {"col1": "dislocation_proxy", "col2": "fatigue_life", "corr": -0.3}
        ],
        "groups": {
            "alloy_batch_ids": ["BATCH_A", "BATCH_B", "BATCH_C"],
            "heat_treatment_groups": ["HT_1", "HT_2", "HT_3"]
        }
    }
    return config

def save_config_to_file(config: Dict[str, Any], filepath: str) -> None:
    """Saves the generator configuration to a JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(config, f, indent=2)

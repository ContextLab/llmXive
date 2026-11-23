import logging
from typing import List, Dict, Any, Generator, Tuple
import json
from pathlib import Path
from config import VIOLATION_SWEEP_CONFIG, RANDOM_SEED
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_sweep_configs(violation_type: str) -> List[Dict[str, Any]]:
    """
    Retrieve the list of parameter configurations for a specific violation type.
    Based on VIOLATION_SWEEP_CONFIG in config.py.

    Args:
        violation_type: One of 'heavy_tailed', 'ar1_autocorrelation', 'effect_size_heterogeneity'

    Returns:
        List of dictionaries, each containing the specific parameter value and metadata.
    """
    if violation_type not in VIOLATION_SWEEP_CONFIG:
        raise ValueError(f"Unknown violation type: {violation_type}. "
                         f"Available: {list(VIOLATION_SWEEP_CONFIG.keys())}")

    config = VIOLATION_SWEEP_CONFIG[violation_type]
    param_name = config["param_name"]
    values = config["values"]

    configs = []
    for val in values:
        configs.append({
            "violation_type": violation_type,
            param_name: val,
            "description": config["description"],
            "seed": RANDOM_SEED
        })
    return configs

def run_sweep_for_violation(violation_type: str, dataset_name: str) -> List[Dict[str, Any]]:
    """
    Generates the sweep configurations for a specific violation type and dataset.
    In a full pipeline, this would iterate and call the perturbation injection,
    but here we return the configuration plan as defined in SC-001.

    Args:
        violation_type: The type of violation to sweep (e.g., 'ar1_autocorrelation')
        dataset_name: Name of the dataset being tested (for logging/context)

    Returns:
        List of configuration dictionaries to be used by the main pipeline loop.
    """
    logger.info(f"Generating sweep configs for {violation_type} on {dataset_name}")
    configs = get_sweep_configs(violation_type)
    for cfg in configs:
        cfg["dataset"] = dataset_name
    return configs

def generate_all_sweep_configs() -> Dict[str, List[Dict[str, Any]]]:
    """
    Generates sweep configurations for all defined violation types.
    Returns a dictionary mapping violation_type to list of configs.
    """
    all_configs = {}
    for v_type in VIOLATION_SWEEP_CONFIG.keys():
        all_configs[v_type] = get_sweep_configs(v_type)
    return all_configs

def save_sweep_configs(output_path: Path):
    """
    Saves the generated sweep configurations to a JSON file.
    This artifact serves as the input for the main pipeline loop (T022).

    Args:
        output_path: Path to the output JSON file.
    """
    all_configs = generate_all_sweep_configs()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(all_configs, f, indent=2)
    
    logger.info(f"Sweep configurations saved to {output_path}")
    return all_configs

def main():
    """Entry point to generate and save sweep configurations."""
    output_file = Path(__file__).resolve().parent.parent / "data" / "results" / "sweep_configs.json"
    configs = save_sweep_configs(output_file)
    
    # Summary log
    total_configs = sum(len(v) for v in configs.values())
    logger.info(f"Generated {total_configs} total violation configurations.")

if __name__ == "__main__":
    main()
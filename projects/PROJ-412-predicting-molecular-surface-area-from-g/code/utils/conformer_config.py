import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from .config import get_project_root, get_data_dir
from .logging import get_logger

logger = get_logger(__name__)

DEFAULT_NUM_THREADS = 0
DEFAULT_MAX_ATTEMPTS = 250
DEFAULT_ENERGY_MINIMIZATION_STEPS = 200

def generate_conformer_config(
    num_threads: int = DEFAULT_NUM_THREADS,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    energy_minimization_steps: int = DEFAULT_ENERGY_MINIMIZATION_STEPS,
    random_seed: int = 42
) -> Dict[str, int]:
    """
    Generate a conformer configuration dictionary.
    """
    return {
        "numThreads": num_threads,
        "maxAttempts": max_attempts,
        "energyMinimizationSteps": energy_minimization_steps,
        "random_seed": random_seed
    }

def save_conformer_config(config: Dict[str, int], output_path: Optional[str] = None) -> str:
    """
    Save conformer configuration to a JSON file.
    Returns the path to the saved file.
    """
    if output_path is None:
        output_path = str(get_data_dir() / "processed" / "conformer_params.json")
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Saved conformer config to {output_path}")
    return str(output_path)

def load_conformer_config(input_path: Optional[str] = None) -> Dict[str, int]:
    """
    Load conformer configuration from a JSON file.
    Returns default config if file doesn't exist.
    """
    if input_path is None:
        input_path = str(get_data_dir() / "processed" / "conformer_params.json")
    
    input_path = Path(input_path)
    
    if input_path.exists():
        with open(input_path, 'r') as f:
            return json.load(f)
    
    logger.warning(f"Conformer config not found at {input_path}, using defaults")
    return {
        "numThreads": DEFAULT_NUM_THREADS,
        "maxAttempts": DEFAULT_MAX_ATTEMPTS,
        "energyMinimizationSteps": DEFAULT_ENERGY_MINIMIZATION_STEPS,
        "random_seed": 42
    }

def main():
    """
    Entry point for conformer config generation.
    """
    config = generate_conformer_config()
    save_conformer_config(config)
    logger.info("Conformer configuration generated and saved")

if __name__ == "__main__":
    main()
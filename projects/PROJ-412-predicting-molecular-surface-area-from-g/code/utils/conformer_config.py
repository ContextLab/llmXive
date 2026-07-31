import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from .config import get_project_root, get_data_dir
from .logging import get_logger

def generate_conformer_config(
    num_threads: int = 1,
    max_attempts: int = 250,
    energy_minimization_steps: int = 200,
    mmff_variant: str = "MMFF94s"
) -> Dict[str, Any]:
    """
    Generate RDKit conformer generation parameters.
    
    Args:
        num_threads: Number of threads for parallel processing.
        max_attempts: Maximum number of conformer generation attempts.
        energy_minimization_steps: Steps for energy minimization.
        mmff_variant: MMFF force field variant to use.
        
    Returns:
        Dictionary of conformer generation parameters.
    """
    return {
        "numThreads": num_threads,
        "maxAttempts": max_attempts,
        "energyMinimizationSteps": energy_minimization_steps,
        "mmffVariant": mmff_variant,
        "numConfs": 10,
        "pruneRmsThresh": 0.5
    }

def load_conformer_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load conformer configuration from a JSON file.
    
    Args:
        config_path: Path to the config file. If None, uses default location.
        
    Returns:
        Dictionary of conformer generation parameters.
    """
    if config_path is None:
        config_path = get_data_dir() / "processed" / "conformer_params.json"
    
    logger = get_logger("conformer_config")
    
    if not Path(config_path).exists():
        logger.warning(f"Config file not found at {config_path}, generating default config.")
        config = generate_conformer_config()
        # Save default config
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        return config
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Validate required keys
    required_keys = ["numThreads", "maxAttempts", "energyMinimizationSteps"]
    for key in required_keys:
        if key not in config:
            logger.warning(f"Missing required key '{key}' in config, using default.")
            config[key] = generate_conformer_config()[key]
    
    return config

def main() -> None:
    """
    Main entry point for conformer config utilities.
    """
    logger = get_logger("conformer_config")
    logger.info("Conformer config utilities loaded.")
    config = load_conformer_config()
    logger.info(f"Loaded conformer config: {config}")

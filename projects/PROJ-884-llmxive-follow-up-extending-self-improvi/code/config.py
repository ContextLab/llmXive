"""
Configuration management for the llmXive BES pipeline.

Handles experiment parameters, default values, and initialization logic.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from code.utils.seed import set_seed, get_seed
from code.utils.logger import log_experiment_entry
import logging

# Placeholder for TDP (Thermal Design Power) in Watts.
# This value MUST be overwritten by T008c (generate_tdp_constant.py) after calibration.
# If T008c has not been run, the system MUST log a warning but continue execution.
DEFAULT_TDP_WATTS = 0.0

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the configuration file.
        
    Returns:
        Dictionary containing configuration parameters.
        
    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the file contains invalid YAML.
    """
    path = Path(config_path)
    if not path.exists():
        # Return a default config if file doesn't exist, but log a warning
        logging.warning(f"Config file {config_path} not found. Using defaults.")
        return get_default_config()
        
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def save_config(config: Dict[str, Any], config_path: str = "config.yaml") -> None:
    """
    Save configuration to a YAML file.
    
    Args:
        config: Configuration dictionary to save.
        config_path: Path to the configuration file.
    """
    path = Path(config_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

def get_experiment_id() -> str:
    """
    Generate a unique experiment ID based on the current seed and timestamp.
    
    Returns:
        A unique string identifier for the experiment.
    """
    seed = get_seed()
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"exp_{seed}_{timestamp}"

def initialize_experiment(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Initialize the experiment environment.
    
    This function:
    1. Sets up the random seed.
    2. Logs the experiment entry.
    3. Validates that TDP calibration has occurred (logs warning if not).
    
    Args:
        config: Optional configuration dictionary. If None, loads from default path.
        
    Returns:
        The initialized configuration dictionary.
    """
    if config is None:
        config = load_config()
    
    # Set seed for reproducibility
    if 'seed' in config:
        set_seed(config['seed'])
    
    # Check TDP calibration status
    # The task T007b requires a placeholder value that warns if not overwritten.
    # We check if the placeholder is still 0.0 (the default).
    current_tdp = config.get('tdp_watts', DEFAULT_TDP_WATTS)
    if current_tdp == 0.0:
        logging.warning(
            "TDP calibration not detected (tdp_watts is 0.0). "
            "Energy consumption metrics will be inaccurate. "
            "Please run code/utils/generate_tdp_constant.py (Task T008c) to calibrate."
        )
    
    # Log experiment entry
    exp_id = get_experiment_id()
    log_experiment_entry(exp_id, config)
    
    return config

def get_default_config() -> Dict[str, Any]:
    """
    Return the default configuration dictionary.
    
    Returns:
        Dictionary with default experiment parameters.
    """
    return {
        "population_size": 50,
        "generations": 20,
        "mutation_rate": 0.1,
        "crossover_rate": 0.7,
        "seed": 42,
        "tdp_watts": DEFAULT_TDP_WATTS,  # Placeholder, to be overwritten by T008c
        "max_attempts": 100,
        "timeout_seconds": 300,
        "device": "cpu"
    }

def main():
    """
    Main entry point for the config module (for testing/debugging).
    """
    print("Loading default config...")
    config = get_default_config()
    print(f"Default TDP: {config['tdp_watts']} W")
    
    print("Initializing experiment...")
    initialized_config = initialize_experiment(config)
    print(f"Experiment ID: {get_experiment_id()}")

if __name__ == "__main__":
    main()

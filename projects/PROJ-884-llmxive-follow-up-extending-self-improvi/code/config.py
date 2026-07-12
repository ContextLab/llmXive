"""
Configuration loader for llmXive experiment parameters.

Handles experiment parameters such as population size, generations,
and other hyperparameters from YAML configuration files.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from code.utils.seed import set_seed, get_seed
from code.utils.logger import log_experiment_entry


DEFAULT_CONFIG = {
    "population_size": 100,
    "generations": 50,
    "mutation_rate": 0.1,
    "crossover_rate": 0.7,
    "elitism_count": 5,
    "max_trajectory_length": 1000,
    "seed": 42,
    "log_level": "INFO",
    "checkpoint_interval": 10,
    "max_workers": 4,
    "symbolic_planner_timeout": 30,
    "llm_model_id": "distilbert-base-uncased",
    "llm_max_new_tokens": 512,
    "llm_temperature": 0.7,
    "verifier_timeout_ms": 100,
}


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load experiment configuration from a YAML file or use defaults.
    
    Args:
        config_path: Path to the YAML configuration file. If None, 
                    defaults are used.
    
    Returns:
        Dictionary containing all configuration parameters.
    
    Raises:
        FileNotFoundError: If the specified config file doesn't exist.
        yaml.YAMLError: If the config file contains invalid YAML.
    """
    config = DEFAULT_CONFIG.copy()
    
    if config_path is not None:
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            file_config = yaml.safe_load(f)
            if file_config:
                config.update(file_config)
    
    # Validate required fields
    _validate_config(config)
    
    return config


def _validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration parameters.
    
    Args:
        config: Configuration dictionary to validate.
    
    Raises:
        ValueError: If any parameter is invalid.
    """
    if not isinstance(config.get("population_size"), int) or config["population_size"] < 1:
        raise ValueError("population_size must be a positive integer")
    
    if not isinstance(config.get("generations"), int) or config["generations"] < 1:
        raise ValueError("generations must be a positive integer")
    
    if not (0 <= config.get("mutation_rate", 0) <= 1):
        raise ValueError("mutation_rate must be between 0 and 1")
    
    if not (0 <= config.get("crossover_rate", 0) <= 1):
        raise ValueError("crossover_rate must be between 0 and 1")
    
    if not isinstance(config.get("elitism_count"), int) or config["elitism_count"] < 0:
        raise ValueError("elitism_count must be a non-negative integer")
    
    if not isinstance(config.get("max_workers"), int) or config["max_workers"] < 1:
        raise ValueError("max_workers must be a positive integer")
    
    if not isinstance(config.get("symbolic_planner_timeout"), (int, float)) or config["symbolic_planner_timeout"] <= 0:
        raise ValueError("symbolic_planner_timeout must be a positive number")
    
    if not isinstance(config.get("verifier_timeout_ms"), int) or config["verifier_timeout_ms"] <= 0:
        raise ValueError("verifier_timeout_ms must be a positive integer")


def save_config(config: Dict[str, Any], output_path: str) -> None:
    """
    Save configuration to a YAML file.
    
    Args:
        config: Configuration dictionary to save.
        output_path: Path where the YAML file will be written.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


def get_experiment_id(config: Dict[str, Any]) -> str:
    """
    Generate a unique experiment ID based on configuration.
    
    Args:
        config: Configuration dictionary.
    
    Returns:
        A string identifier for the experiment.
    """
    seed = config.get("seed", 42)
    pop_size = config.get("population_size", 100)
    gens = config.get("generations", 50)
    return f"exp_seed{seed}_pop{pop_size}_gen{gens}"


def initialize_experiment(config: Dict[str, Any]) -> None:
    """
    Initialize the experiment environment based on configuration.
    
    Sets up random seeds and logs the configuration.
    
    Args:
        config: Configuration dictionary.
    """
    seed = config.get("seed", 42)
    set_seed(seed)
    
    experiment_id = get_experiment_id(config)
    log_entry = {
        "experiment_id": experiment_id,
        "config": config,
        "status": "initialized"
    }
    
    # Log to the experiment log file
    log_experiment_entry(log_entry)


def main() -> None:
    """
    Main entry point for testing the configuration loader.
    
    Parses command line arguments, loads configuration, and prints it.
    """
    import sys
    
    config_path = None
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    
    try:
        config = load_config(config_path)
        print("Configuration loaded successfully:")
        print("-" * 40)
        for key, value in sorted(config.items()):
            print(f"{key}: {value}")
        print("-" * 40)
        
        # Initialize experiment
        initialize_experiment(config)
        print(f"Experiment initialized with ID: {get_experiment_id(config)}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Configuration validation error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
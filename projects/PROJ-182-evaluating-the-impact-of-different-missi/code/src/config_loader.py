"""
Configuration loader for the RD simulation pipeline.

Reads YAML configuration files for simulation, missingness, and estimation settings.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
from src.logging_config import get_logger

logger = get_logger(__name__)


def load_yaml_config(file_path: str) -> Dict[str, Any]:
    """
    Load a YAML configuration file.

    Args:
        file_path: Path to the YAML file.

    Returns:
        Dictionary containing the configuration.

    Raises:
        FileNotFoundError: If the file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")

    with open(path, 'r') as f:
        config = yaml.safe_load(f)

    logger.debug(f"Loaded configuration from {file_path}")
    return config


def load_simulation_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load simulation configuration from config/simulation.yaml.

    Args:
        config_path: Optional override for the config file path.

    Returns:
        Dictionary with simulation parameters.
    """
    if config_path is None:
        config_path = "config/simulation.yaml"

    return load_yaml_config(config_path)


def load_missingness_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load missingness configuration from config/missingness.yaml.

    Args:
        config_path: Optional override for the config file path.

    Returns:
        Dictionary with missingness parameters.
    """
    if config_path is None:
        config_path = "config/missingness.yaml"

    return load_yaml_config(config_path)


def load_estimation_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load estimation configuration from config/estimation.yaml.

    Args:
        config_path: Optional override for the config file path.

    Returns:
        Dictionary with estimation parameters.
    """
    if config_path is None:
        config_path = "config/estimation.yaml"

    return load_yaml_config(config_path)


def get_missingness_rate(config: Dict[str, Any]) -> float:
    """
    Extract missingness rate from configuration.

    Args:
        config: Missingness configuration dictionary.

    Returns:
        Missingness rate as a float.
    """
    rate = config.get('rate', 0.2)
    if not 0.0 <= rate <= 1.0:
        raise ValueError(f"Invalid missingness rate: {rate}. Must be between 0.0 and 1.0.")
    return float(rate)


# Example usage and creation of default config files if they don't exist
def ensure_default_configs():
    """
    Create default configuration files if they don't exist.
    Useful for initial setup.
    """
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)

    # Default simulation config
    sim_config_path = config_dir / "simulation.yaml"
    if not sim_config_path.exists():
        default_sim = {
            'sample_size': 1000,
            'true_effect': 2.0,
            'seed': 42,
            'exclusion_restriction': 0.0,
            'beta0': 0.0,
            'beta1': 1.0,
            'beta2': 0.5,
            'sigma': 1.0
        }
        with open(sim_config_path, 'w') as f:
            yaml.dump(default_sim, f, default_flow_style=False)
        logger.info(f"Created default simulation config at {sim_config_path}")

    # Default missingness config
    miss_config_path = config_dir / "missingness.yaml"
    if not miss_config_path.exists():
        default_miss = {
            'rate': 0.2,
            'mechanism': 'mcar'  # mcar, mar, mnar
        }
        with open(miss_config_path, 'w') as f:
            yaml.dump(default_miss, f, default_flow_style=False)
        logger.info(f"Created default missingness config at {miss_config_path}")

    # Default estimation config
    est_config_path = config_dir / "estimation.yaml"
    if not est_config_path.exists():
        default_est = {
            'bandwidth_rule': 'ik',  # ik, cv, fixed
            'bandwidth_floor': 0.05,
            'imputation_count': 5,
            'nominal_confidence': 0.95
        }
        with open(est_config_path, 'w') as f:
            yaml.dump(default_est, f, default_flow_style=False)
        logger.info(f"Created default estimation config at {est_config_path}")


if __name__ == "__main__":
    ensure_default_configs()
    print("Default configuration files created in config/")
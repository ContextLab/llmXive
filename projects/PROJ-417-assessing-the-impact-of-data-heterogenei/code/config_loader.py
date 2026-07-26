"""
Configuration loader for the Heterogeneity Impact Assessment Pipeline.

This module parses `code/config.yaml` and provides access to configuration
parameters. It implements the fallback logic required when the primary data
source is unavailable, triggering the synthetic data generation path.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from utils.logging import get_logger

logger = get_logger(__name__)

CONFIG_PATH = Path(__file__).parent / "config.yaml"


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Path to the config file. Defaults to code/config.yaml.

    Returns:
        Dictionary containing the configuration parameters.

    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the config file is not valid YAML.
    """
    if config_path is None:
        config_path = CONFIG_PATH

    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    logger.info(f"Configuration loaded from {config_path}")
    return config


def get_simulation_params(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract simulation parameters from the configuration.

    Args:
        config: The loaded configuration dictionary.

    Returns:
        Dictionary containing simulation parameters.
    """
    return config.get("simulation_parameters", {})


def get_data_source_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract data source configuration from the configuration.

    Args:
        config: The loaded configuration dictionary.

    Returns:
        Dictionary containing data source paths.
    """
    return config.get("data_source", {})


def get_base_data_path(config: Dict[str, Any]) -> Path:
    """
    Get the path to the base data file.

    Args:
        config: The loaded configuration dictionary.

    Returns:
        Path to the base data file.

    Raises:
        FileNotFoundError: If the base data file does not exist and no fallback is available.
    """
    data_source_config = get_data_source_config(config)
    base_path = Path(data_source_config.get("base_data_path", "data/raw/cochrane_base.csv"))

    if not base_path.exists():
        logger.warning(f"Base data file not found: {base_path}")
        
        # Check for synthetic fallback
        fallback_path = Path(data_source_config.get("synthetic_fallback_path", "data/raw/cochrane_base_synthetic.csv"))
        
        if fallback_path.exists():
            logger.info(f"Using synthetic fallback data: {fallback_path}")
            return fallback_path
        else:
            logger.error("No base data available and no synthetic fallback found.")
            # Raise FileNotFoundError to trigger the fallback logic in the main pipeline
            # This matches the requirement to catch FileNotFoundError from data fetch
            raise FileNotFoundError(f"REAL_DATA_FETCH_FAILED: Neither base data ({base_path}) nor synthetic fallback ({fallback_path}) found.")

    return base_path


def get_nominal_confidence_level(config: Dict[str, Any]) -> float:
    """
    Get the nominal confidence level for coverage calculations.

    Args:
        config: The loaded configuration dictionary.

    Returns:
        Nominal confidence level (e.g., 0.95).
    """
    return float(config.get("nominal_confidence_level", 0.95))


def get_min_studies_for_reliability(config: Dict[str, Any]) -> int:
    """
    Get the minimum number of studies required for a reliable result.

    Args:
        config: The loaded configuration dictionary.

    Returns:
        Minimum number of studies.
    """
    return int(config.get("analysis", {}).get("min_studies_for_reliability", 5))


def get_significance_level(config: Dict[str, Any]) -> float:
    """
    Get the significance level for statistical tests.

    Args:
        config: The loaded configuration dictionary.

    Returns:
        Significance level.
    """
    return float(config.get("analysis", {}).get("significance_level", 0.01))


def get_replicate_count(config: Dict[str, Any]) -> int:
    """
    Get the number of replicates to generate per heterogeneity level.

    Args:
        config: The loaded configuration dictionary.

    Returns:
        Number of replicates.
    """
    return int(get_simulation_params(config).get("replicate_count", 500))


def get_tau2_levels(config: Dict[str, Any]) -> list:
    """
    Get the heterogeneity levels (tau^2) to simulate.

    Args:
        config: The loaded configuration dictionary.

    Returns:
        List of tau^2 levels.
    """
    return get_simulation_params(config).get("tau2_levels", [0.0, 0.1, 0.5, 1.0, 2.0])


def get_random_seed(config: Dict[str, Any]) -> int:
    """
    Get the random seed for reproducibility.

    Args:
        config: The loaded configuration dictionary.

    Returns:
        Random seed.
    """
    return int(get_simulation_params(config).get("random_seed", 42))


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate the configuration structure.

    Args:
        config: The loaded configuration dictionary.

    Returns:
        True if valid, False otherwise.
    """
    required_keys = ["nominal_confidence_level", "simulation_parameters", "data_source", "analysis"]
    for key in required_keys:
        if key not in config:
            logger.error(f"Missing required configuration key: {key}")
            return False

    sim_params = config.get("simulation_parameters", {})
    if "replicate_count" not in sim_params:
        logger.error("Missing replicate_count in simulation_parameters")
        return False

    if "tau2_levels" not in sim_params:
        logger.error("Missing tau2_levels in simulation_parameters")
        return False

    data_source = config.get("data_source", {})
    if "base_data_path" not in data_source:
        logger.error("Missing base_data_path in data_source")
        return False

    analysis = config.get("analysis", {})
    if "min_studies_for_reliability" not in analysis:
        logger.error("Missing min_studies_for_reliability in analysis")
        return False

    return True


def main():
    """
    Main function to test the configuration loading.
    """
    try:
        config = load_config()
        
        if not validate_config(config):
            logger.error("Configuration validation failed.")
            return 1

        logger.info("Configuration loaded and validated successfully.")
        logger.info(f"Nominal confidence level: {get_nominal_confidence_level(config)}")
        logger.info(f"Replicate count: {get_replicate_count(config)}")
        logger.info(f"Tau2 levels: {get_tau2_levels(config)}")
        logger.info(f"Random seed: {get_random_seed(config)}")
        
        # Try to get the base data path (this will trigger fallback logic if needed)
        try:
            data_path = get_base_data_path(config)
            logger.info(f"Base data path: {data_path}")
        except FileNotFoundError as e:
            logger.error(f"Data fetch failed: {e}")
            # Re-raise to allow the main pipeline to handle the fallback
            raise

        return 0

    except FileNotFoundError as e:
        logger.error(f"Configuration or data error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
"""
Configuration loader for the carbon footprint measurement pipeline.
Loads and validates settings from code/config.yaml.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config.yaml. Defaults to 'code/config.yaml'.

    Returns:
        Dictionary containing configuration settings.

    Raises:
        FileNotFoundError: If config file does not exist.
        yaml.YAMLError: If config file is not valid YAML.
    """
    if config_path is None:
        # Default path relative to project root
        config_path = Path("code") / "config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in config file: {e}")

    # Validate required sections
    required_sections = ["co2_factors", "human_baseline", "codecarbon"]
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required configuration section: {section}")

    logger.info(f"Loaded configuration from {config_path}")
    return config

def get_co2_factor(config: Dict[str, Any], region: Optional[str] = None) -> float:
    """
    Get CO2 conversion factor for a specific region.

    Args:
        config: Configuration dictionary.
        region: Region code (e.g., "US", "EU"). Defaults to config default.

    Returns:
        CO2 factor in kg CO2 per kWh.
    """
    if region is None:
        region = config["co2_factors"]["default_region"]

    regions = config["co2_factors"]["regions"]
    if region not in regions:
        logger.warning(f"Unknown region '{region}', using default: {config['co2_factors']['default_region']}")
        region = config["co2_factors"]["default_region"]

    return regions[region]

def get_human_power(config: Dict[str, Any], model: Optional[str] = None) -> int:
    """
    Get power draw for human baseline in Watts.

    Args:
        config: Configuration dictionary.
        model: Power model name ("low", "medium", "high"). Defaults to config default.

    Returns:
        Power draw in Watts.
    """
    if model is None:
        model = config["human_baseline"]["default_power_model"]

    models = config["human_baseline"]["sensitivity_models"]
    model_dict = {m["name"]: m["watts"] for m in models}

    if model not in model_dict:
        logger.warning(f"Unknown power model '{model}', using default: {config['human_baseline']['default_power_model']}")
        model = config["human_baseline"]["default_power_model"]

    return model_dict[model]

def get_sensitivity_models(config: Dict[str, Any]) -> list:
    """
    Get list of power models for sensitivity analysis.

    Args:
        config: Configuration dictionary.

    Returns:
        List of dictionaries with 'name' and 'watts' keys.
    """
    return config["human_baseline"]["sensitivity_models"]

def get_codecarbon_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get CodeCarbon-specific configuration.

    Args:
        config: Configuration dictionary.

    Returns:
        Dictionary with CodeCarbon settings.
    """
    return config["codecarbon"]

def main():
    """
    CLI entry point to load and print configuration.
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    try:
        config = load_config()

        # Print key settings
        print("\n=== Configuration Summary ===")
        print(f"Default CO2 Region: {config['co2_factors']['default_region']}")
        print(f"Default Power Model: {config['human_baseline']['default_power_model']}")
        print(f"CodeCarbon Region: {config['codecarbon']['default_region']}")

        # Print CO2 factors
        print("\nCO2 Factors (kg CO2/kWh):")
        for region, factor in config["co2_factors"]["regions"].items():
            print(f"  {region}: {factor}")

        # Print power models
        print("\nPower Models (Watts):")
        for model in config["human_baseline"]["sensitivity_models"]:
            print(f"  {model['name']}: {model['watts']}W")

        print("\nConfiguration loaded successfully.")

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"YAML Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Validation Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
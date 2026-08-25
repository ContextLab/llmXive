"""
Configuration Loader Module for Gut Microbiome and EEG Analysis Pipeline.

This module provides functions to load, validate, and extract parameters
from the preprocess.yaml configuration file.
"""
import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from config import get_project_root

# Configure module logger
logger = logging.getLogger(__name__)


def load_preprocess_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the preprocessing configuration from a YAML file.

    Args:
        config_path: Optional path to the config file. If None, uses
                    default path relative to project root.

    Returns:
        Dictionary containing the full configuration.

    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the config file is not valid YAML.
    """
    if config_path is None:
        project_root = get_project_root()
        config_path = project_root / "code" / "preprocess.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    logger.info(f"Loading configuration from: {config_path}")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    if config is None:
        raise ValueError("Configuration file is empty or invalid")

    logger.info("Configuration loaded successfully")
    return config


def get_filter_bands(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract EEG filter band parameters from configuration.

    Args:
        config: The loaded configuration dictionary.

    Returns:
        Dictionary with 'low_cutoff', 'high_cutoff', 'filter_type', 'order'.
    """
    try:
        eeg_config = config['eeg']
        filter_config = eeg_config['filter_bands']
        return {
            'low_cutoff': filter_config['low_cutoff'],
            'high_cutoff': filter_config['high_cutoff'],
            'filter_type': filter_config['filter_type'],
            'order': filter_config['order']
        }
    except KeyError as e:
        logger.warning(f"Missing filter band configuration key: {e}")
        # Return defaults
        return {
            'low_cutoff': 0.5,
            'high_cutoff': 45.0,
            'filter_type': 'bandpass',
            'order': 4
        }


def get_ica_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract ICA settings from configuration.

    Args:
        config: The loaded configuration dictionary.

    Returns:
        Dictionary with ICA parameters.
    """
    try:
        eeg_config = config['eeg']
        ica_config = eeg_config['ica']
        return {
            'method': ica_config.get('method', 'fastica'),
            'n_components': ica_config.get('n_components', 20),
            'random_state': ica_config.get('random_state', 42),
            'max_iter': ica_config.get('max_iter', 2000),
            'tolerance': ica_config.get('tolerance', 1e-4)
        }
    except KeyError as e:
        logger.warning(f"Missing ICA configuration key: {e}")
        # Return defaults
        return {
            'method': 'fastica',
            'n_components': 20,
            'random_state': 42,
            'max_iter': 2000,
            'tolerance': 1e-4
        }


def get_pseudocount(config: Dict[str, Any]) -> float:
    """
    Extract pseudocount value from microbiome configuration.

    Args:
        config: The loaded configuration dictionary.

    Returns:
        Pseudocount value (float).
    """
    try:
        micro_config = config['microbiome']
        return float(micro_config['pseudocount'])
    except (KeyError, ValueError) as e:
        logger.warning(f"Missing or invalid pseudocount configuration: {e}")
        return 0.5  # Default value


def get_alpha_band(config: Dict[str, Any]) -> Dict[str, float]:
    """
    Extract alpha band frequency range from configuration.

    Args:
        config: The loaded configuration dictionary.

    Returns:
        Dictionary with 'low' and 'high' frequency bounds.
    """
    try:
        eeg_config = config['eeg']
        alpha_config = eeg_config['alpha_band']
        return {
            'low': float(alpha_config['low']),
            'high': float(alpha_config['high'])
        }
    except KeyError as e:
        logger.warning(f"Missing alpha band configuration key: {e}")
        return {'low': 8.0, 'high': 13.0}


def get_epoch_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract epoching configuration.

    Args:
        config: The loaded configuration dictionary.

    Returns:
        Dictionary with epoch parameters.
    """
    try:
        eeg_config = config['eeg']
        epoch_config = eeg_config['epoch']
        return {
            'duration_minutes': epoch_config['duration_minutes'],
            'baseline_correction': epoch_config.get('baseline_correction', False),
            'reject_criteria': epoch_config.get('reject_criteria', {})
        }
    except KeyError as e:
        logger.warning(f"Missing epoch configuration key: {e}")
        return {
            'duration_minutes': 2,
            'baseline_correction': False,
            'reject_criteria': {'eeg': 100e-6, 'eog': 150e-6}
        }


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate that the configuration contains all required sections.

    Args:
        config: The loaded configuration dictionary.

    Returns:
        True if valid, False otherwise.
    """
    required_sections = ['microbiome', 'eeg', 'output']
    for section in required_sections:
        if section not in config:
            logger.error(f"Missing required configuration section: {section}")
            return False

    # Validate microbiome settings
    if 'pseudocount' not in config['microbiome']:
        logger.error("Missing 'pseudocount' in microbiome section")
        return False

    # Validate EEG settings
    eeg = config['eeg']
    if 'filter_bands' not in eeg:
        logger.error("Missing 'filter_bands' in eeg section")
        return False
    if 'ica' not in eeg:
        logger.error("Missing 'ica' in eeg section")
        return False
    if 'alpha_band' not in eeg:
        logger.error("Missing 'alpha_band' in eeg section")
        return False

    # Validate output paths
    output = config['output']
    required_outputs = [
        'microbiome_features_file',
        'eeg_features_file',
        'matched_pairs_file',
        'distribution_groups_file'
    ]
    for key in required_outputs:
        if key not in output:
            logger.error(f"Missing output path: {key}")
            return False

    logger.info("Configuration validation passed")
    return True


def main():
    """
    Command-line entry point to load and display configuration.
    """
    logging.basicConfig(level=logging.INFO)

    try:
        config = load_preprocess_config()

        if not validate_config(config):
            logger.error("Configuration validation failed")
            return 1

        # Display key parameters
        logger.info("=== Configuration Summary ===")
        logger.info(f"Pseudocount: {get_pseudocount(config)}")

        filter_bands = get_filter_bands(config)
        logger.info(f"EEG Filter: {filter_bands['low_cutoff']}-{filter_bands['high_cutoff']} Hz")

        ica = get_ica_settings(config)
        logger.info(f"ICA: {ica['n_components']} components, {ica['method']}")

        alpha = get_alpha_band(config)
        logger.info(f"Alpha Band: {alpha['low']}-{alpha['high']} Hz")

        logger.info("=== Configuration Summary End ===")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        return 1
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in configuration file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error loading configuration: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
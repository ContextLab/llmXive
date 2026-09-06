"""
Configuration Loader Module for Gut Microbiome - EEG Alpha Power Analysis

This module provides functions to load and validate preprocessing parameters
from the preprocess.yaml configuration file.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from config import get_project_root

# Configure logger
logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_CONFIG = {
    'eeg': {
        'filter_bands': {
            'low_cutoff': 0.5,
            'high_cutoff': 45.0
        },
        'ica': {
            'method': 'fastica',
            'n_components': 20,
            'random_state': 42,
            'max_iter': 500,
            'tol': 1.0e-4
        },
        'epoch': {
            'duration_minutes': 2,
            'alpha_band': {
                'low': 8.0,
                'high': 13.0
            },
            'valid_epoch_threshold': 0.80
        }
    },
    'microbiome': {
        'pseudocount': 0.5,
        'qiime2': {
            'version': '2023.5',
            'genus_level': True
        }
    },
    'matching': {
        'nearest_neighbor': {
            'n_neighbors': 5,
            'metric': 'euclidean'
        },
        'propensity_score': {
            'model_type': 'logistic',
            'caliper': 0.2
        },
        'min_matched_pairs': 10
    },
    'logging': {
        'level': 'INFO',
        'output_path': 'artifacts/preprocess.yaml'
    },
    'random_seed': 42
}


def load_preprocess_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Load preprocessing configuration from YAML file.
    
    Args:
        config_path: Path to the config file. If None, uses default location.
        
    Returns:
        Dictionary containing the configuration parameters.
        
    Raises:
        FileNotFoundError: If config file does not exist.
        yaml.YAMLError: If config file is not valid YAML.
    """
    if config_path is None:
        project_root = get_project_root()
        config_path = project_root / 'code' / 'preprocess.yaml'
    else:
        config_path = Path(config_path)
        
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
    logger.info(f"Loading configuration from {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        
    # Merge with defaults to ensure all keys exist
    merged_config = _deep_merge(DEFAULT_CONFIG, config)
    
    logger.debug("Configuration loaded successfully")
    return merged_config


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge two dictionaries.
    
    Args:
        base: Base dictionary with default values.
        override: Override dictionary with user values.
        
    Returns:
        Merged dictionary.
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
            
    return result


def get_filter_bands(config: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
    """
    Get EEG filter band cutoffs.
    
    Args:
        config: Configuration dictionary. If None, loads from file.
        
    Returns:
        Dictionary with 'low_cutoff' and 'high_cutoff' keys.
    """
    if config is None:
        config = load_preprocess_config()
        
    return {
        'low_cutoff': config['eeg']['filter_bands']['low_cutoff'],
        'high_cutoff': config['eeg']['filter_bands']['high_cutoff']
    }


def get_ica_settings(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get ICA processing settings.
    
    Args:
        config: Configuration dictionary. If None, loads from file.
        
    Returns:
        Dictionary with ICA parameters.
    """
    if config is None:
        config = load_preprocess_config()
        
    return config['eeg']['ica'].copy()


def get_pseudocount(config: Optional[Dict[str, Any]] = None) -> float:
    """
    Get the pseudocount value for microbiome data.
    
    Args:
        config: Configuration dictionary. If None, loads from file.
        
    Returns:
        Pseudocount value as float.
    """
    if config is None:
        config = load_preprocess_config()
        
    return float(config['microbiome']['pseudocount'])


def get_alpha_band(config: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
    """
    Get alpha frequency band definition.
    
    Args:
        config: Configuration dictionary. If None, loads from file.
        
    Returns:
        Dictionary with 'low' and 'high' frequency bounds.
    """
    if config is None:
        config = load_preprocess_config()
        
    return {
        'low': config['eeg']['epoch']['alpha_band']['low'],
        'high': config['eeg']['epoch']['alpha_band']['high']
    }


def get_epoch_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get epoching configuration parameters.
    
    Args:
        config: Configuration dictionary. If None, loads from file.
        
    Returns:
        Dictionary with epoch parameters.
    """
    if config is None:
        config = load_preprocess_config()
        
    return config['eeg']['epoch'].copy()


def get_matching_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get cohort matching configuration.
    
    Args:
        config: Configuration dictionary. If None, loads from file.
        
    Returns:
        Dictionary with matching parameters.
    """
    if config is None:
        config = load_preprocess_config()
        
    return config['matching'].copy()


def validate_config(config: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    Validate configuration parameters.
    
    Args:
        config: Configuration dictionary. If None, loads from file.
        
    Returns:
        List of validation error messages. Empty if valid.
    """
    if config is None:
        config = load_preprocess_config()
        
    errors = []
    
    # Validate filter bands
    filter_bands = config['eeg']['filter_bands']
    if filter_bands['low_cutoff'] >= filter_bands['high_cutoff']:
        errors.append(f"Invalid filter bands: low_cutoff ({filter_bands['low_cutoff']}) must be < high_cutoff ({filter_bands['high_cutoff']})")
        
    # Validate ICA settings
    ica = config['eeg']['ica']
    if ica['n_components'] <= 0:
        errors.append(f"Invalid ICA n_components: {ica['n_components']} must be positive")
    if ica['max_iter'] <= 0:
        errors.append(f"Invalid ICA max_iter: {ica['max_iter']} must be positive")
        
    # Validate pseudocount
    pseudocount = config['microbiome']['pseudocount']
    if pseudocount <= 0:
        errors.append(f"Invalid pseudocount: {pseudocount} must be positive")
        
    # Validate epoch settings
    epoch = config['eeg']['epoch']
    if epoch['duration_minutes'] <= 0:
        errors.append(f"Invalid epoch duration: {epoch['duration_minutes']} must be positive")
    if not (0 < epoch['valid_epoch_threshold'] <= 1):
        errors.append(f"Invalid valid_epoch_threshold: {epoch['valid_epoch_threshold']} must be in (0, 1]")
        
    # Validate alpha band
    alpha_band = epoch['alpha_band']
    if alpha_band['low'] >= alpha_band['high']:
        errors.append(f"Invalid alpha band: low ({alpha_band['low']}) must be < high ({alpha_band['high']})")
        
    # Validate matching settings
    matching = config['matching']
    if matching['nearest_neighbor']['n_neighbors'] <= 0:
        errors.append(f"Invalid n_neighbors: {matching['nearest_neighbor']['n_neighbors']} must be positive")
    if matching['min_matched_pairs'] <= 0:
        errors.append(f"Invalid min_matched_pairs: {matching['min_matched_pairs']} must be positive")
        
    return errors


def main():
    """
    Main function to demonstrate configuration loading and validation.
    """
    import sys
    
    try:
        config = load_preprocess_config()
        print("Configuration loaded successfully!")
        print(f"Filter bands: {get_filter_bands(config)}")
        print(f"ICA settings: {get_ica_settings(config)}")
        print(f"Pseudocount: {get_pseudocount(config)}")
        print(f"Alpha band: {get_alpha_band(config)}")
        print(f"Epoch config: {get_epoch_config(config)}")
        print(f"Matching config: {get_matching_config(config)}")
        
        errors = validate_config(config)
        if errors:
            print("\nValidation errors:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
        else:
            print("\nConfiguration validation passed!")
            
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"YAML Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
"""
Configuration loader for preprocessing parameters.

Reads parameters from data/processed/preprocess.yaml including:
- Filter bands (EEG preprocessing)
- ICA settings (EEG preprocessing)
- Pseudocount (Microbiome preprocessing)
"""
import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

# Import project root utility from existing config module
from config import get_project_root

logger = logging.getLogger(__name__)


def load_preprocess_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load preprocessing configuration from YAML file.
    
    Args:
        config_path: Optional path to config file. If None, uses default path
                    data/processed/preprocess.yaml relative to project root.
                    
    Returns:
        Dictionary containing configuration parameters with defaults for missing keys.
        
    Raises:
        FileNotFoundError: If config file does not exist.
        yaml.YAMLError: If config file is not valid YAML.
    """
    if config_path is None:
        project_root = get_project_root()
        config_path = project_root / "data" / "processed" / "preprocess.yaml"
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    logger.info(f"Loading preprocessing config from: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    if config is None:
        config = {}
    
    # Apply defaults for missing keys
    config = _apply_defaults(config)
    
    logger.debug(f"Loaded config: {config}")
    return config


def _apply_defaults(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply default values for missing configuration keys.
    
    Args:
        config: User-provided configuration dictionary.
                
    Returns:
        Configuration dictionary with defaults filled in.
    """
    defaults = {
        "filter_bands": {
            "low_cutoff": 0.5,
            "high_cutoff": 45.0,
            "notch_freq": 60.0
        },
        "ica_settings": {
            "n_components": 20,
            "algorithm": "fastica",
            "random_state": None,
            "max_iter": 500
        },
        "pseudocount": 0.5,
        "epoch_duration": 120,  # 2 minutes in seconds
        "valid_epoch_threshold": 0.8
    }
    
    # Merge defaults with user config (user config takes precedence)
    merged = defaults.copy()
    
    for key, value in config.items():
        if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
            merged[key].update(value)
        else:
            merged[key] = value
    
    return merged


def get_filter_bands(config: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
    """
    Extract filter band parameters from configuration.
    
    Args:
        config: Optional config dictionary. If None, loads from default path.
                
    Returns:
        Dictionary with keys: low_cutoff, high_cutoff, notch_freq
    """
    if config is None:
        config = load_preprocess_config()
    
    return {
        "low_cutoff": float(config["filter_bands"]["low_cutoff"]),
        "high_cutoff": float(config["filter_bands"]["high_cutoff"]),
        "notch_freq": float(config["filter_bands"]["notch_freq"])
    }


def get_ica_settings(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extract ICA settings from configuration.
    
    Args:
        config: Optional config dictionary. If None, loads from default path.
                
    Returns:
        Dictionary with keys: n_components, algorithm, random_state, max_iter
    """
    if config is None:
        config = load_preprocess_config()
    
    ica = config["ica_settings"]
    return {
        "n_components": int(ica["n_components"]),
        "algorithm": str(ica["algorithm"]),
        "random_state": ica["random_state"],
        "max_iter": int(ica["max_iter"])
    }


def get_pseudocount(config: Optional[Dict[str, Any]] = None) -> float:
    """
    Extract pseudocount value from configuration.
    
    Args:
        config: Optional config dictionary. If None, loads from default path.
                
    Returns:
        Float pseudocount value.
    """
    if config is None:
        config = load_preprocess_config()
    
    return float(config["pseudocount"])


def validate_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate configuration parameters and return list of validation errors.
    
    Args:
        config: Configuration dictionary to validate.
                
    Returns:
        List of error messages. Empty if validation passes.
    """
    errors = []
    
    # Validate filter bands
    if "filter_bands" in config:
        fb = config["filter_bands"]
        if "low_cutoff" in fb and fb["low_cutoff"] < 0:
            errors.append("filter_bands.low_cutoff must be non-negative")
        if "high_cutoff" in fb and "low_cutoff" in fb:
            if fb["high_cutoff"] <= fb["low_cutoff"]:
                errors.append("filter_bands.high_cutoff must be greater than low_cutoff")
    
    # Validate ICA settings
    if "ica_settings" in config:
        ica = config["ica_settings"]
        if "n_components" in ica and ica["n_components"] <= 0:
            errors.append("ica_settings.n_components must be positive")
        if "max_iter" in ica and ica["max_iter"] <= 0:
            errors.append("ica_settings.max_iter must be positive")
    
    # Validate pseudocount
    if "pseudocount" in config:
        if config["pseudocount"] < 0:
            errors.append("pseudocount must be non-negative")
    
    return errors


def main():
    """
    CLI entry point to load and display configuration.
    """
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        config = load_preprocess_config()
        print("Loaded Configuration:")
        print("-" * 40)
        
        print(f"Filter Bands:")
        fb = config["filter_bands"]
        print(f"  Low Cutoff: {fb['low_cutoff']} Hz")
        print(f"  High Cutoff: {fb['high_cutoff']} Hz")
        print(f"  Notch Freq: {fb['notch_freq']} Hz")
        
        print(f"\nICA Settings:")
        ica = config["ica_settings"]
        print(f"  Components: {ica['n_components']}")
        print(f"  Algorithm: {ica['algorithm']}")
        print(f"  Random State: {ica['random_state']}")
        print(f"  Max Iter: {ica['max_iter']}")
        
        print(f"\nPseudocount: {config['pseudocount']}")
        
        errors = validate_config(config)
        if errors:
            print(f"\nValidation Errors ({len(errors)}):")
            for err in errors:
                print(f"  - {err}")
            sys.exit(1)
        else:
            print("\nConfiguration validation: PASSED")
            
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nCreate a default config file at: data/processed/preprocess.yaml")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

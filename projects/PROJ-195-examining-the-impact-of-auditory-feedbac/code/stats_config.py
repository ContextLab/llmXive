"""
Statistics Configuration for Motor Sequence Learning Analysis.

This module defines the GLM parameters, FDR thresholds, and ROI definitions
required for the statistical analysis pipeline. It serves as the single source
of truth for statistical thresholds and model settings.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent

# Path to the configuration file
CONFIG_PATH = PROJECT_ROOT / "specs" / "stats_config.yaml"

def load_config() -> Dict[str, Any]:
    """
    Load the statistical configuration from the YAML file.
    
    Returns:
        Dict containing all configuration parameters.
        
    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the config file is malformed.
    """
    if not CONFIG_PATH.exists():
        # Create default config if it doesn't exist
        return _create_default_config()
        
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def _create_default_config() -> Dict[str, Any]:
    """
    Create and save a default configuration file if one doesn't exist.
    
    Returns:
        Dict containing the default configuration.
    """
    default_config = {
        "glm": {
            "first_level": {
                "high_pass_filter": 128.0,  # seconds
                "smoothing_fwhm": 6.0,      # mm
                "model_type": "AR(1)",
                "noise_model": "ar1",
                "standardize": True,
                "drift_model": "cosine"
            },
            "group_level": {
                "model_type": "fixed_effect",
                "noise_model": "ols"
            }
        },
        "thresholding": {
            "fdr_q": 0.05,
            "cluster_formation_p": 0.001,
            "cluster_extent_k": 10,  # voxels
            "global_p_uncorrected": 0.10  # For pilot adjustments (SC-002)
        },
        "roi": {
            "auditory_cortex": {
                "path": "roi_masks/auditory_cortex.nii.gz",
                "atlas": "Harvard-Oxford",
                "label": "Auditory Cortex",
                "threshold": 0
            },
            "motor_cortex": {
                "path": "roi_masks/motor_cortex.nii.gz",
                "atlas": "Harvard-Oxford",
                "label": "Motor Cortex",
                "threshold": 0
            }
        },
        "behavioral": {
            "learning_rate": {
                "method": "ols_slope",
                "min_trials": 5,
                "outlier_threshold": 3.0  # Standard deviations
            },
            "correlation": {
                "method": "pearson",
                "alpha": 0.05
            }
        }
    }
    
    # Ensure specs directory exists
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Save the default config
    with open(CONFIG_PATH, 'w') as f:
        yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)
        
    return default_config

def get_glm_params() -> Dict[str, Any]:
    """Get GLM parameters from configuration."""
    config = load_config()
    return config.get("glm", {})

def get_fdr_threshold() -> float:
    """Get the FDR q-value threshold."""
    config = load_config()
    return config.get("thresholding", {}).get("fdr_q", 0.05)

def get_cluster_threshold() -> int:
    """Get the minimum cluster size in voxels."""
    config = load_config()
    return config.get("thresholding", {}).get("cluster_extent_k", 10)

def get_roi_path(roi_name: str = "auditory_cortex") -> Path:
    """
    Get the full path to an ROI mask file.
    
    Args:
        roi_name: Name of the ROI (e.g., 'auditory_cortex')
        
    Returns:
        Path object pointing to the ROI mask file.
    """
    config = load_config()
    roi_config = config.get("roi", {}).get(roi_name, {})
    relative_path = roi_config.get("path", f"roi_masks/{roi_name}.nii.gz")
    return PROJECT_ROOT / relative_path

def get_global_p_threshold() -> float:
    """
    Get the global p-value threshold for uncorrected maps.
    Used when no clusters survive FDR (SC-002).
    """
    config = load_config()
    return config.get("thresholding", {}).get("global_p_uncorrected", 0.10)

def validate_config() -> bool:
    """
    Validate that all required configuration parameters are present.
    
    Returns:
        True if configuration is valid, False otherwise.
    """
    config = load_config()
    required_sections = ["glm", "thresholding", "roi"]
    
    for section in required_sections:
        if section not in config:
            return False
            
    # Check critical thresholds
    if config["thresholding"].get("fdr_q") is None:
        return False
        
    return True

if __name__ == "__main__":
    # Test the configuration loading
    import json
    
    print("Loading statistical configuration...")
    config = load_config()
    
    print("\n=== GLM Parameters ===")
    print(json.dumps(config.get("glm", {}), indent=2))
    
    print("\n=== Thresholding ===")
    print(json.dumps(config.get("thresholding", {}), indent=2))
    
    print("\n=== ROI Definitions ===")
    print(json.dumps(config.get("roi", {}), indent=2))
    
    print(f"\nConfiguration valid: {validate_config()}")
    print(f"FDR q-value: {get_fdr_threshold()}")
    print(f"Global p-threshold: {get_global_p_threshold()}")
    print(f"Auditory Cortex ROI path: {get_roi_path('auditory_cortex')}")

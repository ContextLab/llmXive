"""
Configuration loader for the llmXive meta-analysis simulation project.
Parses code/config.yaml and provides typed access to configuration values.
Handles FileNotFoundError from data fetch and triggers fallback logic.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from utils.logging import get_logger

logger = get_logger(__name__)

CONFIG_PATH = Path("code/config.yaml")

def load_config() -> Dict[str, Any]:
    """
    Load and parse the configuration file.
    
    Returns:
        Dict containing all configuration parameters.
        
    Raises:
        FileNotFoundError: If config.yaml is missing.
        yaml.YAMLError: If config.yaml is malformed.
    """
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Configuration file not found: {CONFIG_PATH}")
    
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    logger.info(f"Configuration loaded from {CONFIG_PATH}")
    return config

def get_simulation_params(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extract simulation parameters from config.
    
    Args:
        config: Optional pre-loaded config dict. If None, loads from file.
        
    Returns:
        Dict with replicate_counts, tau2_levels, and random_seed.
    """
    if config is None:
        config = load_config()
    
    return config.get("simulation_parameters", {})

def get_data_source_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extract data source configuration.
    
    Args:
        config: Optional pre-loaded config dict.
        
    Returns:
        Dict with data source type and paths.
    """
    if config is None:
        config = load_config()
    
    return config.get("data_source", {})

def get_base_data_path(config: Optional[Dict[str, Any]] = None) -> Path:
    """
    Determine the path to the base data file.
    
    This function implements the fallback logic:
    1. Check if real data exists (cochrane_base.csv)
    2. If not, check if synthetic base exists
    3. If neither exists, raise FileNotFoundError to trigger fallback generation
    
    Args:
        config: Optional pre-loaded config dict.
        
    Returns:
        Path to the base data file.
        
    Raises:
        FileNotFoundError: If no valid base data is found.
    """
    if config is None:
        config = load_config()
    
    data_source = get_data_source_config(config)
    data_type = data_source.get("type", "synthetic")
    
    # Check for real Cochrane data first
    cochrane_path = Path("data/raw/cochrane_base.csv")
    synthetic_path = Path(data_source.get("synthetic_file", "data/raw/cochrane_base_synthetic.csv"))
    
    if data_type == "cochrane":
        if cochrane_path.exists():
            logger.info(f"Using real Cochrane data from {cochrane_path}")
            return cochrane_path
        else:
            # Real data requested but not found - trigger fallback
            logger.warning(f"Cochrane data not found at {cochrane_path}. Falling back to synthetic.")
            if synthetic_path.exists():
                logger.info(f"Using synthetic base from {synthetic_path}")
                return synthetic_path
            else:
                raise FileNotFoundError(
                    f"REAL_DATA_FETCH_FAILED: Neither Cochrane data ({cochrane_path}) "
                    f"nor synthetic base ({synthetic_path}) found. "
                    f"Please run fetch_cochrane.py or generate_synthetic_base.py."
                )
    else:
        # Synthetic path
        if synthetic_path.exists():
            logger.info(f"Using synthetic base from {synthetic_path}")
            return synthetic_path
        else:
            raise FileNotFoundError(
                f"REAL_DATA_FETCH_FAILED: Synthetic base not found at {synthetic_path}. "
                f"Please run generate_synthetic_base.py."
            )

def get_nominal_confidence_level(config: Optional[Dict[str, Any]] = None) -> float:
    """
    Get the nominal confidence level for coverage calculations.
    
    Args:
        config: Optional pre-loaded config dict.
        
    Returns:
        Confidence level as float (e.g., 0.95).
    """
    if config is None:
        config = load_config()
    
    return float(config.get("nominal_confidence_level", 0.95))

def get_min_studies_for_reliability(config: Optional[Dict[str, Any]] = None) -> int:
    """
    Get the minimum number of studies for reliability flag.
    
    Args:
        config: Optional pre-loaded config dict.
        
    Returns:
        Minimum study count as integer.
    """
    if config is None:
        config = load_config()
    
    return int(config.get("min_studies_for_reliability", 5))

def get_significance_level(config: Optional[Dict[str, Any]] = None) -> float:
    """
    Get the significance level for hypothesis tests.
    
    Args:
        config: Optional pre-loaded config dict.
        
    Returns:
        Significance level as float (e.g., 0.05).
    """
    if config is None:
        config = load_config()
    
    return float(config.get("significance_level", 0.05))

def get_replicate_count(purpose: str = "primary_sweep", config: Optional[Dict[str, Any]] = None) -> int:
    """
    Get the replicate count for a specific purpose.
    
    Args:
        purpose: One of "primary_sweep", "sensitivity_sweep", or "test_replicates".
        config: Optional pre-loaded config dict.
        
    Returns:
        Number of replicates as integer.
    """
    if config is None:
        config = load_config()
    
    sim_params = get_simulation_params(config)
    replicate_counts = sim_params.get("replicate_counts", {})
    
    return int(replicate_counts.get(purpose, 500))

def get_tau2_levels(config: Optional[Dict[str, Any]] = None) -> List[float]:
    """
    Get the list of tau^2 heterogeneity levels.
    
    Args:
        config: Optional pre-loaded config dict.
        
    Returns:
        List of tau^2 values.
    """
    if config is None:
        config = load_config()
    
    sim_params = get_simulation_params(config)
    return [float(x) for x in sim_params.get("tau2_levels", [0.0, 0.1, 0.5, 1.0, 2.0])]

def get_random_seed(config: Optional[Dict[str, Any]] = None) -> int:
    """
    Get the random seed for reproducibility.
    
    Args:
        config: Optional pre-loaded config dict.
        
    Returns:
        Random seed as integer.
    """
    if config is None:
        config = load_config()
    
    sim_params = get_simulation_params(config)
    return int(sim_params.get("random_seed", 42))

def get_synthetic_base_params(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get synthetic base generation parameters.
    
    Args:
        config: Optional pre-loaded config dict.
        
    Returns:
        Dict with synthetic base parameters.
    """
    if config is None:
        config = load_config()
    
    return config.get("synthetic_base_params", {})

def validate_config(config: Optional[Dict[str, Any]] = None) -> bool:
    """
    Validate that all required configuration fields are present.
    
    Args:
        config: Optional pre-loaded config dict.
        
    Returns:
        True if valid, raises ValueError otherwise.
    """
    if config is None:
        config = load_config()
    
    required_fields = [
        "nominal_confidence_level",
        "min_studies_for_reliability",
        "significance_level",
        "simulation_parameters"
    ]
    
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required configuration field: {field}")
    
    sim_params = config["simulation_parameters"]
    required_sim_fields = ["replicate_counts", "tau2_levels", "random_seed"]
    
    for field in required_sim_fields:
        if field not in sim_params:
            raise ValueError(f"Missing required simulation parameter: {field}")
    
    logger.info("Configuration validation passed")
    return True

def main():
    """
    CLI entry point for testing configuration loading.
    """
    try:
        config = load_config()
        validate_config(config)
        
        print("Configuration loaded successfully:")
        print(f"  Nominal confidence level: {get_nominal_confidence_level(config)}")
        print(f"  Min studies for reliability: {get_min_studies_for_reliability(config)}")
        print(f"  Significance level: {get_significance_level(config)}")
        print(f"  Tau^2 levels: {get_tau2_levels(config)}")
        print(f"  Replicate counts: {get_simulation_params(config).get('replicate_counts', {})}")
        print(f"  Random seed: {get_random_seed(config)}")
        
        # Test base data path resolution
        try:
            base_path = get_base_data_path(config)
            print(f"  Base data path: {base_path}")
        except FileNotFoundError as e:
            print(f"  Base data not found (expected for fresh setup): {e}")
        
        return 0
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
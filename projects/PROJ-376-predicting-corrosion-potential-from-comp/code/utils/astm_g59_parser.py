import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import yaml
from utils.logging import get_logger
from utils.exceptions import DataInsufficientError

logger = get_logger(__name__)

def load_astm_tolerance_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the ASTM G59 tolerance configuration from the YAML file.
    
    Args:
        config_path: Path to the config file. Defaults to config/astm_g59_tolerance.yaml.
        
    Returns:
        Dictionary containing the configuration.
        
    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    if config_path is None:
        config_path = "config/astm_g59_tolerance.yaml"
    
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"ASTM G59 tolerance config not found at {config_path}")
    
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    
    logger.info(f"Loaded ASTM G59 tolerance config from {config_path}")
    return config

def get_tolerance_value(config: Dict[str, Any], tolerance_type: str = "absolute") -> Optional[float]:
    """
    Extract the tolerance value from the configuration.
    
    Args:
        config: The loaded configuration dictionary.
        tolerance_type: Either "absolute" (returns absolute_tolerance_mv) or 
                        "relative" (returns relative_tolerance_percent).
                        
    Returns:
        The tolerance value if found, None otherwise.
        
    Raises:
        DataInsufficientError: If the requested tolerance type is required but not defined 
                               in the standard (i.e., absolute_tolerance_mv is null when 
                               an absolute value is needed).
    """
    if tolerance_type == "absolute":
        value = config.get("absolute_tolerance_mv")
        # If the standard does not define an absolute value (it's null), and we need it,
        # we must raise an error as per SC-002.
        if value is None:
            source = config.get("tolerance_source", "Unknown")
            logger.error(f"ASTM G59 standard ({source}) does not define a specific absolute tolerance value.")
            raise DataInsufficientError(
                "ASTM G59 standard does not define a specific absolute prediction error tolerance in mV. "
                "The pipeline cannot proceed with absolute tolerance comparison. "
                "Refer to config/astm_g59_tolerance.yaml for details."
            )
        return value
    
    elif tolerance_type == "relative":
        value = config.get("relative_tolerance_percent")
        if value is None:
            logger.warning("Relative tolerance percent is not defined in config.")
            return None
        return value
    
    else:
        raise ValueError(f"Unknown tolerance_type: {tolerance_type}. Must be 'absolute' or 'relative'.")

def get_tolerance_source_info(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get metadata about the tolerance source.
    
    Args:
        config: The loaded configuration dictionary.
        
    Returns:
        Dictionary with source metadata.
    """
    return {
        "source": config.get("tolerance_source"),
        "section": config.get("section_reference"),
        "defined_absolute": config.get("defined_in_standard", {}).get("absolute_tolerance_mv", False),
        "defined_relative": config.get("defined_in_standard", {}).get("relative_tolerance_percent", False)
    }

def validate_tolerance_for_comparison(config: Dict[str, Any], comparison_mode: str = "absolute") -> Tuple[bool, str]:
    """
    Validate if the tolerance configuration is sufficient for the requested comparison mode.
    
    Args:
        config: The loaded configuration dictionary.
        comparison_mode: "absolute" or "relative".
                        
    Returns:
        Tuple of (is_valid, message).
    """
    if comparison_mode == "absolute":
        if config.get("absolute_tolerance_mv") is None:
            return False, "Absolute tolerance is required but not defined in ASTM G59 standard."
        return True, f"Absolute tolerance of {config['absolute_tolerance_mv']} mV is available."
    
    elif comparison_mode == "relative":
        if config.get("relative_tolerance_percent") is None:
            return False, "Relative tolerance is required but not defined."
        return True, f"Relative tolerance of {config['relative_tolerance_percent']}% is available."
    
    else:
        return False, f"Unknown comparison mode: {comparison_mode}"

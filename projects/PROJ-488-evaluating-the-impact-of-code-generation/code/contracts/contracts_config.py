"""
Contracts Configuration Module

Provides configuration settings for contract validation
across the pipeline.
"""

from typing import Dict, Any

# Default configuration for contract validation
DEFAULT_CONFIG = {
    'strict_mode': True,
    'log_violations': True,
    'raise_on_violation': True,
    'validation_timeout_seconds': 30,
    
    # Data contract defaults
    'data_contracts': {
        'require_all_fields': True,
        'allow_extra_fields': False,
        'strict_type_checking': True
    },
    
    # API contract defaults
    'api_contracts': {
        'require_type_annotations': True,
        'validate_return_types': True
    },
    
    # Validation contract defaults
    'validation_contracts': {
        'precondition_check': True,
        'postcondition_check': True,
        'log_timing': True
    },
    
    # Thresholds
    'thresholds': {
        'min_sample_count': 100,
        'max_nan_percentage': 0.0,
        'valid_score_range': (0, float('inf'))
    }
}


def get_contract_config() -> Dict[str, Any]:
    """
    Get the current contract configuration.
    
    Returns:
        Dict containing all contract configuration settings
    """
    return DEFAULT_CONFIG.copy()


def update_contract_config(updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update contract configuration with provided values.
    
    Args:
        updates: Dict of configuration updates
    
    Returns:
        Updated configuration dict
    """
    global DEFAULT_CONFIG
    
    def deep_update(base: Dict, updates: Dict) -> Dict:
        """Recursively update nested dictionaries."""
        result = base.copy()
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_update(result[key], value)
            else:
                result[key] = value
        return result
    
    DEFAULT_CONFIG = deep_update(DEFAULT_CONFIG, updates)
    return DEFAULT_CONFIG

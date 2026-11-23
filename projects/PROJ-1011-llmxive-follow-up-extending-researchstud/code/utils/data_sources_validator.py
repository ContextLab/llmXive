"""
Data Sources Configuration Validator
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from utils.error_handling import ValidationError

def validate_url_format(url: str) -> bool:
    """Validate that a string is a valid URL format."""
    pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return pattern.match(url) is not None

def validate_endpoint(endpoint: Dict[str, Any]) -> bool:
    """Validate an endpoint configuration."""
    if "url" not in endpoint and "category" not in endpoint and "dois" not in endpoint:
        return False
    if "url" in endpoint and not validate_url_format(endpoint["url"]):
        return False
    return True

def validate_source(source: Dict[str, Any]) -> bool:
    """Validate a source configuration."""
    if not isinstance(source, dict):
        return False
    # Check for required fields based on source type
    if "category" in source:
        return "description" in source
    if "dois" in source:
        return "name" in source and isinstance(source["dois"], list)
    if "url" in source:
        return validate_url_format(source["url"])
    return False

def validate_data_sources_config(config: Dict[str, Any]) -> bool:
    """Validate the entire data sources configuration."""
    if "sources" not in config:
        raise ValidationError("Configuration missing 'sources' key")
    
    sources = config["sources"]
    required_keys = ["ml", "non_ml_accepted", "non_ml_rejected"]
    
    for key in required_keys:
        if key not in sources:
            raise ValidationError(f"Configuration missing source category: {key}")
        
        if not isinstance(sources[key], list):
            raise ValidationError(f"Source category '{key}' must be a list")
        
        for i, item in enumerate(sources[key]):
            if not validate_source(item):
                raise ValidationError(f"Invalid source at index {i} in '{key}'")
    
    return True

def load_and_validate_config(config_path: str = "data/data-sources.yaml") -> Dict[str, Any]:
    """Load and validate the data sources configuration file."""
    path = Path(config_path)
    if not path.exists():
        raise ValidationError(f"Config file not found: {config_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    validate_data_sources_config(config)
    return config

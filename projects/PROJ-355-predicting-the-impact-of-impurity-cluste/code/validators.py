import os
import requests
from pathlib import Path
from typing import List, Optional
import yaml
import logging

logger = logging.getLogger(__name__)

VALIDATED_SOURCE_WHITELIST = [
    'https://materialsproject.org',
    'https://oqmd.org'
]

def validate_citations(url: str, metadata_path: str) -> bool:
    """
    Validate citations against a whitelist and check URL reachability.
    
    Args:
        url: The URL to validate.
        metadata_path: Path to the metadata YAML file.
    
    Returns:
        bool: True if valid, False otherwise (raises ValueError on failure).
    
    Raises:
        ValueError: If the URL is not in the whitelist or is unreachable.
    """
    if not url:
        logger.error("URL is empty.")
        raise ValueError("[DATA_UNAVAILABLE] URL=")

    # Check whitelist
    is_whitelisted = any(url.startswith(allowed) for allowed in VALIDATED_SOURCE_WHITELIST)
    
    if not is_whitelisted:
        error_msg = f"[DATA_UNAVAILABLE] URL={url}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Check reachability via HTTP HEAD
    try:
        response = requests.head(url, timeout=10)
        if response.status_code >= 400:
            error_msg = f"[DATA_UNAVAILABLE] URL={url}"
            logger.error(f"URL returned status code {response.status_code}")
            raise ValueError(error_msg)
    except requests.RequestException as e:
        error_msg = f"[DATA_UNAVAILABLE] URL={url}"
        logger.error(f"Failed to reach URL: {e}")
        raise ValueError(error_msg)

    logger.info(f"URL validated successfully: {url}")
    return True

def validate_schema(data: dict, schema_path: str) -> bool:
    """
    Validate data against a JSON schema.
    
    Args:
        data: The data to validate.
        schema_path: Path to the schema file.
    
    Returns:
        bool: True if valid.
    
    Raises:
        ValueError: If validation fails.
    """
    # Simple placeholder for schema validation logic
    # In a real implementation, use jsonschema library
    if not schema_path:
        raise ValueError("Schema path is required")
    
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    # Basic check: ensure data is a dict
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")
        
    logger.info("Schema validation passed (basic check).")
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Test logic here if needed
    pass
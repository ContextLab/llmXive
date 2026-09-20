import os
import requests
from pathlib import Path
from typing import List, Optional
import yaml
import logging

logger = logging.getLogger(__name__)

# Whitelist of allowed data source domains
VALIDATED_SOURCE_WHITELIST = [
    'https://materialsproject.org',
    'https://oqmd.org'
]

def validate_citations(url: str, metadata_path: str) -> bool:
    """
    Validate citations against a whitelist and check URL reachability.
    
    This function implements the mandatory Reference-Validator Agent logic
    required by FR-001 and Constitution Principle II.
    
    Args:
        url: The URL to validate.
        metadata_path: Path to the metadata YAML file (used to extract context if needed, 
                       though validation is performed on the provided URL).
    
    Returns:
        bool: True if the URL is valid and reachable.
    
    Raises:
        ValueError: If the URL is not in the whitelist or is unreachable.
                    The error message follows the format: [DATA_UNAVAILABLE] URL=<url>
    """
    if not url:
        logger.error("URL is empty.")
        raise ValueError("[DATA_UNAVAILABLE] URL=")

    # Check if URL starts with any of the whitelisted domains
    is_whitelisted = any(url.startswith(allowed) for allowed in VALIDATED_SOURCE_WHITELIST)
    
    if not is_whitelisted:
        error_msg = f"[DATA_UNAVAILABLE] URL={url}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Verify URL existence via HTTP HEAD request
    try:
        # Use a reasonable timeout to avoid hanging on unreachable hosts
        response = requests.head(url, timeout=10, allow_redirects=True)
        
        # Check for successful response (status code < 400)
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
    Validate data against a YAML schema.
    
    Args:
        data: The data to validate (dictionary).
        schema_path: Path to the schema file.
    
    Returns:
        bool: True if valid.
    
    Raises:
        ValueError: If validation fails.
        FileNotFoundError: If schema file is not found.
    """
    if not schema_path:
        raise ValueError("Schema path is required")
    
    schema_file = Path(schema_path)
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    # Basic check: ensure data is a dict
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")
        
    # Load schema and perform basic field validation
    try:
        with open(schema_file, 'r') as f:
            schema = yaml.safe_load(f)
        
        # Check if schema defines required fields
        if 'required' in schema:
            required_fields = schema['required']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")
                
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid schema format: {e}")
    
    logger.info("Schema validation passed.")
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Example usage for manual testing
    # test_url = "https://materialsproject.org/materials/mp-123"
    # test_metadata = "data/metadata.yaml"
    # try:
    #     result = validate_citations(test_url, test_metadata)
    #     print(f"Validation result: {result}")
    # except ValueError as e:
    #     print(f"Validation failed: {e}")
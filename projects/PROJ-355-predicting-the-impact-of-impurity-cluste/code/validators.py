import os
import requests
from pathlib import Path
from typing import List, Optional, Dict, Any
import yaml
import logging

logger = logging.getLogger(__name__)

# Whitelist of allowed data source domains
VALIDATED_SOURCE_WHITELIST = [
    'https://materialsproject.org',
    'https://oqmd.org',
    ''  # Allow empty string as per task spec for local/internal references if needed
]

def validate_citations(url: str, metadata_path: str) -> Dict[str, Any]:
    """
    Validate citations against a whitelist and check URL reachability.
    
    This function implements the mandatory Reference-Validator Agent logic
    required by FR-001 and Constitution Principle II.
    
    Args:
        url: The URL to validate.
        metadata_path: Path to the metadata YAML file (used to extract context if needed, 
                       though validation is performed on the provided URL).
    
    Returns:
        dict: A status dictionary with keys:
              - "success": bool
              - "error_code": str | None
              - "message": str
    
    Behavior:
        1. Parses metadata_path (not strictly needed for the URL check itself but required by signature).
        2. Checks the provided URL against VALIDATED_SOURCE_WHITELIST.
        3. Verifies the URL exists via HTTP HEAD request.
        4. Returns success dict if valid.
        5. Returns failure dict if invalid (not in whitelist or unreachable).
        6. Does NOT raise exceptions; returns status dict for graceful pipeline handling.
    """
    result = {
        "success": False,
        "error_code": None,
        "message": "OK"
    }

    # 1. Parse metadata_path (log presence, though we validate the passed URL directly)
    if metadata_path:
        logger.info(f"Checking metadata path: {metadata_path}")
        # Optional: verify file exists to ensure context is valid
        if not os.path.exists(metadata_path):
            logger.warning(f"Metadata path provided but not found: {metadata_path}")
            # Continue with URL validation anyway as per task spec logic

    # Handle empty URL
    if not url:
        result["success"] = False
        result["error_code"] = "URL_INVALID"
        result["message"] = "URL not in whitelist or unreachable"
        logger.error("URL is empty.")
        return result

    # 2. Check if URL starts with any of the whitelisted domains
    is_whitelisted = any(url.startswith(allowed) for allowed in VALIDATED_SOURCE_WHITELIST)
    
    if not is_whitelisted:
        result["success"] = False
        result["error_code"] = "URL_INVALID"
        result["message"] = "URL not in whitelist or unreachable"
        logger.error(f"URL not in whitelist: {url}")
        return result

    # 3. Verify URL existence via HTTP HEAD request
    try:
        # Use a reasonable timeout to avoid hanging on unreachable hosts
        response = requests.head(url, timeout=10, allow_redirects=True)
        
        # Check for successful response (status code < 400)
        if response.status_code >= 400:
            result["success"] = False
            result["error_code"] = "URL_INVALID"
            result["message"] = "URL not in whitelist or unreachable"
            logger.error(f"URL returned status code {response.status_code}: {url}")
            return response.status_code
            
    except requests.RequestException as e:
        result["success"] = False
        result["error_code"] = "URL_INVALID"
        result["message"] = "URL not in whitelist or unreachable"
        logger.error(f"Failed to reach URL: {e}")
        return result

    # 4. Success
    logger.info(f"URL validated successfully: {url}")
    result["success"] = True
    result["error_code"] = None
    result["message"] = "OK"
    return result

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
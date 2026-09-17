"""
Utility functions for API requests, validation, and logging.

This module provides shared utilities used across the pipeline.
"""

import json
import logging
import os
import random
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_json_schema(data: Dict[str, Any], schema_path: Union[str, Path]) -> bool:
    """
    Validate data against a JSON schema definition.
    
    Args:
        data: Dictionary to validate
        schema_path: Path to the schema file (YAML or JSON)
    
    Returns:
        True if valid, False otherwise
    
    Note:
        This is a simplified validator. For production use, consider jsonschema library.
    """
    try:
        schema_file = Path(schema_path)
        if not schema_file.exists():
            logger.error(f"Schema file not found: {schema_path}")
            return False
        
        # Load schema (simple JSON/YAML support)
        with open(schema_file, 'r', encoding='utf-8') as f:
            if schema_file.suffix == '.yaml' or schema_file.suffix == '.yml':
                try:
                    import yaml
                    schema = yaml.safe_load(f)
                except ImportError:
                    logger.error("PyYAML not installed. Cannot parse YAML schema.")
                    return False
            else:
                schema = json.load(f)
        
        # Basic validation: check required fields
        required_fields = schema.get('required', [])
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Check types for known fields
        properties = schema.get('properties', {})
        for field, definition in properties.items():
            if field in data:
                expected_type = definition.get('type')
                value = data[field]
                
                type_valid = True
                if expected_type == 'string' and not isinstance(value, str):
                    type_valid = False
                elif expected_type == 'number' and not isinstance(value, (int, float)):
                    type_valid = False
                elif expected_type == 'array' and not isinstance(value, list):
                    type_valid = False
                elif expected_type == 'object' and not isinstance(value, dict):
                    type_valid = False
                
                if not type_valid:
                    logger.warning(f"Invalid type for field {field}: expected {expected_type}, got {type(value)}")
                    return False
        
        logger.debug(f"Data validated successfully against schema: {schema_path}")
        return True
        
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        return False

def api_request_with_backoff(
    url: str, 
    headers: Dict[str, str],
    base_delay: float = 1.0,
    multiplier: float = 2.0,
    max_delay: float = 60.0,
    max_retries: int = 5
) -> Optional[requests.Response]:
    """
    Make an API request with exponential backoff for rate limits.
    
    Args:
        url: Target URL
        headers: Request headers
        base_delay: Initial delay in seconds
        multiplier: Delay multiplier for backoff
        max_delay: Maximum delay cap
        max_retries: Maximum number of retry attempts
    
    Returns:
        Response object if successful, None otherwise
    
    Note:
        Captures rate limit headers (X-RateLimit-Remaining, X-RateLimit-Reset)
        for logging purposes.
    """
    delay = base_delay
    last_response = None
    
    for attempt in range(max_retries + 1):
        try:
            logger.debug(f"API request attempt {attempt + 1}/{max_retries + 1}: {url}")
            response = requests.get(url, headers=headers, timeout=30)
            
            # Capture rate limit headers
            remaining = response.headers.get('X-RateLimit-Remaining', 'unknown')
            reset_time = response.headers.get('X-RateLimit-Reset', 'unknown')
            logger.info(f"Rate limit status - Remaining: {remaining}, Reset: {reset_time}")
            
            # Check for rate limit
            if response.status_code == 403 and 'rate limit' in response.text.lower():
                logger.warning(f"Rate limit hit. Waiting {delay:.1f}s before retry...")
                last_response = response
                time.sleep(delay)
                delay = min(delay * multiplier + random.uniform(0, delay * 0.5), max_delay)
                continue
            
            # Success or permanent error
            return response
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
            if attempt == max_retries:
                return None
            
            time.sleep(delay)
            delay = min(delay * multiplier + random.uniform(0, delay * 0.5), max_delay)
    
    logger.error(f"API request failed after {max_retries} retries: {url}")
    return last_response

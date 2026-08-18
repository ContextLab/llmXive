import json
import logging
import os
import random
import time
from pathlib import Path
from typing import Optional, Dict, Any

import requests

logger = logging.getLogger(__name__)

def validate_json_schema(data: Any, schema_path: str) -> bool:
    """
    Validate data against a JSON schema file.
    
    Args:
        data: Data to validate
        schema_path: Path to schema file
        
    Returns:
        True if valid, False otherwise
    """
    try:
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        # Basic validation - check required fields
        if schema.get("required"):
            for field in schema["required"]:
                if field not in data:
                    logger.error(f"Missing required field: {field}")
                    return False
        
        # Check types for properties
        properties = schema.get("properties", {})
        for field, type_def in properties.items():
            if field in data:
                expected_type = type_def.get("type")
                if expected_type == "string" and not isinstance(data[field], str):
                    logger.error(f"Field {field} should be string")
                    return False
                elif expected_type == "number" and not isinstance(data[field], (int, float)):
                    logger.error(f"Field {field} should be number")
                    return False
                elif expected_type == "array" and not isinstance(data[field], list):
                    logger.error(f"Field {field} should be array")
                    return False
        
        return True
        
    except Exception as e:
        logger.error(f"Schema validation error: {e}")
        return False

def api_request_with_backoff(
    url: str, 
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None
) -> Optional[Dict[str, Any]]:
    """
    Make API request with exponential backoff and jitter.
    
    Args:
        url: API endpoint URL
        params: Query parameters
        headers: Request headers
        
    Returns:
        Response JSON or None on failure
    """
    base_delay = 1.0
    max_delay = 60.0
    multiplier = 2.0
    max_retries = 5
    
    if headers is None:
        headers = {}
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            # Capture rate limit headers
            if "X-RateLimit-Remaining" in response.headers:
                remaining = int(response.headers["X-RateLimit-Remaining"])
                reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                logger.debug(f"Rate limit: {remaining} remaining, resets at {reset_time}")
                
                if remaining < 10:
                    logger.warning(f"Approaching rate limit: {remaining} remaining")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                # Rate limited
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
            elif response.status_code >= 500:
                # Server error, retry
                delay = min(base_delay * (multiplier ** attempt) * (1 + random.uniform(0, 0.5)), max_delay)
                logger.warning(f"Server error {response.status_code}. Retrying in {delay:.2f}s...")
                time.sleep(delay)
            else:
                logger.error(f"API request failed with status {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            delay = min(base_delay * (multiplier ** attempt) * (1 + random.uniform(0, 0.5)), max_delay)
            logger.warning(f"Request error: {e}. Retrying in {delay:.2f}s...")
            time.sleep(delay)
    
    logger.error(f"Failed after {max_retries} attempts")
    return None

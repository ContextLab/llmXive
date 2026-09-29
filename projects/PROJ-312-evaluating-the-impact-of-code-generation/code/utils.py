import json
import logging
import os
import random
import time
from typing import Any, Dict, Optional
import yaml
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MIN_PR_THRESHOLD = 50
MAX_RETRIES = 5
BASE_DELAY = 1.0
MAX_DELAY = 60.0
MULTIPLIER = 2.0

def validate_json_schema(data: Dict[str, Any], schema_path: str) -> bool:
    """
    Validate data against a JSON schema.
    Returns True if valid, False otherwise.
    """
    if not os.path.exists(schema_path):
        logger.warning(f"Schema file not found: {schema_path}")
        return False
    
    try:
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        # Basic validation (full jsonschema validation would require jsonschema library)
        required_fields = schema.get('required', [])
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Check types for known fields
        properties = schema.get('properties', {})
        for field, spec in properties.items():
            if field in data:
                expected_type = spec.get('type')
                value = data[field]
                
                if expected_type == 'string' and not isinstance(value, str):
                    logger.error(f"Field {field} should be string")
                    return False
                elif expected_type == 'number' and not isinstance(value, (int, float)):
                    logger.error(f"Field {field} should be number")
                    return False
                elif expected_type == 'array' and not isinstance(value, list):
                    logger.error(f"Field {field} should be array")
                    return False
                elif expected_type == 'object' and not isinstance(value, dict):
                    logger.error(f"Field {field} should be object")
                    return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating schema: {e}")
        return False

def log_api_headers(response: requests.Response) -> None:
    """
    Extract and log API rate limit headers.
    Logs to logs/pipeline.log
    """
    log_file = "logs/pipeline.log"
    
    rate_limit_remaining = response.headers.get('X-RateLimit-Remaining', 'N/A')
    rate_limit_reset = response.headers.get('X-RateLimit-Reset', 'N/A')
    
    # Extract retry_count from context if available (simulated here)
    retry_count = getattr(response, 'retry_count', 0)
    
    log_entry = f"RateLimit-Remaining: {rate_limit_remaining}, RateLimit-Reset: {rate_limit_reset}, retry_count: {retry_count}\n"
    
    try:
        with open(log_file, 'a') as f:
            f.write(log_entry)
    except Exception as e:
        logger.error(f"Failed to write to log file: {e}")

def api_request_with_backoff(url: str, headers: Dict[str, str]) -> requests.Response:
    """
    Make an API request with exponential backoff.
    """
    delay = BASE_DELAY
    last_response = None
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            last_response = response
            
            # Set retry count on response for logging
            response.retry_count = attempt
            
            if response.status_code == 200:
                return response
            elif response.status_code == 403:
                # Rate limited, use reset time
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                wait_time = max(reset_time - int(time.time()) + 1, delay)
                logger.warning(f"Rate limited. Waiting {wait_time}s")
                time.sleep(wait_time)
                continue
            elif response.status_code >= 500:
                # Server error, retry with backoff
                logger.warning(f"Server error {response.status_code}. Retrying in {delay}s")
            else:
                # Other error, don't retry
                return response
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed: {e}. Retrying in {delay}s")
        
        time.sleep(delay)
        delay = min(delay * MULTIPLIER + random.uniform(0, delay * 0.1), MAX_DELAY)
    
    if last_response:
        return last_response
    raise Exception("All retry attempts failed")

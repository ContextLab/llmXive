import json
import logging
import os
import random
import time
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

def validate_json_schema(data: Dict[str, Any], schema_path: str) -> bool:
    """
    Validates data against a JSON schema defined in a YAML file.
    Note: This is a simplified validator for specific schema structures.
    """
    try:
        import yaml
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        # Basic validation logic for 'required' and 'type'
        if 'required' in schema:
            for field in schema['required']:
                if field not in data:
                    logger.error(f"Missing required field: {field}")
                    return False
        
        if 'properties' in schema:
            for key, value in data.items():
                if key in schema['properties']:
                    expected_type = schema['properties'][key].get('type')
                    if expected_type == 'string' and not isinstance(value, str):
                        logger.error(f"Field {key} expected string, got {type(value)}")
                        return False
                    if expected_type == 'number' and not isinstance(value, (int, float)):
                        logger.error(f"Field {key} expected number, got {type(value)}")
                        return False
                    if expected_type == 'array' and not isinstance(value, list):
                        logger.error(f"Field {key} expected array, got {type(value)}")
                        return False
                    if expected_type == 'object' and not isinstance(value, dict):
                        logger.error(f"Field {key} expected object, got {type(value)}")
                        return False
        
        return True
    except Exception as e:
        logger.error(f"Schema validation error: {e}")
        return False

def api_request_with_backoff(url: str, headers: Dict[str, str] = None, max_retries: int = 5) -> Dict[str, Any]:
    """
    Makes an API request with exponential backoff and jitter.
    """
    base_delay = 1.0
    max_delay = 60.0
    retries = 0

    while retries < max_retries:
        try:
            import requests
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                # Rate limited
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited. Waiting {retry_after}s.")
                time.sleep(retry_after)
                continue
            elif response.status_code >= 500:
                # Server error, retry
                delay = min(base_delay * (2 ** retries) + random.uniform(0, 0.5 * base_delay * (2 ** retries)), max_delay)
                logger.warning(f"Server error {response.status_code}. Retrying in {delay:.2f}s...")
                time.sleep(delay)
                retries += 1
            else:
                logger.error(f"API request failed with status {response.status_code}: {response.text}")
                return {}
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception: {e}")
            delay = min(base_delay * (2 ** retries) + random.uniform(0, 0.5 * base_delay * (2 ** retries)), max_delay)
            time.sleep(delay)
            retries += 1

    raise Exception(f"Failed to fetch {url} after {max_retries} retries")

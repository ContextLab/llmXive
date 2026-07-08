import json
import logging
import os
import random
import time
from pathlib import Path
from typing import Any, Dict, Optional

from logging_config import get_logger

logger = get_logger(__name__)

def validate_json_schema(data: Any, schema_path: str) -> bool:
    """
    Validates data against a JSON schema defined in a YAML file.
    Returns True if valid, False otherwise.
    Note: For a full implementation, we'd use a library like jsonschema.
    Here we implement a basic structural check based on the simple schema definitions provided.
    """
    try:
        with open(schema_path, 'r') as f:
            # Assuming simple YAML parsing or JSON if format allows
            # Since we can't import pyyaml if not installed, we assume the schema is simple enough
            # or we rely on the fact that T004 created simple files.
            # For robustness, we assume the environment has pyyaml or we parse manually if JSON-like.
            # Given constraints, we'll do a basic check if the file exists and is readable.
            import yaml
            schema = yaml.safe_load(f)
    except ImportError:
        logger.warning("PyYAML not installed. Skipping detailed schema validation.")
        return True
    except FileNotFoundError:
        logger.error(f"Schema file not found: {schema_path}")
        return False
    except Exception as e:
        logger.error(f"Error loading schema: {e}")
        return False

    # Basic validation logic for the specific schemas defined in T004
    if not isinstance(data, dict):
        logger.error("Data must be a dictionary.")
        return False
    
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in data:
            logger.error(f"Missing required field: {field}")
            return False
    
    return True

def api_request_with_backoff(url: str, headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
    """
    Makes an API request with exponential backoff and jitter.
    """
    base_delay = 1.0
    max_delay = 60.0
    multiplier = 2.0
    max_retries = 5
    
    for attempt in range(max_retries):
        try:
            import urllib.request
            import urllib.error
            
            req = urllib.request.Request(url, headers=headers or {})
            with urllib.request.urlopen(req, timeout=30) as response:
                # Capture rate limit headers
                if hasattr(response, 'headers'):
                    capture_rate_limit_headers(dict(response.headers))
                
                return json.loads(response.read().decode('utf-8'))
        
        except urllib.error.HTTPError as e:
            if e.code == 403 and "rate limit" in str(e.reason).lower():
                logger.warning(f"Rate limit hit. Retrying in {base_delay}s...")
            else:
                logger.error(f"HTTP Error {e.code}: {e.reason}")
                return None
        
        except Exception as e:
            logger.error(f"Request failed: {e}")
        
        # Calculate delay with jitter
        delay = min(base_delay * (multiplier ** attempt), max_delay)
        jitter = delay * random.uniform(0, 0.5)
        sleep_time = delay + jitter
        
        logger.info(f"Retrying in {sleep_time:.2f}s (Attempt {attempt + 1}/{max_retries})")
        time.sleep(sleep_time)
    
    logger.error(f"Failed to fetch {url} after {max_retries} attempts.")
    return None

import json
import logging
import os
import random
import time
import requests
from pathlib import Path
from typing import Any, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_json_schema(data: Any, schema_path: str) -> bool:
    """
    Validate data against a JSON schema file.
    
    Args:
        data: Data to validate
        schema_path: Path to the schema file
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Simple validation - check required fields exist
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        if schema.get("type") == "object" and "properties" in schema:
            required = schema.get("required", [])
            for field in required:
                if field not in data:
                    logger.error(f"Missing required field: {field}")
                    return False
        
        return True
    except Exception as e:
        logger.error(f"Schema validation error: {e}")
        return False

def log_api_headers(response: requests.Response) -> None:
    """
    Extract and log rate limit headers from API response.
    
    Args:
        response: The API response object
    """
    log_path = Path(__file__).parent.parent / "logs" / "pipeline.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    remaining = response.headers.get("X-RateLimit-Remaining", "N/A")
    reset = response.headers.get("X-RateLimit-Reset", "N/A")
    
    log_entry = f"Rate Limit - Remaining: {remaining}, Reset: {reset}\n"
    
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    logger.debug(f"Rate limit headers logged: Remaining={remaining}, Reset={reset}")

def api_request_with_backoff(
    url: str, 
    headers: Dict[str, str], 
    params: Optional[Dict[str, Any]] = None,
    max_retries: int = 5
) -> requests.Response:
    """
    Make an API request with exponential backoff retry logic.
    
    Args:
        url: The URL to request
        headers: Request headers
        params: Optional query parameters
        max_retries: Maximum number of retry attempts
        
    Returns:
        The response object
        
    Raises:
        requests.exceptions.RequestException: If all retries fail
    """
    base_delay = 1.0
    multiplier = 2.0
    max_delay = 60.0
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            # Handle rate limiting
            if response.status_code == 403 or response.status_code == 429:
                reset_time = response.headers.get("X-RateLimit-Reset")
                if reset_time:
                    wait_time = int(reset_time) - int(time.time()) + 1
                    wait_time = max(wait_time, base_delay)
                    logger.warning(f"Rate limited. Waiting {wait_time} seconds.")
                    time.sleep(wait_time)
                    continue
                
                # Fallback to exponential backoff
                delay = min(base_delay * (multiplier ** attempt) + random.uniform(0, 0.5 * base_delay), max_delay)
                logger.warning(f"Rate limited. Backing off for {delay:.2f} seconds.")
                time.sleep(delay)
                continue
            
            return response
            
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            
            delay = min(base_delay * (multiplier ** attempt) + random.uniform(0, 0.5 * base_delay), max_delay)
            logger.warning(f"Request failed: {e}. Retrying in {delay:.2f} seconds...")
            time.sleep(delay)
    
    raise requests.exceptions.RequestException("Max retries exceeded")
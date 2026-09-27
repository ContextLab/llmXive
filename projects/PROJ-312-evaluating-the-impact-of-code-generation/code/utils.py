import json
import logging
import os
import random
import time
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)

def validate_json_schema(data: Any, schema_path: str) -> bool:
    """
    Validates data against a JSON schema defined in a YAML file.
    
    Args:
        data: The data to validate.
        schema_path: Path to the schema YAML file.
    
    Returns:
        True if valid, False otherwise.
    """
    # Simple validation placeholder for now; assumes structure matches
    # In a real implementation, we would use a library like jsonschema
    # and parse the YAML schema.
    if not isinstance(data, list) and not isinstance(data, dict):
        return False
    return True

def log_api_headers(response: requests.Response) -> None:
    """
    Extracts rate limit headers from the response and logs them.
    
    Args:
        response: The HTTP response object.
    """
    headers = response.headers
    remaining = headers.get("X-RateLimit-Remaining", "N/A")
    reset = headers.get("X-RateLimit-Reset", "N/A")
    
    log_msg = f"Rate Limit - Remaining: {remaining}, Reset: {reset}"
    logger.info(log_msg)
    
    # Also append to the specific log file mentioned in T006a
    log_file_path = Path("logs/pipeline.log")
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file_path, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {log_msg}\n")

def api_request_with_backoff(
    url: str,
    headers: Dict[str, str],
    params: Optional[Dict[str, Any]] = None,
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0
) -> requests.Response:
    """
    Makes a request to the URL with exponential backoff and jitter.
    
    Args:
        url: The URL to request.
        headers: Headers to send.
        params: Query parameters.
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay cap in seconds.
    
    Returns:
        The HTTP response.
    
    Raises:
        requests.exceptions.RequestException: If all retries fail.
    """
    delay = base_delay
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            # Handle 403 (Rate Limit) specifically
            if response.status_code == 403:
                logger.warning(f"Rate limit hit (403). Retrying in {delay}s...")
                time.sleep(delay)
                delay = min(delay * 2, max_delay)
                delay = delay + random.uniform(0, delay * 0.2)  # Jitter
                continue
            
            # Handle 5xx server errors
            if 500 <= response.status_code < 600:
                logger.warning(f"Server error {response.status_code}. Retrying in {delay}s...")
                time.sleep(delay)
                delay = min(delay * 2, max_delay)
                delay = delay + random.uniform(0, delay * 0.2)  # Jitter
                continue

            return response
        
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
            delay = min(delay * 2, max_delay)
            delay = delay + random.uniform(0, delay * 0.2)  # Jitter
    
    raise requests.exceptions.RequestException("Max retries exceeded")

from pathlib import Path

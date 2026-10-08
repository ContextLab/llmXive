import json
import logging
import os
import random
import time
from typing import Any, Dict, Optional
import requests

# T014: Configurable threshold constant
MIN_PR_THRESHOLD = 50

def validate_json_schema(data: Any, schema_path: str) -> bool:
    """
    Validate data against a JSON schema.
    Returns True if valid, False otherwise.
    Logs errors if validation fails.
    """
    try:
        import jsonschema
    except ImportError:
        logging.getLogger(__name__).error("jsonschema library not installed. Install with 'pip install jsonschema'")
        return False

    with open(schema_path, 'r') as f:
        schema = json.load(f)

    try:
        jsonschema.validate(instance=data, schema=schema)
        return True
    except jsonschema.exceptions.ValidationError as e:
        logging.getLogger(__name__).error(f"Schema validation failed: {e.message}")
        return False

def log_api_headers(response: requests.Response, logger: logging.Logger):
    """
    Extract and log API rate limit headers.
    Logs X-RateLimit-Remaining, X-RateLimit-Reset, and retry_count context.
    """
    remaining = response.headers.get('X-RateLimit-Remaining', 'N/A')
    reset = response.headers.get('X-RateLimit-Reset', 'N/A')
    
    # Extract retry_count from response context if available (mocked or real)
    retry_count = getattr(response, 'retry_count', 0)
    
    log_msg = f"Rate Limit - Remaining: {remaining}, Reset: {reset}, Retry Count: {retry_count}"
    logger.info(log_msg)

def api_request_with_backoff(url: str, headers: Dict[str, str], logger: logging.Logger, base_delay: float = 1.0, multiplier: float = 2.0, max_delay: float = 60.0, max_retries: int = 3) -> requests.Response:
    """
    Perform an API request with exponential backoff.
    Parameters:
      base_delay: 1s
      multiplier: 2
      max_delay: 60s
      max_retries: 3
      jitter: random non-negative percentage of delay
    """
    attempt = 0
    delay = base_delay

    while attempt <= max_retries:
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            # If rate limited (403) or server error (5xx), retry
            if response.status_code in [403, 500, 502, 503, 504]:
                if attempt < max_retries:
                    # Add jitter: random non-negative percentage of delay
                    jitter = delay * random.uniform(0, 0.1)
                    sleep_time = delay + jitter
                    logger.warning(f"Rate limited or server error. Retrying in {sleep_time:.2f}s (Attempt {attempt+1}/{max_retries})")
                    time.sleep(sleep_time)
                    delay = min(delay * multiplier, max_delay)
                    attempt += 1
                    # Attach retry count to response for logging
                    response.retry_count = attempt
                    continue
                else:
                    logger.error(f"Max retries exceeded for {url}")
                    return response
            
            # Success or other error (e.g., 404) -> return immediately
            response.retry_count = attempt
            return response

        except requests.exceptions.RequestException as e:
            if attempt < max_retries:
                logger.warning(f"Request failed: {e}. Retrying in {delay:.2f}s")
                time.sleep(delay)
                delay = min(delay * multiplier, max_delay)
                attempt += 1
            else:
                logger.error(f"Max retries exceeded for {url} due to network error: {e}")
                raise

    # Should not reach here, but return last response if loop breaks unexpectedly
    return response

def save_excluded_repos(excluded_repos: list, output_path: str):
    """
    Save the list of excluded repository names to a text file.
    Used by T014 to record repos with fewer than MIN_PR_THRESHOLD PRs.
    """
    with open(output_path, 'w') as f:
        for repo_name in excluded_repos:
            f.write(f"{repo_name}\n")

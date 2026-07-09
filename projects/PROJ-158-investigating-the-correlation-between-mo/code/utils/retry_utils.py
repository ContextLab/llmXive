import time
import logging
from typing import Optional, Any

import requests
from requests.exceptions import RequestException, Timeout, HTTPError

# Import logger from sibling module as per project API
from utils.logger import setup_logger

# Initialize logger for this module
logger = setup_logger(__name__)


def retry_request(
    url: str,
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    timeout: float = 30.0,
    method: str = "GET"
) -> Optional[Any]:
    """
    Execute an HTTP request with exponential backoff retry logic.

    Args:
        url (str): The URL to request.
        max_retries (int): Maximum number of retry attempts.
        backoff_factor (float): Factor by which the wait time increases between retries.
        timeout (float): Request timeout in seconds.
        method (str): HTTP method to use ('GET', 'POST', etc.). Default is 'GET'.

    Returns:
        Optional[Any]: The response object if successful, None if all retries fail.

    Raises:
        None: Errors are logged, and None is returned on failure.
    """
    attempt = 0
    while attempt <= max_retries:
        try:
            logger.info(f"Request attempt {attempt + 1}/{max_retries + 1} for URL: {url}")
            
            response = requests.request(
                method=method,
                url=url,
                timeout=timeout
            )

            # Raise HTTPError for bad status codes (4xx, 5xx)
            response.raise_for_status()

            logger.info(f"Successfully retrieved data from {url}")
            return response

        except (Timeout, RequestException) as e:
            attempt += 1
            if attempt > max_retries:
                logger.error(f"Failed to retrieve {url} after {max_retries} retries. Last error: {e}")
                return None

            # Calculate wait time: backoff_factor^(attempt-1)
            wait_time = backoff_factor ** (attempt - 1)
            logger.warning(
                f"Request to {url} failed (Attempt {attempt}/{max_retries + 1}). "
                f"Retrying in {wait_time:.2f}s... Error: {e}"
            )
            time.sleep(wait_time)

        except Exception as e:
            # Catch unexpected errors to prevent infinite loops
            logger.error(f"Unexpected error during request to {url}: {e}")
            return None

    return None
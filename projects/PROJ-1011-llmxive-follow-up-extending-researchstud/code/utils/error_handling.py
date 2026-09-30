"""
Error Handling Module for llmXive Research Pipeline.

Defines custom exceptions for various failure modes in the data pipeline.
"""

import logging
from typing import Optional, List, Dict, Any, Callable, TypeVar
from urllib.error import URLError
from http.client import HTTPException
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """Raised when data fetching fails (network, API, or content issues)."""
    pass

class ValidationError(Exception):
    """Raised when data validation fails (schema, format, or logical errors)."""
    pass

class BalanceError(Exception):
    """Raised when data sampling fails to achieve target balance."""
    pass

class DesignViolationError(Exception):
    """Raised when a design constraint is violated (e.g., wrong proposal groups)."""
    pass

class VerificationError(Exception):
    """Raised when verification processes fail (e.g., ORCID, signature)."""
    pass

class IRRGateFailError(Exception):
    """Raised when Inter-Rater Reliability gate fails."""
    pass

def validate_data_response(response: requests.Response, expected_content_type: Optional[str] = None) -> bool:
    """
    Validate a requests response for successful status and content type.
    
    Args:
        response: The requests.Response object.
        expected_content_type: Optional expected content type (e.g., 'application/json').
        
    Returns:
        True if valid, False otherwise.
        
    Raises:
        DataFetchError: If validation fails.
    """
    if response.status_code == 403:
        raise DataFetchError(f"Access forbidden (403): {response.url}")
    elif response.status_code == 404:
        raise DataFetchError(f"Not found (404): {response.url}")
    elif response.status_code >= 400:
        raise DataFetchError(f"HTTP error {response.status_code}: {response.text[:200]}")
    
    if expected_content_type and expected_content_type not in response.headers.get('Content-Type', ''):
        raise DataFetchError(
            f"Unexpected content type: expected '{expected_content_type}', "
            f"got '{response.headers.get('Content-Type')}'"
        )
    
    return True

def fetch_with_strict_handling(
    url: str,
    method: str = 'GET',
    expected_content_type: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30
) -> requests.Response:
    """
    Fetch data from a URL with strict error handling.
    
    Args:
        url: The URL to fetch.
        method: HTTP method (GET, POST, etc.).
        expected_content_type: Expected content type.
        headers: Optional headers.
        timeout: Request timeout in seconds.
        
    Returns:
        The requests.Response object.
        
    Raises:
        DataFetchError: For any fetch failure.
    """
    try:
        response = requests.request(method, url, headers=headers, timeout=timeout)
        validate_data_response(response, expected_content_type)
        return response
        
    except (Timeout, ConnectionError) as e:
        raise DataFetchError(f"Network error fetching {url}: {e}")
    except requests.exceptions.RequestException as e:
        raise DataFetchError(f"Request failed fetching {url}: {e}")
    except ValueError as e:
        raise DataFetchError(f"Invalid response handling for {url}: {e}")

def handle_fetch_failure(
    url: str,
    error: Exception,
    venue_name: Optional[str] = None,
    context: Optional[str] = None
) -> None:
    """
    Handle and log a fetch failure with context.
    
    Args:
        url: The URL that failed.
        error: The exception that occurred.
        venue_name: Optional name of the data source/venue.
        context: Optional additional context.
    """
    msg_parts = [f"Data fetch failed for {url}"]
    if venue_name:
        msg_parts.append(f"(Venue: {venue_name})")
    if context:
        msg_parts.append(f"({context})")
    
    msg = " ".join(msg_parts)
    logger.error(f"{msg}: {error}")
    
    # Raise a more descriptive error
    raise DataFetchError(f"{msg}: {error}")

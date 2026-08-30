import logging
from typing import Optional, List, Dict, Any, Callable, TypeVar
from urllib.error import URLError
from http.client import HTTPException
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """Custom exception for data fetching errors."""
    def __init__(self, message: str, url: Optional[str] = None, status_code: Optional[int] = None):
        super().__init__(message)
        self.url = url
        self.status_code = status_code

class ValidationError(Exception):
    """Custom exception for validation errors."""
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message)
        self.field = field

def validate_data_response(response: requests.Response) -> bool:
    """Validate that a response is successful."""
    return response.status_code == 200

def fetch_with_strict_handling(url: str, params: Optional[Dict[str, Any]] = None, 
                               headers: Optional[Dict[str, str]] = None,
                               timeout: int = 30) -> requests.Response:
    """
    Fetch data with strict error handling.
    Raises DataFetchError for any failure, never returns partial/synthetic data.
    """
    try:
        response = requests.get(url, params=params, headers=headers, timeout=timeout)
        # Don't raise on status code here - let the caller decide
        return response
    except Timeout as e:
        logger.error(f"Timeout fetching {url}: {e}")
        raise DataFetchError(f"Timeout fetching {url}: {e}", url=url)
    except ConnectionError as e:
        logger.error(f"Connection error fetching {url}: {e}")
        raise DataFetchError(f"Connection error fetching {url}: {e}", url=url)
    except URLError as e:
        logger.error(f"URL error fetching {url}: {e}")
        raise DataFetchError(f"URL error fetching {url}: {e}", url=url)
    except RequestException as e:
        logger.error(f"Request error fetching {url}: {e}")
        raise DataFetchError(f"Request error fetching {url}: {e}", url=url)
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {e}")
        raise DataFetchError(f"Unexpected error fetching {url}: {e}", url=url)

def handle_fetch_failure(url: str, error: Exception) -> None:
    """Handle a fetch failure by logging and raising a DataFetchError."""
    logger.error(f"Fetch failed for {url}: {error}")
    raise DataFetchError(f"Fetch failed for {url}: {error}", url=url)

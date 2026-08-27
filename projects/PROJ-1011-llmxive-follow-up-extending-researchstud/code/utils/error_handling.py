"""
Error handling infrastructure for the llmXive pipeline.

This module provides strict error handling that fails loudly on data fetch errors.
It ensures that any failure to retrieve real data from external sources raises
a clear exception rather than falling back to synthetic data.
"""
import logging
from typing import Optional, List, Dict, Any, Callable, TypeVar
from urllib.error import URLError
from http.client import HTTPException
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

# Configure module logger
logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """
    Custom exception raised when data fetching from a real source fails.
    
    This error is raised loudly to prevent silent fallback to synthetic data.
    """
    def __init__(self, message: str, source: str, status_code: Optional[int] = None, details: Optional[str] = None):
        self.source = source
        self.status_code = status_code
        self.details = details
        
        error_msg = f"DataFetchError: {message}"
        if source:
            error_msg += f" (Source: {source})"
        if status_code:
            error_msg += f" (Status: {status_code})"
        if details:
            error_msg += f" (Details: {details})"
        
        super().__init__(error_msg)

class ValidationError(Exception):
    """
    Custom exception raised when data validation fails.
    """
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        self.field = field
        self.value = value
        
        error_msg = f"ValidationError: {message}"
        if field:
            error_msg += f" (Field: {field})"
        if value is not None:
            error_msg += f" (Value: {value})"
        
        super().__init__(error_msg)

def validate_data_response(response_data: Any, required_fields: List[str], source: str) -> Dict[str, Any]:
    """
    Validate that fetched data contains required fields.
    
    Args:
        response_data: The data returned from the fetch operation
        required_fields: List of field names that must be present
        source: The source of the data (for error messages)
    
    Returns:
        The validated data if all required fields are present
    
    Raises:
        ValidationError: If required fields are missing or data is invalid
        DataFetchError: If response_data is None or empty
    """
    if response_data is None:
        logger.error(f"DataFetchError: Received None response from {source}")
        raise DataFetchError(
            message="Received None response from data source",
            source=source
        )
    
    if isinstance(response_data, (list, dict)) and len(response_data) == 0:
        logger.error(f"DataFetchError: Received empty response from {source}")
        raise DataFetchError(
            message="Received empty response from data source",
            source=source
        )
    
    if isinstance(response_data, dict):
        missing_fields = [field for field in required_fields if field not in response_data]
        if missing_fields:
            logger.error(f"ValidationError: Missing required fields {missing_fields} in data from {source}")
            raise ValidationError(
                message=f"Missing required fields in data response",
                field=str(missing_fields),
                value=list(response_data.keys())
            )
    
    return response_data

T = TypeVar('T')

def fetch_with_strict_handling(
    fetch_func: Callable[[], T],
    source: str,
    timeout: int = 30
) -> T:
    """
    Execute a fetch function with strict error handling.
    
    This function wraps a fetch operation and ensures that any failure
    raises a DataFetchError rather than returning None or synthetic data.
    
    Args:
        fetch_func: A callable that performs the actual data fetch
        source: Human-readable identifier for the data source
        timeout: Timeout in seconds for the fetch operation
    
    Returns:
        The fetched data if successful
    
    Raises:
        DataFetchError: If the fetch fails for any reason
        Timeout: If the fetch times out
        ConnectionError: If there's a network connection issue
    """
    logger.info(f"Attempting to fetch data from {source}")
    
    try:
        # Set a timeout for the fetch operation
        result = fetch_func()
        
        if result is None:
            logger.error(f"DataFetchError: Fetch from {source} returned None")
            raise DataFetchError(
                message="Data fetch returned None",
                source=source
            )
        
        logger.info(f"Successfully fetched data from {source}")
        return result
        
    except (URLError, HTTPException) as e:
        logger.error(f"DataFetchError: Network error fetching from {source}: {str(e)}")
        raise DataFetchError(
            message=f"Network error: {str(e)}",
            source=source,
            details=str(e)
        )
    except Timeout as e:
        logger.error(f"DataFetchError: Timeout fetching from {source} after {timeout}s")
        raise DataFetchError(
            message=f"Timeout after {timeout} seconds",
            source=source,
            details=str(e)
        )
    except ConnectionError as e:
        logger.error(f"DataFetchError: Connection error fetching from {source}: {str(e)}")
        raise DataFetchError(
            message=f"Connection error: {str(e)}",
            source=source,
            details=str(e)
        )
    except RequestException as e:
        status_code = getattr(e.response, 'status_code', None) if hasattr(e, 'response') and e.response else None
        logger.error(f"DataFetchError: Request error fetching from {source}: {str(e)} (Status: {status_code})")
        raise DataFetchError(
            message=f"Request error: {str(e)}",
            source=source,
            status_code=status_code,
            details=str(e)
        )
    except Exception as e:
        logger.error(f"DataFetchError: Unexpected error fetching from {source}: {str(e)}")
        raise DataFetchError(
            message=f"Unexpected error: {str(e)}",
            source=source,
            details=str(e)
        )

def handle_fetch_failure(source: str, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log and handle a fetch failure.
    
    This function is used to ensure consistent logging and error handling
    when a data fetch fails. It logs the error and re-raises it as a
    DataFetchError to ensure the failure is loud and visible.
    
    Args:
        source: The data source that failed
        error: The original exception that occurred
        context: Optional additional context about the fetch attempt
    
    Raises:
        DataFetchError: Always raised with detailed information
    """
    error_msg = f"Failed to fetch data from {source}"
    if context:
        error_msg += f" - Context: {context}"
    
    logger.error(f"{error_msg}: {str(error)}", exc_info=True)
    
    raise DataFetchError(
        message=error_msg,
        source=source,
        details=str(error)
    )
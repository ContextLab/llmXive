"""
Error handling utilities for the data ingestion pipeline.

Provides decorators and helper functions to catch, log, and transform
low-level exceptions into the project's custom exception hierarchy.
"""

import logging
import traceback
from functools import wraps
from typing import Callable, Optional, Type, Tuple, Union

import requests
import json

from ..exceptions import (
    DataIngestionError,
    SourceConnectionError,
    SourceAuthenticationError,
    SourceNotFoundError,
    DataFormatError
)

logger = logging.getLogger(__name__)

def handle_ingestion_errors(source_name: str = "unknown"):
    """
    Decorator to wrap ingestion functions and map exceptions to custom types.
    
    Args:
        source_name (str): Identifier for the data source being accessed.
    
    Returns:
        Callable: The wrapped function.
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error fetching from {source_name}: {e}")
                raise SourceConnectionError("Failed to connect to data source", source_name) from e
            except requests.exceptions.Timeout as e:
                logger.error(f"Timeout fetching from {source_name}: {e}")
                raise SourceConnectionError("Request timed out", source_name) from e
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if hasattr(e, 'response') and e.response else None
                if status_code == 401:
                    logger.error(f"Authentication error for {source_name}: {e}")
                    raise SourceAuthenticationError("API key invalid or missing", source_name) from e
                elif status_code == 404:
                    logger.error(f"Resource not found for {source_name}: {e}")
                    raise SourceNotFoundError("Dataset or resource not found", source_name) from e
                else:
                    logger.error(f"HTTP error {status_code} for {source_name}: {e}")
                    raise SourceConnectionError(f"HTTP Error {status_code}", source_name, status_code) from e
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Data format error for {source_name}: {e}")
                raise DataFormatError("Could not parse response as expected JSON/Format", source_name) from e
            except DataIngestionError:
                # Re-raise our custom errors as-is
                raise
            except Exception as e:
                # Log unexpected errors and wrap them
                logger.critical(f"Unexpected error in {source_name}: {traceback.format_exc()}")
                raise DataIngestionError(f"Unexpected ingestion failure: {str(e)}", source_name) from e
        return wrapper
    return decorator

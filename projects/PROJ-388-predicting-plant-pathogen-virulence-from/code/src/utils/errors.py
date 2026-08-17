"""
Unified error handling module for the plant pathogen virulence prediction pipeline.

This module defines custom exceptions and handler functions to ensure
'Fail Loudly' behavior for all data ingestion and analysis steps.

Constitution Principle: No synthetic fallbacks allowed. All failures must raise
explicit errors with context (URLs, status codes, analysis context).
"""
import logging
from typing import Optional, Dict, Any, Callable, TypeVar, Union
import requests
from json import JSONDecodeError
import pandas as pd
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for generic handlers
T = TypeVar('T')


class DataFetchError(Exception):
    """
    Raised when data ingestion (NCBI, PHI-base, file parsing) fails.
    
    Attributes:
        message: Human-readable error description.
        url: The URL that failed (if applicable).
        status_code: HTTP status code (if applicable).
        context: Additional context about the failure.
    """
    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.url = url
        self.status_code = status_code
        self.context = context or {}
        
        error_details = [message]
        if url:
            error_details.append(f"URL: {url}")
        if status_code:
            error_details.append(f"Status: {status_code}")
        if context:
            error_details.append(f"Context: {context}")
        
        super().__init__(" | ".join(error_details))
        logger.error(self.message)


class AnalysisError(Exception):
    """
    Raised when statistical analysis steps (Tree construction, PGLS, FDR) fail.
    
    Attributes:
        message: Human-readable error description.
        step: The analysis step that failed (e.g., 'tree_construction', 'pgls_fit').
        context: Additional context about the failure.
    """
    def __init__(
        self,
        message: str,
        step: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.step = step
        self.context = context or {}
        
        error_details = [message]
        if step:
            error_details.append(f"Step: {step}")
        if context:
            error_details.append(f"Context: {context}")
        
        super().__init__(" | ".join(error_details))
        logger.error(self.message)


def handle_data_fetch_error(
    e: Exception,
    url: Optional[str] = None,
    step: str = "data_fetch"
) -> None:
    """
    Unified handler for data fetch errors.
    
    This function inspects the exception and raises a specific DataFetchError
    with appropriate context. It ensures no synthetic fallback is ever triggered.
    
    Args:
        e: The original exception caught.
        url: The URL being accessed (if applicable).
        step: The logical step where the error occurred.
    
    Raises:
        DataFetchError: Always raised with detailed context.
    """
    if isinstance(e, DataFetchError):
        # Re-raise if already our custom error
        raise e
    
    error_context = {"original_exception": str(e), "step": step}
    message = f"Data fetch failed during {step}"
    
    if isinstance(e, requests.exceptions.RequestException):
        status_code = None
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
            message = f"HTTP request failed: {e.response.status_code} {e.response.reason}"
        else:
            message = f"Network error during {step}: {str(e)}"
        raise DataFetchError(message, url=url, status_code=status_code, context=error_context)
    
    elif isinstance(e, JSONDecodeError):
        message = f"JSON parsing failed during {step}: Invalid JSON format"
        raise DataFetchError(message, url=url, context=error_context)
    
    elif isinstance(e, FileNotFoundError):
        message = f"Required file not found during {step}: {str(e)}"
        raise DataFetchError(message, context=error_context)
    
    elif isinstance(e, ValueError):
        # Catch NaN or schema validation errors
        if "NaN" in str(e) or "nan" in str(e):
            message = f"Invalid data value (NaN) detected during {step}"
        else:
            message = f"Value error during {step}: {str(e)}"
        raise DataFetchError(message, url=url, context=error_context)
    
    else:
        # Generic fallback for unexpected errors
        message = f"Unexpected error during {step}: {type(e).__name__} - {str(e)}"
        raise DataFetchError(message, url=url, context=error_context)


def handle_analysis_error(
    e: Exception,
    step: str = "analysis",
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Unified handler for analysis errors.
    
    This function inspects the exception and raises a specific AnalysisError
    with appropriate context. It ensures no silent failure or fallback occurs.
    
    Args:
        e: The original exception caught.
        step: The analysis step that failed.
        context: Additional context to include in the error.
    
    Raises:
        AnalysisError: Always raised with detailed context.
    """
    if isinstance(e, AnalysisError):
        # Re-raise if already our custom error
        raise e
    
    error_context = {"original_exception": str(e), "step": step}
    if context:
        error_context.update(context)
    
    message = f"Analysis failed during {step}: {str(e)}"
    
    if isinstance(e, (np.linalg.LinAlgError, ValueError)):
        if "singular" in str(e).lower() or "convergence" in str(e).lower():
            message = f"Numerical instability or convergence failure during {step}"
        else:
            message = f"Numerical error during {step}: {str(e)}"
    
    elif isinstance(e, pd.errors.EmptyDataError):
        message = f"Empty dataset provided to analysis step: {step}"
    
    elif isinstance(e, KeyError):
        message = f"Missing required data column or key during {step}: {str(e)}"
    
    raise AnalysisError(message, step=step, context=error_context)


def wrap_fetch_operation(
    func: Callable[..., T],
    url: Optional[str] = None,
    step: str = "fetch"
) -> Callable[..., T]:
    """
    Decorator to wrap data fetch operations with unified error handling.
    
    Args:
        func: The function to wrap.
        url: The URL being accessed (if applicable).
        step: The logical step name.
    
    Returns:
        Wrapped function that raises DataFetchError on failure.
    """
    def wrapper(*args, **kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            handle_data_fetch_error(e, url=url, step=step)
    return wrapper


def wrap_analysis_operation(
    func: Callable[..., T],
    step: str = "analysis"
) -> Callable[..., T]:
    """
    Decorator to wrap analysis operations with unified error handling.
    
    Args:
        func: The function to wrap.
        step: The analysis step name.
    
    Returns:
        Wrapped function that raises AnalysisError on failure.
    """
    def wrapper(*args, **kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            handle_analysis_error(e, step=step)
    return wrapper

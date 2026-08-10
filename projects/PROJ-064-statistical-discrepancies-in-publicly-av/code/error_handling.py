"""
Error handling utilities and context managers.
"""
import traceback
from functools import wraps
from typing import Callable, Any, TypeVar, Optional

from .logger import get_logger
from .exceptions import DiscrepancyError, DataAcquisitionError

logger = get_logger(__name__)

T = TypeVar('T')

def handle_errors(
    fallback: Optional[Any] = None,
    log_level: int = logging.ERROR,
    reraise: bool = False
):
    """
    Decorator to handle errors in a function gracefully.

    Args:
        fallback: Value to return if an error occurs (if reraise is False).
        log_level: Level at which to log the error.
        reraise: If True, re-raise the exception after logging.

    Returns:
        Decorated function.
    """
    import logging
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except DiscrepancyError as e:
                logger.log(log_level, f"DiscrepancyError in {func.__name__}: {e}")
                logger.debug(traceback.format_exc())
                if reraise:
                    raise
                return fallback
            except Exception as e:
                logger.critical(f"Unexpected error in {func.__name__}: {e}")
                logger.debug(traceback.format_exc())
                if reraise:
                    raise
                return fallback
        return wrapper
    return decorator

def validate_required_fields(data: dict, required_fields: list, context: str = "") -> None:
    """
    Validate that a dictionary contains all required fields.

    Args:
        data: The dictionary to validate.
        required_fields: List of keys that must be present.
        context: String describing the source of data for error messages.

    Raises:
        MissingDataError: If any required field is missing.
    """
    missing = [field for field in required_fields if field not in data]
    if missing:
        raise MissingDataError(
            f"Missing required fields in {context}: {missing}. "
            f"Available keys: {list(data.keys())}"
        )

"""
Custom exception classes for the llmXive research pipeline.
"""
import logging
from typing import Optional, List, Dict, Any, Callable, TypeVar
from urllib.error import URLError
from http.client import HTTPException
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """Raised when data fetching fails due to network errors, paywalls, or invalid responses."""
    def __init__(self, message: str, venue: Optional[str] = None, status_code: Optional[int] = None):
        self.venue = venue
        self.status_code = status_code
        full_message = message
        if venue:
            full_message += f" (Venue: {venue})"
        if status_code:
            full_message += f" (Status: {status_code})"
        super().__init__(full_message)
        logger.error(f"DataFetchError: {full_message}")


class ValidationError(Exception):
    """Raised when data validation fails (schema, format, or business rules)."""
    pass


class BalanceError(Exception):
    """Raised when dataset extraction fails to meet balance requirements."""
    pass


class DesignViolationError(Exception):
    """Raised when a generated artifact violates the experimental design constraints."""
    pass


class VerificationError(Exception):
    """Raised when a verification step (e.g., blind check, fabrication guard) fails."""
    pass


class IRRGateFailError(Exception):
    """
    Raised when the Inter-Rater Reliability (IRR) gate fails.
    This is a hard blocking constraint per Constitution Principle VII.
    """
    def __init__(self, message: str, alpha_value: float, detailed_log: Optional[Dict[str, Any]] = None):
        self.alpha_value = alpha_value
        self.detailed_log = detailed_log or {}
        full_message = (
            f"{message} "
            f"Calculated Krippendorff's alpha: {alpha_value:.4f} (Threshold: >= 0.6). "
            f"The pipeline cannot proceed to statistical analysis due to insufficient inter-rater reliability."
        )
        super().__init__(full_message)
        logger.critical(f"IRRGateFailError: {full_message}")
        if detailed_log:
            logger.critical(f"IRR Details: {detailed_log}")


def validate_data_response(response: requests.Response, expected_status: int = 200) -> None:
    """
    Validates an HTTP response and raises DataFetchError if it fails.
    """
    if response.status_code != expected_status:
        raise DataFetchError(
            f"Unexpected status code {response.status_code}",
            status_code=response.status_code
        )
    if "text/html" in response.headers.get("Content-Type", ""):
        # Likely a login page or error page
        raise DataFetchError(
            "Received HTML instead of expected data format (likely a login page or error)",
            status_code=response.status_code
        )


def fetch_with_strict_handling(url: str, **kwargs) -> requests.Response:
    """
    Fetches data with strict error handling.
    Raises DataFetchError on any failure.
    """
    try:
        response = requests.get(url, **kwargs)
        validate_data_response(response)
        return response
    except (RequestException, Timeout, ConnectionError) as e:
        raise DataFetchError(f"Network error fetching {url}: {str(e)}")
    except DataFetchError:
        raise
    except Exception as e:
        raise DataFetchError(f"Unexpected error fetching {url}: {str(e)}")


def handle_fetch_failure(
    url: str,
    error: Exception,
    venue_name: str,
    fallback_url: Optional[str] = None,
    max_retries: int = 0
) -> Optional[requests.Response]:
    """
    Handles fetch failures.
    If fallback is provided and retries exhausted, attempts fallback.
    Otherwise, raises DataFetchError.
    """
    logger.warning(f"Fetch failed for {venue_name} ({url}): {error}")

    if fallback_url and max_retries > 0:
        logger.info(f"Attempting fallback for {venue_name}: {fallback_url}")
        try:
            return fetch_with_strict_handling(fallback_url)
        except Exception as fallback_error:
            logger.error(f"Fallback also failed for {venue_name}: {fallback_error}")

    raise DataFetchError(
        f"Failed to fetch data from {venue_name} after retries.",
        venue=venue_name
    )

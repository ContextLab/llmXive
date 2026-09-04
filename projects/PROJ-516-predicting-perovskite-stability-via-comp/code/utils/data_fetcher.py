"""
Data fetching utilities with configurable retry logic and exponential backoff.
"""
import time
import logging
import yaml
from pathlib import Path
from typing import Optional, Callable, Any, Dict, Tuple
from urllib.error import URLError, HTTPError
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FetchError(Exception):
    """Custom exception for data fetching errors."""
    pass

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Path to the config.yaml file. Defaults to project root.

    Returns:
        Dictionary containing configuration values.

    Raises:
        FileNotFoundError: If config file is not found.
        yaml.YAMLError: If YAML parsing fails.
    """
    if config_path is None:
        # Default to project root config.yaml
        config_path = Path(__file__).parent.parent.parent / "code" / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found at {config_path}")

    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def fetch_with_retry(
    url: str,
    fetch_func: Optional[Callable[[str], Any]] = None,
    config_path: Optional[Path] = None,
    **kwargs
) -> Any:
    """
    Fetch data from a URL with configurable retry logic and exponential backoff.

    The retry logic uses: delay = base_delay * (delay_multiplier ** retry_count)
    Values are read from config.yaml.

    Args:
        url: The URL to fetch data from.
        fetch_func: Optional custom fetch function. Defaults to requests.get.
        config_path: Optional path to config file.
        **kwargs: Additional arguments to pass to the fetch function.

    Returns:
        The response content (or processed data if fetch_func is provided).

    Raises:
        FetchError: If all retry attempts fail.
        FileNotFoundError: If config file is not found.
    """
    # Load configuration
    config = load_config(config_path)
    retry_config = config.get('retry', {})

    max_attempts = retry_config.get('max_attempts', 3)
    base_delay = retry_config.get('base_delay_seconds', 1.0)
    delay_multiplier = retry_config.get('delay_multiplier', 2.0)
    max_delay = retry_config.get('max_delay_seconds', 60.0)

    # Use default fetch function if not provided
    if fetch_func is None:
        fetch_func = lambda u, **kw: requests.get(u, **kw)

    last_exception = None

    for attempt in range(max_attempts):
        try:
            logger.info(f"Fetching {url} (attempt {attempt + 1}/{max_attempts})")
            response = fetch_func(url, **kwargs)

            # Check for HTTP errors
            if isinstance(response, requests.Response):
                response.raise_for_status()
                return response
            else:
                return response

        except (URLError, HTTPError, requests.RequestException) as e:
            last_exception = e
            logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")

            if attempt < max_attempts - 1:
                # Calculate delay with exponential backoff
                delay = min(base_delay * (delay_multiplier ** attempt), max_delay)
                logger.info(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
            else:
                logger.error(f"All {max_attempts} attempts failed for {url}")

    raise FetchError(f"Failed to fetch {url} after {max_attempts} attempts: {last_exception}")

def fetch_text_with_retry(
    url: str,
    config_path: Optional[Path] = None,
    **kwargs
) -> str:
    """
    Fetch text data from a URL with retry logic.

    Args:
        url: The URL to fetch text from.
        config_path: Optional path to config file.
        **kwargs: Additional arguments for the request.

    Returns:
        The response text content.

    Raises:
        FetchError: If all retry attempts fail.
    """
    response = fetch_with_retry(url, config_path=config_path, **kwargs)

    if isinstance(response, requests.Response):
        return response.text
    elif isinstance(response, str):
        return response
    else:
        raise FetchError(f"Unexpected response type: {type(response)}")

def extract_and_validate_instrumentation(
    metadata: Dict[str, Any],
    config_path: Optional[Path] = None
) -> Tuple[Optional[str], Optional[str], bool]:
    """
    Extract and validate instrumentation metadata from source data.

    Args:
        metadata: Dictionary containing source metadata.
        config_path: Optional path to config file.

    Returns:
        Tuple of (instrument_model, manufacturer, is_valid)
        Returns (None, None, False) if instrumentation is missing.
    """
    instrument_model = metadata.get('instrument_model')
    manufacturer = metadata.get('manufacturer')

    # Validate that at least one field is present
    if instrument_model or manufacturer:
        return instrument_model, manufacturer, True
    else:
        logger.warning("Missing instrumentation metadata in source data")
        return None, None, False

def main():
    """
    Main function to demonstrate retry logic with a test URL.
    """
    # Example usage with a test URL
    test_urls = [
        "https://httpbin.org/status/200",  # Should succeed
        "https://httpbin.org/status/500",  # Should fail after retries
    ]

    for url in test_urls:
        try:
            logger.info(f"\n--- Testing: {url} ---")
            response = fetch_with_retry(url)
            logger.info(f"Success! Status: {response.status_code}")
        except FetchError as e:
            logger.error(f"Failed: {e}")

    # Show configuration values
    try:
        config = load_config()
        retry_config = config.get('retry', {})
        logger.info("\n--- Configuration ---")
        logger.info(f"Max attempts: {retry_config.get('max_attempts')}")
        logger.info(f"Base delay: {retry_config.get('base_delay_seconds')}s")
        logger.info(f"Delay multiplier: {retry_config.get('delay_multiplier')}")
        logger.info(f"Max delay: {retry_config.get('max_delay_seconds')}s")
    except Exception as e:
        logger.error(f"Could not load config: {e}")

if __name__ == "__main__":
    main()
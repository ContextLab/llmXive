"""
Generic helper functions for the A/B test audit pipeline.

This module provides utility functions for:
- Computing file checksums
- Extracting domain names from URLs
- Safely parsing float values from strings
- Parsing inequality p-values (e.g., "p < 0.05", "p > 0.1")
"""
import hashlib
import re
from urllib.parse import urlparse
from typing import Optional, Tuple, Union


def checksum(file_path: str, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file.

    Args:
        file_path: Path to the file to hash.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal digest of the file's hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    hash_obj = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(8192), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def domain_from_url(url: str) -> Optional[str]:
    """
    Extract the domain name from a URL.

    Args:
        url: The URL string to parse.

    Returns:
        The domain name (e.g., 'example.com') or None if parsing fails.
    """
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            # Try parsing with scheme if missing
            parsed = urlparse("http://" + url)
        return parsed.netloc.lower()
    except Exception:
        return None


def safe_float(value: Union[str, float, int, None], default: Optional[float] = None) -> Optional[float]:
    """
    Safely convert a value to a float.

    Args:
        value: The value to convert (string, int, float, or None).
        default: Value to return if conversion fails (default: None).

    Returns:
        The float value, or the default if conversion fails.
    """
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return default
        try:
            return float(value)
        except ValueError:
            # Handle scientific notation or other edge cases if necessary
            return default
    return default


def parse_inequality_p(p_value_str: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Parse a p-value string that may contain an inequality operator.

    Handles formats like:
    - "0.03" -> (0.03, None)
    - "< 0.05" -> (0.05, "<")
    - "> 0.1" -> (0.1, ">")
    - "p < 0.01" -> (0.01, "<")
    - "p > 0.05" -> (0.05, ">")

    Args:
        p_value_str: The string containing the p-value and optional inequality.

    Returns:
        A tuple of (numeric_value, operator).
        If no inequality is found, operator is None.
        If parsing fails, both values are None.
    """
    if not isinstance(p_value_str, str):
        return None, None

    p_value_str = p_value_str.strip().lower()

    # Remove leading 'p' or 'p-value' if present
    p_value_str = re.sub(r'^p[-\s]*value?\s*[:=]?\s*', '', p_value_str)
    p_value_str = p_value_str.strip()

    operator = None
    numeric_value = None

    # Check for inequality operators at the start
    if p_value_str.startswith('<'):
        operator = '<'
        p_value_str = p_value_str[1:].strip()
    elif p_value_str.startswith('>'):
        operator = '>'
        p_value_str = p_value_str[1:].strip()
    elif p_value_str.startswith('<='):
        operator = '<='
        p_value_str = p_value_str[2:].strip()
    elif p_value_str.startswith('>='):
        operator = '>='
        p_value_str = p_value_str[2:].strip()

    try:
        numeric_value = float(p_value_str)
        return numeric_value, operator
    except ValueError:
        return None, None

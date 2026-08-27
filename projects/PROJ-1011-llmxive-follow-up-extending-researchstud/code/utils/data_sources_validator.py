"""
Validator for data-sources.yaml configuration.
Ensures required fields are present and URLs are valid formats.
"""
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from utils.error_handling import ValidationError

logger = logging.getLogger(__name__)

# Required top-level keys for a source entry
REQUIRED_SOURCE_KEYS = {
    "name",
    "type",
    "endpoint",
    "params",
}

# Allowed types for sources
ALLOWED_SOURCE_TYPES = {"arxiv", "doi", "api"}

# Regex for URL validation (basic, covers http/https)
URL_REGEX = re.compile(
    r"^https?://"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
    r"localhost|"  # localhost...
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)

# Regex for DOI validation
DOI_REGEX = re.compile(
    r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$",
    re.IGNORECASE,
)


def validate_url_format(url: str) -> bool:
    """
    Validate that a string is a well-formed HTTP/HTTPS URL.
    """
    if not isinstance(url, str) or not url.strip():
        return False
    return bool(URL_REGEX.match(url.strip()))


def validate_endpoint(endpoint: Any) -> bool:
    """
    Validate the 'endpoint' field.
    - If type is 'arxiv', endpoint must be a valid URL.
    - If type is 'doi', endpoint can be a list of DOIs or a single DOI string.
    - If type is 'api', endpoint must be a valid URL.
    """
    if not isinstance(endpoint, (str, list)):
        return False

    if isinstance(endpoint, str):
        endpoint = endpoint.strip()
        # If it looks like a DOI list or single DOI, validate as such
        if endpoint.startswith("10."):
            return bool(DOI_REGEX.match(endpoint))
        # Otherwise treat as URL
        return validate_url_format(endpoint)

    if isinstance(endpoint, list):
        if not endpoint:
            return False
        # All items must be valid DOIs if the first one looks like a DOI
        is_doi_list = all(
            isinstance(item, str) and bool(DOI_REGEX.match(item.strip()))
            for item in endpoint
        )
        if is_doi_list:
            return True
        # Otherwise, treat as list of URLs
        return all(isinstance(item, str) and validate_url_format(item.strip()) for item in endpoint)

    return False


def validate_source(source: Dict[str, Any]) -> None:
    """
    Validate a single source entry.
    Raises ValidationError if validation fails.
    """
    if not isinstance(source, dict):
        raise ValidationError(f"Source entry must be a dictionary, got {type(source)}")

    missing_keys = REQUIRED_SOURCE_KEYS - set(source.keys())
    if missing_keys:
        raise ValidationError(f"Source missing required keys: {missing_keys}")

    source_type = source.get("type")
    if source_type not in ALLOWED_SOURCE_TYPES:
        raise ValidationError(f"Invalid source type '{source_type}'. Allowed: {ALLOWED_SOURCE_TYPES}")

    endpoint = source.get("endpoint")
    if not validate_endpoint(endpoint):
        raise ValidationError(f"Invalid endpoint format for source '{source.get('name')}': {endpoint}")

    params = source.get("params")
    if not isinstance(params, dict):
        raise ValidationError(f"'params' must be a dictionary for source '{source.get('name')}'")


def validate_data_sources_config(config: Dict[str, Any]) -> None:
    """
    Validate the entire data-sources.yaml configuration.
    Expects a dictionary with a 'sources' key containing a list of source dicts.
    Raises ValidationError if validation fails.
    """
    if not isinstance(config, dict):
        raise ValidationError("Configuration must be a dictionary")

    if "sources" not in config:
        raise ValidationError("Configuration must contain a 'sources' key")

    sources = config["sources"]
    if not isinstance(sources, list):
        raise ValidationError("'sources' must be a list")

    if not sources:
        raise ValidationError("'sources' list cannot be empty")

    for i, source in enumerate(sources):
        try:
            validate_source(source)
        except ValidationError as e:
            raise ValidationError(f"Validation failed for source at index {i}: {e}")


def load_and_validate_config(config_path: Path) -> Dict[str, Any]:
    """
    Load the data-sources.yaml file and validate its contents.
    Returns the parsed configuration if valid.
    Raises ValidationError if the file cannot be loaded or is invalid.
    """
    if not config_path.exists():
        raise ValidationError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValidationError(f"Failed to parse YAML: {e}")
    except Exception as e:
        raise ValidationError(f"Failed to read configuration file: {e}")

    validate_data_sources_config(config)
    logger.info(f"Configuration validated successfully: {config_path}")
    return config
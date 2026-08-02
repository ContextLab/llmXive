"""
Error Contract Module for llmXive Research Pipeline.

Implements strict error handling and data validation contracts:
1. Exit code 1 on HTTP 404, timeout > 60s, or schema mismatch.
2. Immediate checksum verification upon download to ensure reproducibility.
3. Schema validation against contracts/dataset.schema.yaml.
"""

import os
import sys
import hashlib
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import yaml

# Constants
DEFAULT_TIMEOUT = 60  # seconds
CHECKSUM_ALGORITHM = 'sha256'


class ContractViolationError(Exception):
    """Raised when a data contract (schema, checksum, or HTTP status) is violated."""
    pass


def calculate_checksum(file_path: Path, algorithm: str = CHECKSUM_ALGORITHM) -> str:
    """
    Calculate the checksum of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal digest of the file.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for checksum calculation: {file_path}")

    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """
    Load a YAML schema from a file.

    Args:
        schema_path: Path to the schema YAML file.

    Returns:
        Parsed schema dictionary.

    Raises:
        FileNotFoundError: If schema file not found.
        yaml.YAMLError: If schema is invalid YAML.
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def validate_schema(data_path: Path, schema: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate a data file against a loaded schema.
    Currently supports basic structural validation for CSV/TSV/JSON.
    For complex validation, this integrates with utils/schema_validator.py concepts.

    Args:
        data_path: Path to the data file.
        schema: The schema dictionary.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not data_path.exists():
        return False, "Data file does not exist."

    # Basic validation logic based on schema type
    file_type = schema.get("type", "unknown")
    required_columns = schema.get("required_columns", [])

    if file_type == "csv" or file_type == "tsv":
        import pandas as pd
        try:
            df = pd.read_csv(data_path) if file_type == "csv" else pd.read_csv(data_path, sep='\t')
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                return False, f"Missing required columns: {missing_cols}"
            return True, None
        except Exception as e:
            return False, f"Failed to parse or validate CSV/TSV: {str(e)}"

    elif file_type == "json":
        import json
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Basic structure check if schema expects a list of objects
            if isinstance(data, list) and required_columns:
                if not data:
                    return False, "JSON list is empty but schema expects data."
                first_item = data[0]
                missing_keys = [col for col in required_columns if col not in first_item]
                if missing_keys:
                    return False, f"Missing required keys in JSON objects: {missing_keys}"
            return True, None
        except Exception as e:
            return False, f"Failed to parse or validate JSON: {str(e)}"

    else:
        # Unknown type, assume valid if file exists (strictness can be adjusted)
        return True, None


def download_with_contract(
    url: str,
    output_path: Path,
    expected_checksum: Optional[str] = None,
    schema_path: Optional[Path] = None,
    timeout: int = DEFAULT_TIMEOUT
) -> Path:
    """
    Download a file with strict contract enforcement.

    Contracts enforced:
    1. HTTP Status: Must be 200. Raises ContractViolationError on 404 or other errors.
    2. Timeout: Must complete within `timeout` seconds (default 60s).
    3. Checksum: If `expected_checksum` is provided, verify immediately after download.
    4. Schema: If `schema_path` is provided, validate the downloaded file content.

    Args:
        url: URL to download from.
        output_path: Local path to save the file.
        expected_checksum: Expected SHA-256 hex digest.
        schema_path: Path to YAML schema for content validation.
        timeout: Maximum seconds to wait for download.

    Returns:
        Path to the downloaded file.

    Raises:
        ContractViolationError: On HTTP error, timeout, checksum mismatch, or schema failure.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. & 2. HTTP Request with Timeout
    start_time = time.time()
    try:
        response = requests.get(url, stream=True, timeout=timeout)
    except requests.exceptions.Timeout:
        raise ContractViolationError(
            f"Download timed out after {timeout} seconds for {url}"
        )
    except requests.exceptions.RequestException as e:
        raise ContractViolationError(f"Network error during download: {str(e)}")

    elapsed = time.time() - start_time
    if elapsed > timeout:
        # Should be caught by exception, but double check for safety
        raise ContractViolationError(f"Download exceeded timeout ({elapsed:.2f}s > {timeout}s)")

    if response.status_code == 404:
        raise ContractViolationError(f"Resource not found (404) at {url}")
    elif response.status_code != 200:
        raise ContractViolationError(f"HTTP error {response.status_code} for {url}")

    # Download content
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    # 3. Checksum Verification
    if expected_checksum:
        actual_checksum = calculate_checksum(output_path)
        if actual_checksum.lower() != expected_checksum.lower():
            raise ContractViolationError(
                f"Checksum mismatch for {output_path}. "
                f"Expected: {expected_checksum}, Got: {actual_checksum}"
            )

    # 4. Schema Validation
    if schema_path:
        try:
            schema = load_schema(schema_path)
            is_valid, error_msg = validate_schema(output_path, schema)
            if not is_valid:
                raise ContractViolationError(f"Schema validation failed: {error_msg}")
        except FileNotFoundError as e:
            # If schema file is missing, we might want to fail loudly or warn
            # Given "strict error contract", missing schema definition is a violation
            raise ContractViolationError(f"Schema file missing: {e}")

    return output_path


def enforce_error_contract(func):
    """
    Decorator to enforce error contract on a function.
    Catches ContractViolationError and ensures exit code 1.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ContractViolationError as e:
            print(f"Contract Violation: {str(e)}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            # Unexpected errors also cause exit 1 to prevent silent failures
            print(f"Unexpected error: {str(e)}", file=sys.stderr)
            sys.exit(1)
    return wrapper

"""
Downloader module for fetching and validating TELBench dataset.
Implements validation logic to handle malformed JSON and missing fields gracefully.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import ensure_directories
from hasher import verify_file_hash


class ValidationError(Exception):
    """Raised when data validation fails."""
    pass


def validate_trajectory_record(record: Dict[str, Any], record_id: str) -> Tuple[bool, List[str]]:
    """
    Validate a single trajectory record from TELBench.

    Checks for:
    - Presence of required fields: 'id', 'spans'
    - 'spans' must be a non-empty list
    - Each span must contain 'content' and 'step_id' (or similar core fields)

    Args:
        record: The dictionary representing a single trajectory.
        record_id: Identifier for the record (for error reporting).

    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    errors = []

    # Check top-level required fields
    if 'id' not in record:
        errors.append(f"Record {record_id}: Missing required field 'id'")
    
    if 'spans' not in record:
        errors.append(f"Record {record_id}: Missing required field 'spans'")
        return False, errors

    spans = record.get('spans')
    
    if not isinstance(spans, list):
        errors.append(f"Record {record_id}: Field 'spans' must be a list, got {type(spans).__name__}")
        return False, errors

    if len(spans) == 0:
        errors.append(f"Record {record_id}: Field 'spans' is empty")
        return False, errors

    # Validate individual spans
    required_span_fields = {'content', 'step_id'}
    for i, span in enumerate(spans):
        if not isinstance(span, dict):
            errors.append(f"Record {record_id}, span {i}: Span must be a dict, got {type(span).__name__}")
            continue
        
        missing_fields = required_span_fields - set(span.keys())
        if missing_fields:
            errors.append(
                f"Record {record_id}, span {i}: Missing fields {missing_fields}"
            )

    return len(errors) == 0, errors


def validate_json_file(file_path: Path) -> Tuple[int, int, List[str]]:
    """
    Validate a JSON file containing a list of trajectory records.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Tuple of (valid_count, total_count, list_of_error_messages).
        valid_count: Number of records that passed validation.
        total_count: Total number of records processed.
        errors: List of validation error strings.
    """
    errors = []
    valid_count = 0
    total_count = 0

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Malformed JSON in {file_path}: {e}")
    
    if not isinstance(data, list):
        raise ValidationError(
            f"Invalid structure in {file_path}: Expected a list of records, got {type(data).__name__}"
        )

    total_count = len(data)

    for i, record in enumerate(data):
        is_valid, record_errors = validate_trajectory_record(record, f"index_{i}")
        if is_valid:
            valid_count += 1
        else:
            errors.extend(record_errors)

    return valid_count, total_count, errors


def fetch_and_validate(
    dataset_id: str,
    output_path: Path,
    expected_hash: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch dataset from HuggingFace, save to disk, and validate.

    Note: This implementation uses the 'datasets' library to fetch the real data.
    It strictly fails if the real source is unreachable or data is invalid.
    No synthetic fallback is provided.

    Args:
        dataset_id: HuggingFace dataset ID (e.g., 'HuggingFaceH4/tebench').
        output_path: Path where the JSON file should be saved.
        expected_hash: Optional SHA256 hash to verify the downloaded file.

    Returns:
        Dictionary with validation results.
    """
    ensure_directories()
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from datasets import load_dataset
    except ImportError:
        raise ImportError(
            "The 'datasets' library is required. "
            "Install it with: pip install datasets"
        )

    # Fetch the real dataset
    # Using streaming=False to download the full split for validation
    # The task requires real data, so we fetch the 'train' split.
    try:
        dataset = load_dataset(dataset_id, split="train")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch dataset '{dataset_id}': {e}")

    # Convert to list of dicts and save as JSON
    # The TELBench dataset structure needs to be handled. 
    # Assuming standard structure: list of trajectories.
    # We serialize the dataset to a JSON file.
    records = dataset.to_list()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)

    # Verify hash if provided
    if expected_hash:
        is_hash_valid = verify_file_hash(output_path, expected_hash)
        if not is_hash_valid:
            raise ValidationError(
                f"Checksum verification failed for {output_path}. "
                "The downloaded file does not match the expected hash."
            )

    # Validate the content
    valid_count, total_count, errors = validate_json_file(output_path)

    return {
        "file_path": str(output_path),
        "total_records": total_count,
        "valid_records": valid_count,
        "invalid_records": total_count - valid_count,
        "validation_errors": errors,
        "is_valid": valid_count == total_count and total_count > 0
    }

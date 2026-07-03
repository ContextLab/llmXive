"""
Schema validator for Colony entities.
Validates against specs/001-gene-regulation/contracts/dataset.schema.yaml
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import json
import re


@dataclass
class ColonySchema:
    """
    Defines the expected schema for a Colony record.
    Corresponds to the 'dataset.schema.yaml' definition for Colony entities.
    """
    # Required fields
    colony_id: str
    sampling_date: str  # ISO 8601 format
    geographic_region: str
    sampling_year: int

    # Optional but expected fields
    varroa_load: Optional[float] = None
    hive_status: Optional[str] = None  # e.g., 'healthy', 'ccd_suspect', 'collapsed'
    notes: Optional[str] = None

    # Metadata for validation
    required_fields: List[str] = field(default_factory=lambda: [
        "colony_id", "sampling_date", "geographic_region", "sampling_year"
    ])
    valid_hive_statuses: List[str] = field(default_factory=lambda: [
        "healthy", "ccd_suspect", "collapsed"
    ])


def validate_colony_data(data: Dict[str, Any]) -> List[str]:
    """
    Validates a single colony record against the ColonySchema.

    Args:
        data: A dictionary representing a single colony record.

    Returns:
        A list of error messages. Empty if validation passes.
    """
    errors = []
    schema = ColonySchema()

    # Check required fields
    for field_name in schema.required_fields:
        if field_name not in data:
            errors.append(f"Missing required field: {field_name}")
        elif data[field_name] is None or data[field_name] == "":
            errors.append(f"Field '{field_name}' cannot be empty.")

    # Validate types for required fields
    if "colony_id" in data and not isinstance(data["colony_id"], str):
        errors.append("colony_id must be a string.")

    if "sampling_year" in data:
        if not isinstance(data["sampling_year"], int):
            errors.append("sampling_year must be an integer.")
        elif data["sampling_year"] < 1900 or data["sampling_year"] > 2100:
            errors.append("sampling_year must be between 1900 and 2100.")

    if "sampling_date" in data:
        if not isinstance(data["sampling_date"], str):
            errors.append("sampling_date must be a string (ISO 8601).")
        else:
            # Basic ISO 8601 check (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
            iso_pattern = r'^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2})?$'
            if not re.match(iso_pattern, data["sampling_date"]):
                errors.append(f"sampling_date '{data['sampling_date']}' is not in valid ISO 8601 format.")

    if "geographic_region" in data and not isinstance(data["geographic_region"], str):
        errors.append("geographic_region must be a string.")

    # Validate optional fields if present
    if "hive_status" in data and data["hive_status"] is not None:
        if data["hive_status"] not in schema.valid_hive_statuses:
            errors.append(
                f"Invalid hive_status: '{data['hive_status']}'. "
                f"Must be one of: {schema.valid_hive_statuses}"
            )

    if "varroa_load" in data and data["varroa_load"] is not None:
        if not isinstance(data["varroa_load"], (int, float)):
            errors.append("varroa_load must be a number.")
        elif data["varroa_load"] < 0:
            errors.append("varroa_load cannot be negative.")

    return errors


def validate_colony_batch(data_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validates a batch of colony records.

    Args:
        data_batch: A list of dictionaries, each representing a colony record.

    Returns:
        A dictionary with 'valid_count', 'invalid_count', and 'errors' list.
    """
    errors = []
    valid_count = 0
    invalid_count = 0

    for i, record in enumerate(data_batch):
        record_errors = validate_colony_data(record)
        if record_errors:
            invalid_count += 1
            for err in record_errors:
                errors.append(f"Record {i}: {err}")
        else:
            valid_count += 1

    return {
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "errors": errors
    }

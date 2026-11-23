"""
Data validation module for NIST reference data.

This module provides functions to validate the existence, schema, and checksum
of the nist_refs.json file. It raises specific errors if validation fails.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Import from sibling modules
from utils.checksums import calculate_sha256, verify_file_hash
from config import NIST_REFS_PATH, MANIFEST_PATH


@dataclass
class ValidationResult:
    """Result of a validation check."""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class DataValidationError(Exception):
    """Custom exception for data validation errors."""
    pass


def validate_nist_refs_exists() -> ValidationResult:
    """
    Check if the nist_refs.json file exists.

    Returns:
        ValidationResult: Success status and message.

    Raises:
        DataValidationError: If the file does not exist.
    """
    if not os.path.exists(NIST_REFS_PATH):
        raise DataValidationError(
            f"Data file not found: {NIST_REFS_PATH}. "
            "Please ensure the file has been generated or downloaded."
        )
    return ValidationResult(
        success=True,
        message=f"File exists: {NIST_REFS_PATH}"
    )


def validate_nist_refs_schema() -> ValidationResult:
    """
    Validate the schema of the nist_refs.json file.

    Expected schema:
    [
      {
        "solvent": str,
        "temperature": float,
        "value": float,
        "unit": str,
        "reference": str,
        "method": str
      },
      ...
    ]

    Returns:
        ValidationResult: Success status and message.

    Raises:
        DataValidationError: If the file is missing, malformed, or schema is invalid.
    """
    # Check existence first
    if not os.path.exists(NIST_REFS_PATH):
        raise DataValidationError(
            f"Data file not found for schema validation: {NIST_REFS_PATH}"
        )

    try:
        with open(NIST_REFS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise DataValidationError(
            f"Invalid JSON format in {NIST_REFS_PATH}: {str(e)}"
        )
    except Exception as e:
        raise DataValidationError(
            f"Error reading {NIST_REFS_PATH}: {str(e)}"
        )

    # Validate structure
    if not isinstance(data, list):
        raise DataValidationError(
            f"Schema error: Expected a list at the root of {NIST_REFS_PATH}, got {type(data).__name__}"
        )

    if len(data) == 0:
        raise DataValidationError(
            f"Schema error: The list in {NIST_REFS_PATH} is empty."
        )

    required_fields = ['solvent', 'temperature', 'value', 'unit', 'reference', 'method']

    for i, entry in enumerate(data):
        if not isinstance(entry, dict):
            raise DataValidationError(
                f"Schema error at index {i}: Expected a dictionary, got {type(entry).__name__}"
            )

        missing_fields = [field for field in required_fields if field not in entry]
        if missing_fields:
            raise DataValidationError(
                f"Schema error at index {i}: Missing required fields: {missing_fields}"
            )

        # Type validation
        if not isinstance(entry['solvent'], str):
            raise DataValidationError(
                f"Schema error at index {i}: 'solvent' must be a string"
            )
        if not isinstance(entry['temperature'], (int, float)):
            raise DataValidationError(
                f"Schema error at index {i}: 'temperature' must be a number"
            )
        if not isinstance(entry['value'], (int, float)):
            raise DataValidationError(
                f"Schema error at index {i}: 'value' must be a number"
            )
        if not isinstance(entry['unit'], str):
            raise DataValidationError(
                f"Schema error at index {i}: 'unit' must be a string"
            )
        if not isinstance(entry['reference'], str):
            raise DataValidationError(
                f"Schema error at index {i}: 'reference' must be a string"
            )
        if not isinstance(entry['method'], str):
            raise DataValidationError(
                f"Schema error at index {i}: 'method' must be a string"
            )

    return ValidationResult(
        success=True,
        message=f"Schema validation passed for {NIST_REFS_PATH} ({len(data)} entries)"
    )


def validate_nist_refs_checksum() -> ValidationResult:
    """
    Validate the checksum of nist_refs.json against the manifest.

    Returns:
        ValidationResult: Success status and message.

    Raises:
        DataValidationError: If the checksum does not match or manifest is missing.
    """
    # Check if manifest exists
    if not os.path.exists(MANIFEST_PATH):
        raise DataValidationError(
            f"Manifest file not found: {MANIFEST_PATH}. "
            "Please run the manifest initialization script first."
        )

    try:
        with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        raise DataValidationError(
            f"Invalid JSON format in manifest {MANIFEST_PATH}: {str(e)}"
        )
    except Exception as e:
        raise DataValidationError(
            f"Error reading manifest {MANIFEST_PATH}: {str(e)}"
        )

    # Find entry for nist_refs.json
    nist_entry = None
    for entry in manifest.get('files', []):
        if entry.get('path') == NIST_REFS_PATH:
            nist_entry = entry
            break

    if not nist_entry:
        raise DataValidationError(
            f"Checksum entry for {NIST_REFS_PATH} not found in manifest {MANIFEST_PATH}"
        )

    expected_checksum = nist_entry.get('checksum')
    if not expected_checksum:
        raise DataValidationError(
            f"Checksum missing for {NIST_REFS_PATH} in manifest"
        )

    # Calculate current checksum
    try:
        current_checksum = calculate_sha256(NIST_REFS_PATH)
    except Exception as e:
        raise DataValidationError(
            f"Error calculating checksum for {NIST_REFS_PATH}: {str(e)}"
        )

    if current_checksum != expected_checksum:
        raise DataValidationError(
            f"Checksum mismatch for {NIST_REFS_PATH}!\n"
            f"  Expected: {expected_checksum}\n"
            f"  Current:  {current_checksum}\n"
            f"  File may have been modified or corrupted."
        )

    return ValidationResult(
        success=True,
        message=f"Checksum validation passed for {NIST_REFS_PATH}"
    )


def validate_nist_refs() -> List[ValidationResult]:
    """
    Run all validations on nist_refs.json.

    Returns:
        List[ValidationResult]: Results of all validation checks.

    Raises:
        DataValidationError: If any validation fails.
    """
    results = []

    # 1. Check existence
    try:
        results.append(validate_nist_refs_exists())
    except DataValidationError as e:
        raise e

    # 2. Check schema
    try:
        results.append(validate_nist_refs_schema())
    except DataValidationError as e:
        raise e

    # 3. Check checksum
    try:
        results.append(validate_nist_refs_checksum())
    except DataValidationError as e:
        raise e

    return results


def main():
    """Main entry point for running validation."""
    print(f"Starting validation for {NIST_REFS_PATH}...")

    try:
        results = validate_nist_refs()
        print("\nValidation Summary:")
        for result in results:
            status = "✓ PASS" if result.success else "✗ FAIL"
            print(f"  {status}: {result.message}")

        print("\nAll validations passed successfully!")
        return 0

    except DataValidationError as e:
        print(f"\n✗ VALIDATION FAILED: {str(e)}")
        return 1
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

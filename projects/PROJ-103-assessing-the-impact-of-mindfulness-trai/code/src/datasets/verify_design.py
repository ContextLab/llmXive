"""
Dataset Design Verification Module.

Verifies that downloaded datasets contain the required pre/post resting-state scans
with mindfulness intervention metadata as per User Story 1 requirements.
"""

import re
import os
import json
from typing import Dict, Any, List, Tuple
from pathlib import Path

from src.config.env import get_data_dir


class DesignVerificationError(Exception):
    """Raised when dataset design verification fails."""
    pass


def validate_metadata_fields(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates that required metadata fields are present and of correct types.

    Required fields:
    - pre_scan_count: int
    - post_scan_count: int
    - intervention_type: str
    - scan_type: str

    Args:
        metadata: Dictionary containing dataset metadata.

    Returns:
        Tuple of (is_valid, list_of_missing_or_invalid_fields).
    """
    required_fields = {
        'pre_scan_count': int,
        'post_scan_count': int,
        'intervention_type': str,
        'scan_type': str
    }

    errors = []

    for field_name, expected_type in required_fields.items():
        if field_name not in metadata:
            errors.append(f"Missing required field: {field_name}")
            continue

        value = metadata[field_name]
        if not isinstance(value, expected_type):
            errors.append(
                f"Field '{field_name}' has invalid type: "
                f"expected {expected_type.__name__}, got {type(value).__name__}"
            )

    return len(errors) == 0, errors


def validate_design_logic(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates the logical constraints of the dataset design.

    Rules:
    1. pre_scan_count > 0
    2. post_scan_count > 0
    3. intervention_type matches regex 'mindfulness|MBSR|MBC' (case-insensitive)
    4. scan_type equals 'rs-fMRI' or 'resting'

    Args:
        metadata: Dictionary containing dataset metadata.

    Returns:
        Tuple of (is_valid, list_of_logic_violations).
    """
    errors = []

    # Check scan counts
    if metadata.get('pre_scan_count', 0) <= 0:
        errors.append("pre_scan_count must be greater than 0")

    if metadata.get('post_scan_count', 0) <= 0:
        errors.append("post_scan_count must be greater than 0")

    # Check intervention type
    intervention_type = metadata.get('intervention_type', '')
    mindfulness_pattern = re.compile(r'mindfulness|MBSR|MBC', re.IGNORECASE)
    if not mindfulness_pattern.search(intervention_type):
        errors.append(
            f"intervention_type '{intervention_type}' does not match "
            f"required pattern (mindfulness|MBSR|MBC)"
        )

    # Check scan type
    scan_type = metadata.get('scan_type', '')
    valid_scan_types = {'rs-fMRI', 'resting'}
    if scan_type not in valid_scan_types:
        errors.append(
            f"scan_type '{scan_type}' must be one of: {valid_scan_types}"
        )

    return len(errors) == 0, errors


def verify_dataset_design(dataset_id: str, metadata_path: str = None) -> Dict[str, Any]:
    """
    Verifies the design of a specific dataset.

    Args:
        dataset_id: The ID of the dataset to verify.
        metadata_path: Optional path to a JSON metadata file. If not provided,
                     attempts to load from data/raw/{dataset_id}/dataset_description.json
                     or a generated metadata file.

    Returns:
        Dictionary containing verification results:
        {
            "dataset_id": str,
            "verified": bool,
            "field_validation": {"valid": bool, "errors": list},
            "logic_validation": {"valid": bool, "errors": list},
            "metadata": dict (if found),
            "message": str
        }
    """
    data_dir = Path(get_data_dir())
    dataset_path = data_dir / dataset_id

    # Determine metadata source
    if metadata_path and os.path.exists(metadata_path):
        metadata_file = Path(metadata_path)
    elif (dataset_path / "dataset_description.json").exists():
        metadata_file = dataset_path / "dataset_description.json"
    else:
        # Try to find a generated metadata file
        possible_files = list(dataset_path.glob("*_metadata.json"))
        if possible_files:
            metadata_file = possible_files[0]
        else:
            return {
                "dataset_id": dataset_id,
                "verified": False,
                "field_validation": {"valid": False, "errors": ["No metadata file found"]},
                "logic_validation": {"valid": False, "errors": []},
                "metadata": None,
                "message": f"Could not locate metadata file for dataset {dataset_id}"
            }

    try:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    except json.JSONDecodeError as e:
        return {
            "dataset_id": dataset_id,
            "verified": False,
            "field_validation": {"valid": False, "errors": [f"Invalid JSON: {str(e)}"]},
            "logic_validation": {"valid": False, "errors": []},
            "metadata": None,
            "message": f"Failed to parse metadata file: {str(e)}"
        }

    # Validate fields
    fields_valid, field_errors = validate_metadata_fields(metadata)

    # Validate logic
    logic_valid, logic_errors = validate_design_logic(metadata)

    verified = fields_valid and logic_valid

    return {
        "dataset_id": dataset_id,
        "verified": verified,
        "field_validation": {
            "valid": fields_valid,
            "errors": field_errors
        },
        "logic_validation": {
            "valid": logic_valid,
            "errors": logic_errors
        },
        "metadata": metadata,
        "message": "Design verification passed" if verified else "Design verification failed"
    }


def verify_all_datasets(dataset_ids: List[str] = None) -> List[Dict[str, Any]]:
    """
    Verifies the design of multiple datasets.

    Args:
        dataset_ids: List of dataset IDs to verify. If None, attempts to discover
                     all datasets in the data/raw directory.

    Returns:
        List of verification result dictionaries.
    """
    if dataset_ids is None:
        data_dir = Path(get_data_dir())
        raw_dir = data_dir / "raw"
        if not raw_dir.exists():
            return []
        dataset_ids = [d.name for d in raw_dir.iterdir() if d.is_dir()]

    results = []
    for dataset_id in dataset_ids:
        result = verify_dataset_design(dataset_id)
        results.append(result)

    return results


def main():
    """
    Main entry point for command-line execution.
    Verifies all datasets found in the data/raw directory.
    """
    print("Starting dataset design verification...")
    results = verify_all_datasets()

    if not results:
        print("No datasets found to verify.")
        return

    passed_count = sum(1 for r in results if r["verified"])
    total_count = len(results)

    print(f"\nVerification Summary: {passed_count}/{total_count} datasets passed.")

    for result in results:
        status = "PASS" if result["verified"] else "FAIL"
        print(f"\n[{status}] Dataset: {result['dataset_id']}")

        if not result["field_validation"]["valid"]:
            print("  Field Errors:")
            for err in result["field_validation"]["errors"]:
                print(f"    - {err}")

        if not result["logic_validation"]["valid"]:
            print("  Logic Errors:")
            for err in result["logic_validation"]["errors"]:
                print(f"    - {err}")

        if result["verified"]:
            print("  Design verified successfully.")


if __name__ == "__main__":
    main()

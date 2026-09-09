"""
Dataset design verification module for mindfulness training studies.

This module validates that downloaded datasets contain the required
pre/post resting-state scans with mindfulness intervention metadata.
"""

import re
import os
import json
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass
from src.config.env import get_data_dir


class DesignVerificationError(Exception):
    """Exception raised when dataset design verification fails."""
    pass


@dataclass
class DesignMetadata:
    """Container for verified dataset design metadata."""
    pre_scan_count: int
    post_scan_count: int
    intervention_type: str
    scan_type: str
    dataset_id: str
    verified: bool
    errors: List[str]

def validate_metadata_fields(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that required metadata fields are present and have correct types.

    Args:
        metadata: Dictionary containing dataset metadata

    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    errors = []
    required_fields = {
        'pre_scan_count': int,
        'post_scan_count': int,
        'intervention_type': str,
        'scan_type': str
    }

    for field, expected_type in required_fields.items():
        if field not in metadata:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(metadata[field], expected_type):
            errors.append(f"Field '{field}' must be of type {expected_type.__name__}, got {type(metadata[field]).__name__}")

    # Validate non-negative scan counts
    if 'pre_scan_count' in metadata and isinstance(metadata['pre_scan_count'], int):
        if metadata['pre_scan_count'] < 0:
            errors.append("pre_scan_count must be non-negative")

    if 'post_scan_count' in metadata and isinstance(metadata['post_scan_count'], int):
        if metadata['post_scan_count'] < 0:
            errors.append("post_scan_count must be non-negative")

    return len(errors) == 0, errors


def validate_design_logic(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate the logical constraints of the dataset design.

    Requirements:
    - pre_scan_count > 0
    - post_scan_count > 0
    - intervention_type matches regex 'mindfulness|MBSR|MBC' (case-insensitive)
    - scan_type equals 'rs-fMRI' or 'resting'

    Args:
        metadata: Dictionary containing dataset metadata

    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    errors = []

    # Check scan counts are positive
    if metadata.get('pre_scan_count', 0) <= 0:
        errors.append("pre_scan_count must be greater than 0")

    if metadata.get('post_scan_count', 0) <= 0:
        errors.append("post_scan_count must be greater than 0")

    # Validate intervention type
    intervention_type = metadata.get('intervention_type', '')
    mindfulness_pattern = re.compile(r'mindfulness|MBSR|MBC', re.IGNORECASE)
    if not mindfulness_pattern.search(intervention_type):
        errors.append(
            f"intervention_type '{intervention_type}' must match 'mindfulness|MBSR|MBC' (case-insensitive)"
        )

    # Validate scan type
    scan_type = metadata.get('scan_type', '')
    valid_scan_types = ['rs-fMRI', 'resting']
    if scan_type not in valid_scan_types:
        errors.append(f"scan_type '{scan_type}' must be one of {valid_scan_types}")

    return len(errors) == 0, errors


def verify_dataset_design(dataset_path: Path) -> DesignMetadata:
    """
    Verify the design of a single dataset.

    Looks for a design.json file in the dataset directory and validates
    its contents against the requirements.

    Args:
        dataset_path: Path to the dataset directory

    Returns:
        DesignMetadata object with verification results
    """
    dataset_id = dataset_path.name
    design_file = dataset_path / 'design.json'

    errors = []

    if not design_file.exists():
        errors.append("design.json file not found in dataset directory")
        return DesignMetadata(
            pre_scan_count=0,
            post_scan_count=0,
            intervention_type="",
            scan_type="",
            dataset_id=dataset_id,
            verified=False,
            errors=errors
        )

    try:
        with open(design_file, 'r') as f:
            metadata = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON in design.json: {str(e)}")
        return DesignMetadata(
            pre_scan_count=0,
            post_scan_count=0,
            intervention_type="",
            scan_type="",
            dataset_id=dataset_id,
            verified=False,
            errors=errors
        )

    # Validate metadata fields
    fields_valid, field_errors = validate_metadata_fields(metadata)
    errors.extend(field_errors)

    # Validate design logic
    logic_valid, logic_errors = validate_design_logic(metadata)
    errors.extend(logic_errors)

    return DesignMetadata(
        pre_scan_count=metadata.get('pre_scan_count', 0),
        post_scan_count=metadata.get('post_scan_count', 0),
        intervention_type=metadata.get('intervention_type', ''),
        scan_type=metadata.get('scan_type', ''),
        dataset_id=dataset_id,
        verified=len(errors) == 0,
        errors=errors
    )


def verify_all_datasets() -> List[DesignMetadata]:
    """
    Verify the design of all datasets in the raw data directory.

    Returns:
        List of DesignMetadata objects for each dataset
    """
    data_dir = Path(get_data_dir())
    raw_dir = data_dir / 'raw'

    if not raw_dir.exists():
        raise DesignVerificationError(f"Raw data directory not found: {raw_dir}")

    results = []

    for dataset_path in raw_dir.iterdir():
        if dataset_path.is_dir():
            result = verify_dataset_design(dataset_path)
            results.append(result)

    return results


def main():
    """Main entry point for dataset design verification."""
    print("Starting dataset design verification...")

    try:
        results = verify_all_datasets()

        if not results:
            print("No datasets found in raw data directory.")
            return

        verified_count = sum(1 for r in results if r.verified)
        total_count = len(results)

        print(f"\nVerification Results ({verified_count}/{total_count} verified):")
        print("-" * 60)

        for result in results:
            status = "✓ VERIFIED" if result.verified else "✗ FAILED"
            print(f"\nDataset: {result.dataset_id}")
            print(f"  Status: {status}")
            print(f"  Pre-scan count: {result.pre_scan_count}")
            print(f"  Post-scan count: {result.post_scan_count}")
            print(f"  Intervention type: {result.intervention_type}")
            print(f"  Scan type: {result.scan_type}")

            if result.errors:
                print(f"  Errors:")
                for error in result.errors:
                    print(f"    - {error}")

        print("\n" + "=" * 60)
        print(f"Summary: {verified_count} verified, {total_count - verified_count} failed")

        if verified_count != total_count:
            raise DesignVerificationError(
                f"Design verification failed for {total_count - verified_count} datasets"
            )

        print("All datasets passed design verification!")

    except DesignVerificationError as e:
        print(f"Design verification error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error during verification: {e}")
        raise


if __name__ == "__main__":
    main()
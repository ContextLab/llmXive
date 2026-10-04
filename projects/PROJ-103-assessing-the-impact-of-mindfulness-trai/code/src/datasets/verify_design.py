"""
Dataset design verification module for User Story 1.

Verifies that downloaded datasets contain the required mindfulness intervention
metadata and scan structure (pre/post resting-state scans).
"""
import re
import os
import json
import logging
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass

from src.config.env import get_data_dir

logger = logging.getLogger(__name__)


class DesignVerificationError(Exception):
    """Raised when design verification fails or data is missing."""
    pass


@dataclass
class DesignMetadata:
    """Container for verified design metadata."""
    pre_scan_count: int
    post_scan_count: int
    intervention_type: str
    scan_type: str
    dataset_id: str
    is_valid: bool
    validation_errors: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "pre_scan_count": self.pre_scan_count,
            "post_scan_count": self.post_scan_count,
            "intervention_type": self.intervention_type,
            "scan_type": self.scan_type,
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors
        }


def validate_metadata_fields(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that all required metadata fields are present and non-empty.

    Required fields:
    - pre_scan_count: int > 0
    - post_scan_count: int > 0
    - intervention_type: str matching mindfulness regex
    - scan_type: str matching 'rs-fMRI' or 'resting'

    Args:
        metadata: Dictionary containing dataset metadata.

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    required_fields = ["pre_scan_count", "post_scan_count", "intervention_type", "scan_type"]

    # Check presence of required fields
    for field in required_fields:
        if field not in metadata:
            errors.append(f"Missing required field: {field}")

    if errors:
        return False, errors

    # Validate pre_scan_count
    try:
        pre_count = int(metadata["pre_scan_count"])
        if pre_count <= 0:
            errors.append(f"pre_scan_count must be > 0, got {pre_count}")
    except (ValueError, TypeError):
        errors.append(f"pre_scan_count must be an integer, got {type(metadata['pre_scan_count']).__name__}")

    # Validate post_scan_count
    try:
        post_count = int(metadata["post_scan_count"])
        if post_count <= 0:
            errors.append(f"post_scan_count must be > 0, got {post_count}")
    except (ValueError, TypeError):
        errors.append(f"post_scan_count must be an integer, got {type(metadata['post_scan_count']).__name__}")

    # Validate intervention_type (case-insensitive regex)
    intervention_pattern = re.compile(r"^(mindfulness|MBSR|MBC)$", re.IGNORECASE)
    intervention = str(metadata["intervention_type"]).strip()
    if not intervention_pattern.match(intervention):
        errors.append(
            f"intervention_type must match 'mindfulness|MBSR|MBC' (case-insensitive), "
            f"got '{intervention}'"
        )

    # Validate scan_type
    scan_types_allowed = {"rs-fMRI", "resting"}
    scan_type = str(metadata["scan_type"]).strip()
    if scan_type not in scan_types_allowed:
        errors.append(
            f"scan_type must be one of {scan_types_allowed}, got '{scan_type}'"
        )

    return len(errors) == 0, errors


def validate_design_logic(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate the logical consistency of the design.

    Checks:
    - pre_scan_count > 0 AND post_scan_count > 0
    - intervention_type matches regex
    - scan_type is valid

    Args:
        metadata: Dictionary containing dataset metadata.

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    # Reuse field validation logic
    is_valid, errors = validate_metadata_fields(metadata)

    # Additional logical checks if field validation passed
    if is_valid:
        pre_count = int(metadata["pre_scan_count"])
        post_count = int(metadata["post_scan_count"])

        if pre_count == 0 or post_count == 0:
            errors.append("Design requires both pre and post scans (counts > 0)")
            is_valid = False

    return is_valid, errors


def verify_dataset_design(dataset_id: str, metadata_path: Optional[Path] = None) -> DesignMetadata:
    """
    Verify a single dataset's design against requirements.

    Looks for a design.json file in the dataset directory or accepts a direct path.

    Args:
        dataset_id: The OpenNeuro dataset ID (e.g., 'ds000001').
        metadata_path: Optional explicit path to the design metadata JSON file.

    Returns:
        DesignMetadata object with verification results.
    """
    data_dir = Path(get_data_dir())
    dataset_dir = data_dir / "raw" / dataset_id

    # Determine metadata file path
    if metadata_path and metadata_path.exists():
        meta_file = metadata_path
    else:
        # Standard location: data/raw/{dataset_id}/design.json
        meta_file = dataset_dir / "design.json"
        if not meta_file.exists():
            # Fallback: check for dataset_description.json if design.json missing
            # but for this task, we strictly require design.json per spec
            logger.warning(f"Design metadata file not found at {meta_file}")
            return DesignMetadata(
                pre_scan_count=0,
                post_scan_count=0,
                intervention_type="",
                scan_type="",
                dataset_id=dataset_id,
                is_valid=False,
                validation_errors=[f"Design metadata file not found: {meta_file}"]
            )

    try:
        with open(meta_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    except json.JSONDecodeError as e:
        return DesignMetadata(
            pre_scan_count=0,
            post_scan_count=0,
            intervention_type="",
            scan_type="",
            dataset_id=dataset_id,
            is_valid=False,
            validation_errors=[f"Invalid JSON in design file: {e}"]
        )
    except Exception as e:
        return DesignMetadata(
            pre_scan_count=0,
            post_scan_count=0,
            intervention_type="",
            scan_type="",
            dataset_id=dataset_id,
            is_valid=False,
            validation_errors=[f"Error reading design file: {e}"]
        )

    # Perform validation
    is_valid, errors = validate_design_logic(metadata)

    return DesignMetadata(
        pre_scan_count=int(metadata.get("pre_scan_count", 0)),
        post_scan_count=int(metadata.get("post_scan_count", 0)),
        intervention_type=str(metadata.get("intervention_type", "")),
        scan_type=str(metadata.get("scan_type", "")),
        dataset_id=dataset_id,
        is_valid=is_valid,
        validation_errors=errors
    )


def verify_all_datasets(dataset_ids: Optional[List[str]] = None) -> List[DesignMetadata]:
    """
    Verify design for all available datasets or a specific list.

    Args:
        dataset_ids: Optional list of dataset IDs to verify. If None, scans
                     the data/raw directory for all datasets.

    Returns:
        List of DesignMetadata objects for each dataset.
    """
    data_dir = Path(get_data_dir())
    raw_dir = data_dir / "raw"

    if not raw_dir.exists():
        logger.warning(f"Raw data directory not found: {raw_dir}")
        return []

    if dataset_ids is None:
        # Discover all datasets in data/raw
        dataset_ids = [d.name for d in raw_dir.iterdir() if d.is_dir()]

    results = []
    for ds_id in dataset_ids:
        logger.info(f"Verifying design for dataset: {ds_id}")
        result = verify_dataset_design(ds_id)
        results.append(result)
        if result.is_valid:
            logger.info(f"  -> VALID: {ds_id} ({result.intervention_type}, {result.scan_type})")
        else:
            logger.warning(f"  -> INVALID: {ds_id} - {result.validation_errors}")

    return results


def main():
    """Main entry point for design verification."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting dataset design verification...")

    results = verify_all_datasets()

    if not results:
        logger.warning("No datasets found to verify.")
        return

    valid_count = sum(1 for r in results if r.is_valid)
    total_count = len(results)

    logger.info(f"Verification complete: {valid_count}/{total_count} datasets valid.")

    # Output summary
    for r in results:
        status = "PASS" if r.is_valid else "FAIL"
        print(f"[{status}] {r.dataset_id}: "
              f"pre={r.pre_scan_count}, post={r.post_scan_count}, "
              f"intv={r.intervention_type}, scan={r.scan_type}")
        if not r.is_valid:
            for err in r.validation_errors:
                print(f"      Error: {err}")

    # Exit with error if any verification failed
    if valid_count != total_count:
        raise DesignVerificationError(
            f"Design verification failed for {total_count - valid_count} dataset(s)."
        )


if __name__ == "__main__":
    main()

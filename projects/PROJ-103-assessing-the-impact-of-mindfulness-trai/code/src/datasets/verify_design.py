import re
import os
import json
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass
import logging

from src.config.env import get_data_dir

logger = logging.getLogger(__name__)

class DesignVerificationError(Exception):
    """Raised when dataset design verification fails."""
    pass

@dataclass
class DesignMetadata:
    """Container for verified design metadata fields."""
    pre_scan_count: int
    post_scan_count: int
    intervention_type: str
    scan_type: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pre_scan_count": self.pre_scan_count,
            "post_scan_count": self.post_scan_count,
            "intervention_type": self.intervention_type,
            "scan_type": self.scan_type
        }

    def __str__(self) -> str:
        return (
            f"DesignMetadata(pre_scan_count={self.pre_scan_count}, "
            f"post_scan_count={self.post_scan_count}, "
            f"intervention_type='{self.intervention_type}', "
            f"scan_type='{self.scan_type}')"
        )

def validate_metadata_fields(
    dataset_info: Dict[str, Any]
) -> Tuple[bool, Optional[DesignMetadata], List[str]]:
    """
    Validate that required metadata fields exist and are of correct type.

    Args:
        dataset_info: Dictionary containing dataset metadata.

    Returns:
        Tuple of (is_valid, DesignMetadata object or None, list of error messages)
    """
    errors = []
    
    # Check for required fields
    required_fields = ['pre_scan_count', 'post_scan_count', 'intervention_type', 'scan_type']
    for field in required_fields:
        if field not in dataset_info:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        return False, None, errors

    # Validate types
    if not isinstance(dataset_info['pre_scan_count'], int):
        errors.append(f"pre_scan_count must be int, got {type(dataset_info['pre_scan_count']).__name__}")
    if not isinstance(dataset_info['post_scan_count'], int):
        errors.append(f"post_scan_count must be int, got {type(dataset_info['post_scan_count']).__name__}")
    if not isinstance(dataset_info['intervention_type'], str):
        errors.append(f"intervention_type must be str, got {type(dataset_info['intervention_type']).__name__}")
    if not isinstance(dataset_info['scan_type'], str):
        errors.append(f"scan_type must be str, got {type(dataset_info['scan_type']).__name__}")

    if errors:
        return False, None, errors

    metadata = DesignMetadata(
        pre_scan_count=dataset_info['pre_scan_count'],
        post_scan_count=dataset_info['post_scan_count'],
        intervention_type=dataset_info['intervention_type'],
        scan_type=dataset_info['scan_type']
    )
    
    return True, metadata, []

def validate_design_logic(metadata: DesignMetadata) -> Tuple[bool, List[str]]:
    """
    Validate design logic rules:
    - pre_scan_count > 0 AND post_scan_count > 0
    - intervention_type matches regex 'mindfulness|MBSR|MBC' (case-insensitive)
    - scan_type equals 'rs-fMRI' or 'resting'

    Args:
        metadata: DesignMetadata object to validate.

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    # Check scan counts
    if metadata.pre_scan_count <= 0:
        errors.append(f"pre_scan_count must be > 0, got {metadata.pre_scan_count}")
    if metadata.post_scan_count <= 0:
        errors.append(f"post_scan_count must be > 0, got {metadata.post_scan_count}")

    # Check intervention type regex
    mindfulness_pattern = re.compile(r'mindfulness|mbsr|mbc', re.IGNORECASE)
    if not mindfulness_pattern.search(metadata.intervention_type):
        errors.append(
            f"intervention_type '{metadata.intervention_type}' does not match "
            r"pattern 'mindfulness|MBSR|MBC' (case-insensitive)"
        )

    # Check scan type
    valid_scan_types = ['rs-fMRI', 'resting']
    if metadata.scan_type not in valid_scan_types:
        errors.append(
            f"scan_type '{metadata.scan_type}' must be one of {valid_scan_types}"
        )

    return len(errors) == 0, errors

def verify_dataset_design(dataset_info: Dict[str, Any]) -> Tuple[bool, Optional[DesignMetadata], List[str]]:
    """
    Verify a single dataset's design meets requirements.

    Args:
        dataset_info: Dictionary containing dataset metadata.

    Returns:
        Tuple of (is_valid, DesignMetadata object or None, list of all errors)
    """
    # Step 1: Validate metadata fields
    field_valid, metadata, field_errors = validate_metadata_fields(dataset_info)
    if not field_valid:
        return False, None, field_errors

    # Step 2: Validate design logic
    logic_valid, logic_errors = validate_design_logic(metadata)
    if not logic_valid:
        return False, metadata, logic_errors

    return True, metadata, []

def verify_all_datasets(
    datasets_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Verify design for all downloaded datasets.

    Searches for design.json files in the data directory structure.
    Expected structure: data/raw/<dataset_id>/design.json

    Args:
        datasets_dir: Optional base directory for datasets. Defaults to data/raw/ from env.

    Returns:
        Dictionary with verification results:
        {
            "total_datasets": int,
            "verified_datasets": List[Dict],
            "failed_datasets": List[Dict],
            "summary": Dict
        }
    """
    if datasets_dir is None:
        data_root = get_data_dir()
        datasets_dir = Path(data_root) / "raw"
    
    if not datasets_dir.exists():
        raise DesignVerificationError(f"Datasets directory does not exist: {datasets_dir}")

    results = {
        "total_datasets": 0,
        "verified_datasets": [],
        "failed_datasets": [],
        "summary": {
            "verified_count": 0,
            "failed_count": 0
        }
    }

    # Find all design.json files
    design_files = list(datasets_dir.rglob("design.json"))
    
    if not design_files:
        logger.warning(f"No design.json files found in {datasets_dir}")
        return results

    for design_file in design_files:
        results["total_datasets"] += 1
        dataset_id = design_file.parent.name
        
        try:
            with open(design_file, 'r') as f:
                dataset_info = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            error_msg = f"Failed to read design.json: {str(e)}"
            results["failed_datasets"].append({
                "dataset_id": dataset_id,
                "file_path": str(design_file),
                "error": error_msg
            })
            results["summary"]["failed_count"] += 1
            logger.error(f"[{dataset_id}] {error_msg}")
            continue

        is_valid, metadata, errors = verify_dataset_design(dataset_info)
        
        if is_valid:
            results["verified_datasets"].append({
                "dataset_id": dataset_id,
                "file_path": str(design_file),
                "metadata": metadata.to_dict()
            })
            results["summary"]["verified_count"] += 1
            logger.info(f"[{dataset_id}] Design verification passed: {metadata}")
        else:
            results["failed_datasets"].append({
                "dataset_id": dataset_id,
                "file_path": str(design_file),
                "metadata": metadata.to_dict() if metadata else None,
                "errors": errors
            })
            results["summary"]["failed_count"] += 1
            logger.error(f"[{dataset_id}] Design verification failed: {errors}")

    return results

def main() -> int:
    """
    Main entry point for dataset design verification.
    
    Reads design.json files from data/raw/, validates them,
    and writes verification results to data/results/design_verification.json.

    Returns:
        Exit code (0 for success, 1 for failures)
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        results = verify_all_datasets()
        
        # Write results to output file
        data_root = get_data_dir()
        output_dir = Path(data_root) / "results"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / "design_verification.json"
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Verification results written to {output_file}")
        logger.info(f"Total: {results['total_datasets']}, "
                   f"Verified: {results['summary']['verified_count']}, "
                   f"Failed: {results['summary']['failed_count']}")
        
        # Return non-zero if any failures
        return 1 if results["summary"]["failed_count"] > 0 else 0
        
    except Exception as e:
        logger.error(f"Verification failed with error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())

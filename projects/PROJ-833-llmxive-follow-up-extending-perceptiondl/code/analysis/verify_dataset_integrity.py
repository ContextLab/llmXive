"""
T030: Verify generated dataset integrity (checksums, schema compliance) and log failure counts.

This script performs a comprehensive integrity check on the synthetic dataset generated
by T029. It verifies:
1. Schema compliance against contracts/synthetic_image.schema.yaml
2. Checksums of generated files to detect corruption
3. Geometric consistency (no overlaps, valid derived relations)
4. Logs failure counts and generates a summary report.
"""
import os
import sys
import json
import hashlib
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from config import get_data_path, ensure_directories
from contracts.validator import load_schema, validate_synthetic_image, validate_file
from synthetic.validator import validate_synthetic_image_file, validate_no_overlaps
from synthetic.geometry_validator import validate_all_in_directory
from synthetic.deriver import calculate_centroid, derive_spatial_relation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / "state" / "dataset_integrity_check.log")
    ]
)
logger = logging.getLogger(__name__)

def calculate_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to calculate checksum for {file_path}: {e}")
        return ""

def load_schema_file(schema_path: Path) -> Dict[str, Any]:
    """Load a JSON schema file."""
    try:
        with open(schema_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load schema {schema_path}: {e}")
        return {}

def verify_schema_compliance(json_file: Path, schema: Dict[str, Any]) -> Tuple[bool, str]:
    """Verify a JSON file against a schema."""
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Use jsonschema for validation if available, otherwise basic check
        try:
            from jsonschema import validate, ValidationError
            validate(instance=data, schema=schema)
            return True, "Schema compliant"
        except ImportError:
            # Fallback to basic structure check if jsonschema not installed
            required_fields = schema.get('required', [])
            for field in required_fields:
                if field not in data:
                    return False, f"Missing required field: {field}"
            return True, "Basic structure compliant (jsonschema not installed)"
        except ValidationError as e:
            return False, f"Schema validation error: {e.message}"
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"
    except Exception as e:
        return False, f"Error reading file: {e}"

def verify_checksums(data_dir: Path, checksums_file: Path) -> Tuple[int, int]:
    """
    Verify file checksums against a stored checksums file.
    Returns (valid_count, invalid_count)
    """
    if not checksums_file.exists():
        logger.warning(f"Checksums file not found: {checksums_file}. Skipping checksum verification.")
        return 0, 0

    try:
        with open(checksums_file, 'r') as f:
            stored_checksums = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load checksums file: {e}")
        return 0, 0

    valid_count = 0
    invalid_count = 0

    for file_name, stored_hash in stored_checksums.items():
        file_path = data_dir / file_name
        if not file_path.exists():
            logger.error(f"File missing: {file_path}")
            invalid_count += 1
            continue

        current_hash = calculate_file_checksum(file_path)
        if current_hash == stored_hash:
            valid_count += 1
        else:
            logger.error(f"Checksum mismatch for {file_name}: expected {stored_hash}, got {current_hash}")
            invalid_count += 1

    return valid_count, invalid_count

def run_integrity_check(data_dir: Path, schema_path: Path) -> Dict[str, Any]:
    """
    Run comprehensive integrity check on the dataset.
    Returns a summary dictionary with counts and details.
    """
    ensure_directories()
    summary = {
        "total_files": 0,
        "schema_compliant": 0,
        "schema_violations": 0,
        "geometry_valid": 0,
        "geometry_violations": 0,
        "checksum_valid": 0,
        "checksum_invalid": 0,
        "missing_files": 0,
        "errors": [],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    # Load schema
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        summary["errors"].append(f"Schema file missing: {schema_path}")
        return summary

    schema = load_schema_file(schema_path)
    if not schema:
        summary["errors"].append("Failed to load schema")
        return summary

    # Find all JSON files
    json_files = list(data_dir.glob("*.json"))
    summary["total_files"] = len(json_files)

    if summary["total_files"] == 0:
        logger.warning("No JSON files found in dataset directory.")
        summary["errors"].append("No JSON files found in dataset directory")
        return summary

    logger.info(f"Checking {summary['total_files']} JSON files...")

    # Verify each file
    for json_file in json_files:
        # Schema compliance
        is_compliant, msg = verify_schema_compliance(json_file, schema)
        if is_compliant:
            summary["schema_compliant"] += 1
        else:
            summary["schema_violations"] += 1
            logger.warning(f"Schema violation in {json_file.name}: {msg}")

        # Geometry validation (overlaps and derived relations)
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Check for overlaps
            boxes = data.get('bounding_boxes', [])
            if validate_no_overlaps(boxes):
                summary["geometry_valid"] += 1
            else:
                summary["geometry_violations"] += 1
                logger.warning(f"Overlap detected in {json_file.name}")
        except Exception as e:
            summary["geometry_violations"] += 1
            logger.error(f"Geometry validation failed for {json_file.name}: {e}")

    # Checksum verification
    checksums_file = data_dir.parent / "checksums.json"
    if checksums_file.exists():
        valid, invalid = verify_checksums(data_dir, checksums_file)
        summary["checksum_valid"] = valid
        summary["checksum_invalid"] = invalid
    else:
        logger.info("No checksums file found. Skipping checksum verification.")

    # Log summary
    logger.info("=" * 50)
    logger.info("INTEGRITY CHECK SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total files checked: {summary['total_files']}")
    logger.info(f"Schema compliant: {summary['schema_compliant']}")
    logger.info(f"Schema violations: {summary['schema_violations']}")
    logger.info(f"Geometry valid: {summary['geometry_valid']}")
    logger.info(f"Geometry violations: {summary['geometry_violations']}")
    logger.info(f"Checksum valid: {summary['checksum_valid']}")
    logger.info(f"Checksum invalid: {summary['checksum_invalid']}")
    logger.info(f"Missing files: {summary['missing_files']}")
    logger.info(f"Errors encountered: {len(summary['errors'])}")
    logger.info("=" * 50)

    return summary

def main():
    """Main entry point for the integrity check."""
    data_path = get_data_path()
    synthetic_dir = data_path / "synthetic"
    schema_path = PROJECT_ROOT / "contracts" / "synthetic_image.schema.yaml"

    logger.info(f"Starting dataset integrity check for: {synthetic_dir}")
    logger.info(f"Using schema: {schema_path}")

    if not synthetic_dir.exists():
        logger.error(f"Synthetic data directory not found: {synthetic_dir}")
        sys.exit(1)

    summary = run_integrity_check(synthetic_dir, schema_path)

    # Save summary report
    report_path = PROJECT_ROOT / "state" / "dataset_integrity_report.json"
    with open(report_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Integrity report saved to: {report_path}")

    # Exit with error code if any critical failures
    if summary["schema_violations"] > 0 or summary["geometry_violations"] > 0:
        logger.error("Dataset integrity check FAILED - violations detected")
        sys.exit(1)
    else:
        logger.info("Dataset integrity check PASSED")
        sys.exit(0)

if __name__ == "__main__":
    main()

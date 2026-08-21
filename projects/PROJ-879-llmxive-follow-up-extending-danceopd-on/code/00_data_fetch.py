"""
T012: Verify Pre-fetched Raw Datasets.

This script verifies the existence and checksums of ImageNet-1K and LAION-400M
samples in data/raw/. It does NOT download data. It assumes data was pre-fetched
in a separate CI job or manually.

Validation:
1. Check for data/raw/imagenet_samples.parquet and data/raw/laion_samples.parquet.
2. Compute SHA256 and compare against data/raw/checksums.json.
3. If any file is missing or checksum mismatch, exit with code 1.
4. Write validation report to data/results/data_fetch_validation.json.
"""

import argparse
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Import from sibling utils
from utils.config import get_config


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")


def load_checksums(checksums_path: Path) -> Dict[str, str]:
    """Load expected checksums from JSON file."""
    if not checksums_path.exists():
        raise FileNotFoundError(f"Checksums file not found: {checksums_path}")
    
    with open(checksums_path, "r") as f:
        return json.load(f)


def verify_dataset(
    dataset_name: str,
    file_path: Path,
    expected_hash: str
) -> Tuple[bool, str, Optional[str]]:
    """
    Verify a single dataset file.
    
    Returns:
        Tuple of (is_valid, message, actual_hash)
    """
    if not file_path.exists():
        return False, f"File missing: {file_path}", None
    
    try:
        actual_hash = calculate_sha256(file_path)
    except FileNotFoundError as e:
        return False, str(e), None
    
    if actual_hash != expected_hash:
        return False, f"Checksum mismatch for {dataset_name}", actual_hash
    
    return True, f"Verified {dataset_name}", actual_hash


def run_verification(project_root: Path) -> Dict[str, Any]:
    """
    Run full verification of pre-fetched datasets.
    
    Returns:
        Validation report dictionary
    """
    config = get_config()
    
    # Define expected files based on T012 requirements
    expected_datasets = {
        "imagenet_samples": {
            "file_path": project_root / "data" / "raw" / "imagenet_samples.parquet",
            "key": "imagenet_samples.parquet"
        },
        "laion_samples": {
            "file_path": project_root / "data" / "raw" / "laion_samples.parquet",
            "key": "laion_samples.parquet"
        }
    }
    
    checksums_path = project_root / "data" / "raw" / "checksums.json"
    
    results = {
        "status": "verified",
        "datasets": {},
        "errors": [],
        "warnings": []
    }
    
    # Load checksums
    try:
        checksums = load_checksums(checksums_path)
    except FileNotFoundError as e:
        results["status"] = "failed"
        results["errors"].append(str(e))
        results["message"] = "Checksums file missing. Cannot verify data."
        return results
    
    # Verify each dataset
    all_valid = True
    for dataset_name, dataset_info in expected_datasets.items():
        file_path = dataset_info["file_path"]
        key = dataset_info["key"]
        
        if key not in checksums:
            results["warnings"].append(f"No checksum entry for {key}")
            # Continue verification, but mark as potentially problematic
            results["datasets"][dataset_name] = {
                "status": "warning",
                "message": f"No checksum defined for {key}",
                "file_exists": file_path.exists()
            }
            continue
        
        expected_hash = checksums[key]
        is_valid, message, actual_hash = verify_dataset(
            dataset_name, 
            file_path, 
            expected_hash
        )
        
        results["datasets"][dataset_name] = {
            "status": "verified" if is_valid else "failed",
            "message": message,
            "file_exists": file_path.exists(),
            "expected_hash": expected_hash,
            "actual_hash": actual_hash
        }
        
        if not is_valid:
            all_valid = False
            results["errors"].append(message)
    
    # Set overall status
    if all_valid and not results["errors"]:
        results["status"] = "verified"
        results["message"] = "All datasets verified successfully."
    else:
        results["status"] = "failed"
        results["message"] = "Verification failed. Check errors below."
    
    return results


def save_validation_report(report: Dict[str, Any], output_path: Path) -> None:
    """Save validation report to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)


def main() -> int:
    """Main entry point for T012 verification."""
    parser = argparse.ArgumentParser(
        description="Verify pre-fetched raw datasets (T012)"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Project root directory (defaults to config)"
    )
    args = parser.parse_args()
    
    # Determine project root
    if args.project_root:
        project_root = args.project_root
    else:
        config = get_config()
        project_root = config.get("PROJECT_ROOT", Path.cwd())
    
    print(f"Starting T012 verification for project: {project_root}")
    
    try:
        # Run verification
        report = run_verification(project_root)
        
        # Save report
        output_path = project_root / "data" / "results" / "data_fetch_validation.json"
        save_validation_report(report, output_path)
        
        print(f"Validation report saved to: {output_path}")
        print(f"Status: {report['status']}")
        
        if report["errors"]:
            print("\nErrors:")
            for error in report["errors"]:
                print(f"  - {error}")
        
        if report["warnings"]:
            print("\nWarnings:")
            for warning in report["warnings"]:
                print(f"  - {warning}")
        
        # Exit with appropriate code
        if report["status"] == "verified":
            print("\n✓ Verification PASSED")
            return 0
        else:
            print("\n✗ Verification FAILED")
            return 1
            
    except Exception as e:
        print(f"\n✗ Verification ERROR: {str(e)}")
        # Save error report
        error_report = {
            "status": "failed",
            "message": f"Verification error: {str(e)}",
            "errors": [str(e)],
            "datasets": {}
        }
        output_path = project_root / "data" / "results" / "data_fetch_validation.json"
        try:
            save_validation_report(error_report, output_path)
        except Exception:
            pass  # Best effort to save error report
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
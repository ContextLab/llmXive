#!/usr/bin/env python
# Implementation
"""
Data Fetching Module.
Verifies the existence and checksums of ImageNet-1K and LAION-400M samples.
"""
import argparse
import json
import sys
import hashlib
from pathlib import Path
from typing import Dict, Any, List

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_data(project_root: Path) -> Dict[str, Any]:
    """
    Verify existence and checksums of raw datasets.
    Returns a validation report.
    """
    raw_dir = project_root / "data" / "raw"
    checksums_file = raw_dir / "checksums.json"
    validation_report = {
        "status": "failed",
        "files_checked": [],
        "errors": []
    }

    # Expected files
    expected_files = ["imagenet_samples.parquet", "laion_samples.parquet"]
    
    # Load checksums if they exist
    if not checksums_file.exists():
        validation_report["errors"].append(f"Checksum file not found: {checksums_file}")
        return validation_report

    with open(checksums_file, "r") as f:
        expected_checksums = json.load(f)

    all_valid = True
    for filename in expected_files:
        file_path = raw_dir / filename
        if not file_path.exists():
            validation_report["errors"].append(f"Missing file: {file_path}")
            all_valid = False
            validation_report["files_checked"].append({"file": filename, "status": "missing"})
            continue

        current_hash = calculate_sha256(file_path)
        expected_hash = expected_checksums.get(filename)
        
        if expected_hash and current_hash == expected_hash:
            validation_report["files_checked"].append({"file": filename, "status": "verified", "hash": current_hash})
        else:
            validation_report["errors"].append(f"Checksum mismatch for {filename}")
            all_valid = False
            validation_report["files_checked"].append({"file": filename, "status": "mismatch", "expected": expected_hash, "actual": current_hash})

    validation_report["status"] = "verified" if all_valid else "failed"
    
    # Write validation report
    results_dir = project_root / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    report_path = results_dir / "data_fetch_validation.json"
    with open(report_path, "w") as f:
        json.dump(validation_report, f, indent=2)
    
    return validation_report

def main():
    project_root = Path(__file__).parent.parent
    report = fetch_data(project_root)
    if report["status"] == "failed":
        print(f"Data fetch validation failed: {report['errors']}")
        sys.exit(1)
    print("Data fetch validation successful.")
    sys.exit(0)

if __name__ == "__main__":
    main()

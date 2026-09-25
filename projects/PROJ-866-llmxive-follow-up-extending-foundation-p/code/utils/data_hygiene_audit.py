"""
Data Hygiene Audit Script for llmXive Project.

This script verifies:
1. data/raw/ contains only generated workflow files (no hand-edited or downloaded files).
2. data/processed/ and data/results/ are derived solely from data/raw/ by ensuring
   every workflow ID in processed/results exists in raw.

It produces an audit report at data/results/data_hygiene_audit.json.
"""
import json
import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any

# Project root is assumed to be the parent of 'code'
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
AUDIT_OUTPUT_PATH = DATA_RESULTS_DIR / "data_hygiene_audit.json"

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    if not file_path.exists():
        return ""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def get_generated_workflow_ids(raw_dir: Path) -> Set[str]:
    """
    Extract workflow IDs from data/raw/ directory.
    Assumes files are named like workflow_{id}.json or contain 'id' in JSON.
    """
    workflow_ids = set()
    if not raw_dir.exists():
        return workflow_ids

    for file_path in raw_dir.iterdir():
        if file_path.is_file() and file_path.suffix == ".json":
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Handle both single workflow and list of workflows
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and "id" in item:
                                workflow_ids.add(str(item["id"]))
                    elif isinstance(data, dict) and "id" in data:
                        workflow_ids.add(str(data["id"]))
                    # Also check for 'workflow_id' key as fallback
                    elif isinstance(data, dict) and "workflow_id" in data:
                        workflow_ids.add(str(data["workflow_id"]))
            except (json.JSONDecodeError, IOError):
                # Skip corrupted files
                continue
    return workflow_ids

def get_processed_workflow_ids(processed_dir: Path) -> Set[str]:
    """
    Extract workflow IDs from data/processed/ directory.
    Looks for log files (e.g., log_{workflow_id}_{depth}.json).
    """
    workflow_ids = set()
    if not processed_dir.exists():
        return workflow_ids

    for file_path in processed_dir.iterdir():
        if file_path.is_file() and file_path.suffix == ".json":
            # Try to extract ID from filename or content
            filename = file_path.stem
            # Pattern: log_{workflow_id}_{depth}
            if filename.startswith("log_"):
                parts = filename.split("_")
                if len(parts) >= 3:
                    # Assume second part is workflow_id
                    workflow_ids.add(parts[1])
            
            # Also try parsing content if filename doesn't match pattern
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        if "workflow_id" in data:
                            workflow_ids.add(str(data["workflow_id"]))
                        elif "id" in data:
                            workflow_ids.add(str(data["id"]))
                    elif isinstance(data, list) and len(data) > 0:
                        if isinstance(data[0], dict):
                            if "workflow_id" in data[0]:
                                workflow_ids.add(str(data[0]["workflow_id"]))
                            elif "id" in data[0]:
                                workflow_ids.add(str(data[0]["id"]))
            except (json.JSONDecodeError, IOError):
                continue
    return workflow_ids

def get_results_workflow_ids(results_dir: Path) -> Set[str]:
    """
    Extract workflow IDs from data/results/ directory.
    For analysis files, we check if they reference specific workflow IDs.
    """
    workflow_ids = set()
    if not results_dir.exists():
        return workflow_ids

    for file_path in results_dir.iterdir():
        if file_path.is_file() and file_path.suffix == ".json":
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Check for common fields that might contain workflow IDs
                    if isinstance(data, dict):
                        if "workflow_id" in data:
                            workflow_ids.add(str(data["workflow_id"]))
                        elif "id" in data:
                            workflow_ids.add(str(data["id"]))
                        # Check for nested structures
                        for key, value in data.items():
                            if isinstance(value, dict):
                                if "workflow_id" in value:
                                    workflow_ids.add(str(value["workflow_id"]))
                            elif isinstance(value, list):
                                for item in value:
                                    if isinstance(item, dict):
                                        if "workflow_id" in item:
                                            workflow_ids.add(str(item["workflow_id"]))
            except (json.JSONDecodeError, IOError):
                continue
    return workflow_ids

def check_for_non_generated_files(raw_dir: Path) -> Tuple[bool, List[str]]:
    """
    Check if data/raw/ contains only generated files.
    Returns (is_clean, list_of_suspicious_files).
    """
    suspicious_files = []
    if not raw_dir.exists():
        return True, []

    # Known patterns for generated files
    generated_patterns = [
        "workflow_",  # Standard prefix for generated workflows
        "log_",       # Log files
        "audit_"      # Audit files
    ]

    for file_path in raw_dir.iterdir():
        if file_path.is_file():
            filename = file_path.name
            is_generated = any(pattern in filename for pattern in generated_patterns)
            
            if not is_generated:
                # Check if it's a system file or hidden
                if filename.startswith(".") or filename.startswith("__"):
                    continue
                suspicious_files.append(str(file_path))

    return len(suspicious_files) == 0, suspicious_files

def check_derivation_consistency(
    raw_ids: Set[str],
    processed_ids: Set[str],
    results_ids: Set[str]
) -> Tuple[bool, Dict[str, List[str]]]:
    """
    Verify that processed and results IDs are subsets of raw IDs.
    Returns (is_consistent, details_dict).
    """
    details = {
        "orphaned_processed": [],
        "orphaned_results": [],
        "missing_in_raw": []
    }

    # Check processed IDs
    orphaned_processed = [pid for pid in processed_ids if pid not in raw_ids]
    details["orphaned_processed"] = orphaned_processed

    # Check results IDs
    orphaned_results = [rid for rid in results_ids if rid not in raw_ids]
    details["orphaned_results"] = orphaned_results

    # Check for any IDs that exist in processed/results but not raw
    missing_in_raw = list(set(orphaned_processed + orphaned_results))
    details["missing_in_raw"] = missing_in_raw

    is_consistent = len(missing_in_raw) == 0
    return is_consistent, details

def main():
    """Run the data hygiene audit."""
    print("Starting Data Hygiene Audit...")
    
    # Ensure output directory exists
    AUDIT_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Step 1: Collect workflow IDs
    print("Collecting workflow IDs from data/raw/...")
    raw_ids = get_generated_workflow_ids(DATA_RAW_DIR)
    print(f"  Found {len(raw_ids)} unique workflow IDs in raw data.")

    print("Collecting workflow IDs from data/processed/...")
    processed_ids = get_processed_workflow_ids(DATA_PROCESSED_DIR)
    print(f"  Found {len(processed_ids)} unique workflow IDs in processed data.")

    print("Collecting workflow IDs from data/results/...")
    results_ids = get_results_workflow_ids(DATA_RESULTS_DIR)
    print(f"  Found {len(results_ids)} unique workflow IDs in results data.")

    # Step 2: Check for non-generated files in raw
    print("Checking for non-generated files in data/raw/...")
    is_raw_clean, suspicious_files = check_for_non_generated_files(DATA_RAW_DIR)
    if not is_raw_clean:
        print(f"  WARNING: Found {len(suspicious_files)} suspicious files in data/raw/: {suspicious_files}")
    else:
        print("  OK: No suspicious files found in data/raw/.")

    # Step 3: Check derivation consistency
    print("Checking derivation consistency...")
    is_consistent, details = check_derivation_consistency(raw_ids, processed_ids, results_ids)
    
    if not is_consistent:
        print(f"  WARNING: Found {len(details['missing_in_raw'])} workflow IDs in processed/results that are not in raw.")
        if details['orphaned_processed']:
            print(f"    Orphaned in processed: {details['orphaned_processed'][:5]}...")
        if details['orphaned_results']:
            print(f"    Orphaned in results: {details['orphaned_results'][:5]}...")
    else:
        print("  OK: All processed and results IDs are derived from raw data.")

    # Step 4: Generate audit report
    audit_report = {
        "audit_timestamp": str(Path(__file__).stat().st_mtime),  # Using file mtime as proxy for run time
        "raw_data": {
            "directory": str(DATA_RAW_DIR),
            "workflow_count": len(raw_ids),
            "is_clean": is_raw_clean,
            "suspicious_files": suspicious_files
        },
        "processed_data": {
            "directory": str(DATA_PROCESSED_DIR),
            "workflow_count": len(processed_ids),
            "orphaned_ids": details["orphaned_processed"]
        },
        "results_data": {
            "directory": str(DATA_RESULTS_DIR),
            "workflow_count": len(results_ids),
            "orphaned_ids": details["orphaned_results"]
        },
        "consistency_check": {
            "is_consistent": is_consistent,
            "missing_in_raw": details["missing_in_raw"],
            "summary": "All data is properly derived from raw source" if is_consistent else "Data consistency issues detected"
        },
        "overall_status": "PASS" if (is_raw_clean and is_consistent) else "FAIL"
    }

    # Write audit report
    with open(AUDIT_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(audit_report, f, indent=2)

    print(f"\nAudit report written to: {AUDIT_OUTPUT_PATH}")
    print(f"Overall Status: {audit_report['overall_status']}")

    # Exit with appropriate code
    sys.exit(0 if audit_report['overall_status'] == "PASS" else 1)

if __name__ == "__main__":
    main()

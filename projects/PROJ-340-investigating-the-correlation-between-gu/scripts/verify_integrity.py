"""
Integrity Verification Script for Pipeline Artifacts.

This script compares checksums in the state file against actual file hashes
and outputs a comprehensive integrity report.
"""
import os
import sys
import json
import hashlib
import yaml
import argparse
from pathlib import Path
from datetime import datetime

def calculate_file_checksum(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state_file(state_path: str) -> dict:
    """Load the project state YAML file."""
    with open(state_path, 'r') as f:
        return yaml.safe_load(f)

def discover_artifacts(base_path: str) -> list:
    """
    Discover all relevant data files under the given base path.
    Returns a list of (relative_path, full_path) tuples.
    """
    artifacts = []
    base = Path(base_path)
    if not base.exists():
        return artifacts
    
    for root, dirs, files in os.walk(base):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if file.endswith(('.csv', '.json', '.parquet', '.yaml', '.yml', '.md')):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, base)
                artifacts.append((rel_path, full_path))
    
    return artifacts

def verify_artifacts(state: dict, artifacts: list) -> dict:
    """
    Verify artifacts against the state file checksums.
    
    Returns a report dict with verification results.
    """
    report = {
        "timestamp": str(datetime.now()),
        "total_artifacts": len(artifacts),
        "verified_count": 0,
        "missing_count": 0,
        "mismatch_count": 0,
        "details": []
    }
    
    # Build expected checksums map from state
    expected_checksums = state.get("artifact_hashes", {})
    
    for rel_path, full_path in artifacts:
        detail = {
            "path": rel_path,
            "status": "unknown",
            "expected_hash": None,
            "actual_hash": None
        }
        
        if rel_path in expected_checksums:
            expected_hash = expected_checksums[rel_path]
            detail["expected_hash"] = expected_hash
            
            if not os.path.exists(full_path):
                detail["status"] = "MISSING"
                report["missing_count"] += 1
            else:
                actual_hash = calculate_file_checksum(full_path)
                detail["actual_hash"] = actual_hash
                
                if actual_hash == expected_hash:
                    detail["status"] = "VERIFIED"
                    report["verified_count"] += 1
                else:
                    detail["status"] = "MISMATCH"
                    report["mismatch_count"] += 1
        else:
            # Artifact exists but not in state file (new or untracked)
            if os.path.exists(full_path):
                detail["status"] = "UNTRACKED"
                detail["actual_hash"] = calculate_file_checksum(full_path)
            else:
                detail["status"] = "MISSING"
                report["missing_count"] += 1
        
        report["details"].append(detail)
    
    return report

def main():
    parser = argparse.ArgumentParser(description="Verify integrity of pipeline artifacts.")
    parser.add_argument("--state-file", type=str, default="state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml", help="Path to the state YAML file")
    parser.add_argument("--data-path", type=str, default="data", help="Base path to scan for artifacts")
    parser.add_argument("--output", type=str, default="data/results/integrity_verification_report.json", help="Output report file path")
    
    args = parser.parse_args()
    
    print(f"Loading state file from {args.state_file}...")
    if not os.path.exists(args.state_file):
        print(f"ERROR: State file not found: {args.state_file}")
        sys.exit(1)
    
    state = load_state_file(args.state_file)
    
    print(f"Discovering artifacts under {args.data_path}...")
    artifacts = discover_artifacts(args.data_path)
    print(f"Found {len(artifacts)} artifacts.")
    
    print("Verifying artifacts...")
    report = verify_artifacts(state, artifacts)
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Integrity verification report written to {output_path}")
    print(f"Summary: {report['verified_count']} verified, {report['missing_count']} missing, {report['mismatch_count']} mismatched")
    
    # Exit with error if any mismatches or missing critical files
    if report["mismatch_count"] > 0:
        print("WARNING: Some artifacts have checksum mismatches.")
        sys.exit(1)
    elif report["missing_count"] > 0:
        print("WARNING: Some artifacts are missing.")
        sys.exit(1)
    else:
        print("All tracked artifacts verified successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()

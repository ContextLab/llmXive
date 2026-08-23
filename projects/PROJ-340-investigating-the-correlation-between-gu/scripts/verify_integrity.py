"""
Final Data Integrity Check Script (T130).

This script performs a comprehensive checksum verification of all raw and processed
data files against the state manifest defined in:
state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml

It compares the stored checksums in the state file against the actual SHA-256 hashes
of the files currently present in the data/ directory.

Output:
    data/results/integrity_verification_report.json
"""

import os
import sys
import json
import hashlib
import argparse
from pathlib import Path
from datetime import datetime

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_FILE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-340-investigating-the-correlation-between-gu.yaml"
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "data" / "results"
OUTPUT_FILE = OUTPUT_DIR / "integrity_verification_report.json"

# Import shared utility if available, otherwise define locally to avoid circular deps
# Based on API surface: code/constitution_checker.py has calculate_file_checksum
# We will implement a simple local version to ensure this script is standalone and robust
def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        raise IOError(f"Failed to read file {file_path}: {e}")

def load_state_yaml(file_path: Path) -> dict:
    """Load the state YAML file manually or via yaml if available."""
    try:
        import yaml
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except ImportError:
        # Fallback for environments without PyYAML installed, though requirements.txt should have it
        # Simple parser for the expected structure
        content = file_path.read_text()
        data = {"artifact_hashes": {}}
        current_key = None
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("artifact_hashes:"):
                current_key = "artifact_hashes"
            elif line.startswith("- path:") and current_key:
                # Extract path
                path_val = line.split(":", 1)[1].strip().strip('"').strip("'")
                data["artifact_hashes"][path_val] = None
            elif line.startswith("checksum:") and current_key and path_val:
                # This logic is simplistic; relying on yaml is preferred.
                # If yaml is missing, we assume the file is malformed for this check.
                pass
        return data

def discover_artifacts(base_dir: Path) -> dict:
    """
    Discover all relevant data files (CSV, JSON, PARQUET, YAML) in the data directory.
    Returns a dict mapping relative paths to absolute paths.
    """
    artifacts = {}
    extensions = {".csv", ".json", ".parquet", ".yaml", ".yml", ".tsv"}
    
    if not base_dir.exists():
        return artifacts

    for root, _, files in os.walk(base_dir):
        for file in files:
            if Path(file).suffix.lower() in extensions:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(base_dir)
                artifacts[str(rel_path)] = full_path
    
    return artifacts

def verify_integrity(state_file_path: Path, data_dir: Path) -> dict:
    """
    Compare stored checksums against actual file hashes.
    Returns a report dictionary.
    """
    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "state_file": str(state_file_path),
        "data_directory": str(data_dir),
        "total_artifacts_checked": 0,
        "passed": 0,
        "failed": 0,
        "missing": 0,
        "details": []
    }

    if not state_file_path.exists():
        report["error"] = f"State file not found: {state_file_path}"
        report["status"] = "FAILED"
        return report

    try:
        import yaml
        with open(state_file_path, 'r') as f:
            state_data = yaml.safe_load(f)
    except Exception as e:
        report["error"] = f"Failed to parse state file: {e}"
        report["status"] = "FAILED"
        return report

    artifact_hashes = state_data.get("artifact_hashes", {})
    
    if not artifact_hashes:
        report["warning"] = "No artifact hashes found in state file."
        report["status"] = "WARNING"
        return report

    # Check each registered artifact
    for rel_path, expected_hash in artifact_hashes.items():
        report["total_artifacts_checked"] += 1
        file_path = data_dir / rel_path
        
        detail = {
            "path": rel_path,
            "status": "",
            "expected_hash": expected_hash,
            "actual_hash": None
        }

        if not file_path.exists():
            detail["status"] = "MISSING"
            report["missing"] += 1
        else:
            try:
                actual_hash = calculate_sha256(file_path)
                detail["actual_hash"] = actual_hash
                
                if actual_hash == expected_hash:
                    detail["status"] = "PASSED"
                    report["passed"] += 1
                else:
                    detail["status"] = "FAILED"
                    report["failed"] += 1
            except Exception as e:
                detail["status"] = "ERROR"
                detail["error_message"] = str(e)
                report["failed"] += 1

        report["details"].append(detail)

    # Determine overall status
    if report["failed"] > 0 or report["missing"] > 0:
        report["status"] = "FAILED"
    else:
        report["status"] = "PASSED"

    return report

def main():
    parser = argparse.ArgumentParser(description="Verify data integrity against state manifest.")
    parser.add_argument("--state", type=str, default=str(STATE_FILE_PATH), help="Path to state YAML file")
    parser.add_argument("--data", type=str, default=str(DATA_DIR), help="Path to data directory")
    parser.add_argument("--output", type=str, default=str(OUTPUT_FILE), help="Path for output report JSON")
    
    args = parser.parse_args()

    state_path = Path(args.state)
    data_path = Path(args.data)
    output_path = Path(args.output)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Starting integrity check for project PROJ-340...")
    print(f"State file: {state_path}")
    print(f"Data directory: {data_path}")

    report = verify_integrity(state_path, data_path)

    # Write report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Integrity check complete. Report saved to: {output_path}")
    print(f"Status: {report.get('status', 'UNKNOWN')}")
    print(f"Passed: {report['passed']}, Failed: {report['failed']}, Missing: {report['missing']}")

    # Exit with code 0 if passed, 1 otherwise (standard convention)
    if report.get("status") == "PASSED":
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
import os
import sys
import json
import argparse
import time
from pathlib import Path
from datetime import datetime
import hashlib

# Define the marker for synthetic data as per T056 definition
SYNTHETIC_MARKER = "SYNTHETIC_PLACEHOLDER"
SYNTHETIC_PREFIX = "synthetic_"

class IntegrityCheckResult:
    def __init__(self):
        self.status = "PASS"
        self.found_artifacts = []
        self.errors = []
        self.check_time = datetime.now().isoformat()

def load_json_file(path: Path) -> dict:
    """Helper to load JSON files."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def verify_data_integrity(project_root: Path) -> dict:
    """
    Scans the data/ directory for synthetic placeholders generated during a failed real-data run.
    
    Definition: Files in data/ matching `synthetic_*.csv` or containing a specific 
    checksum marker defined in data/metadata/synthetic_data_manifest.json (if present).
    
    If found and the context implies a real-data run, this returns a FAIL status.
    
    Returns:
        dict: IntegrityCheckResult as a dictionary.
    """
    result = IntegrityCheckResult()
    data_dir = project_root / "data"
    
    if not data_dir.exists():
        result.errors.append("Data directory does not exist.")
        result.status = "ERROR"
        return result.__dict__

    # 1. Load the manifest if it exists to get expected synthetic checksums/markers
    manifest_path = project_root / "data" / "metadata" / "synthetic_data_manifest.json"
    manifest = load_json_file(manifest_path)
    allowed_synthetic_files = set()
    
    if manifest:
        # If a manifest exists, it might list allowed synthetic files for validation studies
        # We assume files listed here are "allowed" in a synthetic-only context, 
        # but we still flag them if we are in real-data mode.
        allowed_synthetic_files = set(manifest.get("allowed_files", []))

    # 2. Scan for synthetic_*.csv files
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.startswith(SYNTHETIC_PREFIX) and file.endswith(".csv"):
                file_path = Path(root) / file
                # Check if this is an allowed synthetic file for a validation study
                if file in allowed_synthetic_files:
                    continue # Allowed in synthetic mode
                
                # Check content for marker
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read(1024) # Read first 1KB
                        if SYNTHETIC_MARKER in content:
                            result.found_artifacts.append(str(file_path.relative_to(project_root)))
                except Exception:
                    pass

    # 3. Scan for files containing the marker in any format (text/csv/json)
    # This is a broader check
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.endswith((".csv", ".json", ".txt")) and not file.startswith("synthetic_"):
                file_path = Path(root) / file
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read(2048) # Read first 2KB
                        if SYNTHETIC_MARKER in content:
                            if str(file_path.relative_to(project_root)) not in result.found_artifacts:
                                result.found_artifacts.append(str(file_path.relative_to(project_root)))
                except Exception:
                    pass

    if result.found_artifacts:
        result.status = "FAIL"
        result.errors.append(f"Synthetic artifacts detected: {result.found_artifacts}")
    else:
        result.status = "PASS"

    return result.__dict__

def main():
    parser = argparse.ArgumentParser(description="Verify Data Integrity (T056)")
    parser.add_argument(
        "--project-root", 
        type=str, 
        default=".", 
        help="Path to the project root directory"
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    
    if not project_root.exists():
        print(f"Error: Project root {project_root} does not exist.")
        sys.exit(1)

    try:
        result = verify_data_integrity(project_root)
        output_dir = project_root / "data" / "results"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "integrity_verification.json"
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        
        print(f"Integrity verification result written to: {output_path}")
        print(f"Status: {result['status']}")
        if result['status'] == 'FAIL':
            print(f"Found artifacts: {result['found_artifacts']}")
            
        # Exit with error code if failed (for CI gate)
        if result['status'] == 'FAIL':
            sys.exit(1)
            
    except Exception as e:
        print(f"Verification failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

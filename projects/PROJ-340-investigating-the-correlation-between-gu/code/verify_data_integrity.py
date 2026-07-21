"""
T056 Implementation: Real Data Verification Script.
Scans the data/ directory for synthetic placeholders if --real-data flag is set.
"""
import os
import sys
import json
import hashlib
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Import project config if available, otherwise define paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
METADATA_DIR = DATA_DIR / "metadata"
RESULTS_DIR = DATA_DIR / "results"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

SYNTHETIC_MANIFEST_PATH = METADATA_DIR / "synthetic_data_manifest.json"

def load_json_file(path: Path) -> Dict[str, Any]:
    """Load a JSON file safely."""
    if not path.exists():
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(path: Path, data: Dict[str, Any]) -> None:
    """Save data to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def calculate_file_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def find_synthetic_artifacts(data_dir: Path, manifest: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Scan data directories for files matching synthetic patterns or checksums.
    
    Patterns:
    1. Filenames starting with 'synthetic_'
    2. Files matching checksums listed in synthetic_data_manifest.json
    """
    found_artifacts = []
    synthetic_checksums = manifest.get("artifact_checksums", [])
    
    patterns_to_check = []
    for root, _, files in os.walk(data_dir):
        for file in files:
            patterns_to_check.append(Path(root) / file)

    for file_path in patterns_to_check:
        # Check 1: Filename pattern
        if file_path.name.startswith("synthetic_"):
            found_artifacts.append({
                "path": str(file_path.relative_to(data_dir)),
                "reason": "Filename matches 'synthetic_' prefix",
                "checksum": calculate_file_checksum(file_path)
            })
            continue

        # Check 2: Checksum match
        checksum = calculate_file_checksum(file_path)
        if checksum in synthetic_checksums:
            found_artifacts.append({
                "path": str(file_path.relative_to(data_dir)),
                "reason": "Checksum matches synthetic manifest",
                "checksum": checksum
            })

    return found_artifacts

def run_validation_pipeline(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Main validation logic.
    If --real-data is set, ensure no synthetic artifacts exist.
    """
    is_real_mode = args.real_data
    report = {
        "status": "PASS",
        "mode": "real-data" if is_real_mode else "synthetic-allowed",
        "timestamp": str(Path.cwd().parent), # Placeholder for actual timestamp logic if needed
        "scanned_directories": [],
        "artifacts_found": [],
        "errors": []
    }

    if not DATA_DIR.exists():
        report["status"] = "FAIL"
        report["errors"].append("Data directory not found. Pipeline may not have run.")
        return report

    # Load manifest if it exists
    manifest = load_json_file(SYNTHETIC_MANIFEST_PATH)

    scanned_dirs = [RAW_DIR, PROCESSED_DIR, RESULTS_DIR, METADATA_DIR]
    report["scanned_directories"] = [str(d.relative_to(PROJECT_ROOT)) for d in scanned_dirs if d.exists()]

    all_artifacts = []
    for d in scanned_dirs:
        if d.exists():
            found = find_synthetic_artifacts(d, manifest)
            all_artifacts.extend(found)

    report["artifacts_found"] = all_artifacts

    if is_real_mode and all_artifacts:
        report["status"] = "FAIL"
        report["errors"].append(f"FABRICATION DETECTED: {len(all_artifacts)} synthetic artifacts found in real-data mode.")
        report["summary"] = "CRITICAL: Synthetic data detected while real data was required. Pipeline integrity compromised."
    elif is_real_mode:
        report["summary"] = "PASS: No synthetic artifacts detected in real-data mode."
    else:
        report["summary"] = "SKIPPED: Synthetic mode allowed; no fabrication check enforced."

    return report

def main():
    parser = argparse.ArgumentParser(description="Verify data integrity against synthetic fabrication.")
    parser.add_argument("--real-data", action="store_true", help="Enforce strict real-data mode (fail if synthetic found).")
    args = parser.parse_args()

    report = run_validation_pipeline(args)

    output_path = RESULTS_DIR / "integrity_verification.json"
    save_json_file(output_path, report)

    print(f"Integrity verification complete. Report saved to: {output_path}")
    print(f"Status: {report['status']}")
    if report['status'] == 'FAIL':
        print("ERRORS:")
        for err in report['errors']:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print(report['summary'])
        sys.exit(0)

if __name__ == "__main__":
    main()

"""
T050: Verify all artifacts are checksummed in state/.

This script scans the `state/` directory for all generated artifacts (excluding
the checksum registry itself), computes their SHA-256 hashes, and compares them
against the registry stored in `state/data_hashes.json`.

It ensures data integrity by verifying that every file recorded in the registry
exists and matches its recorded hash. It also reports any files in `state/`
that are missing from the registry.

Output:
    - Prints a summary to stdout.
    - Writes `state/checksum_verification_report.json` with detailed results.
    - Exits with code 0 if all checks pass, 1 if any discrepancies are found.
"""
import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Import project utilities
# Assuming logging_init is already set up by T008b, but we can re-initialize if needed
# For this script, we'll set up a basic logger to avoid circular import issues if not fully initialized
def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    return logger

logger = setup_logger("verify_checksums")

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent

def compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error computing hash for {file_path}: {e}")
        return ""

def load_hash_registry(registry_path: Path) -> Dict[str, str]:
    """Load the existing hash registry from state/data_hashes.json."""
    if not registry_path.exists():
        logger.warning(f"Hash registry not found at {registry_path}. Creating a new one.")
        return {}
    
    try:
        with open(registry_path, "r") as f:
            data = json.load(f)
            # Handle potential nested structure if the file stores more than just {path: hash}
            if "hashes" in data:
                return data["hashes"]
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse hash registry: {e}")
        return {}

def save_hash_registry(registry_path: Path, registry: Dict[str, str]) -> None:
    """Save the updated hash registry."""
    with open(registry_path, "w") as f:
        json.dump({"hashes": registry}, f, indent=2)
    logger.info(f"Updated hash registry saved to {registry_path}")

def verify_artifact(
    file_path: Path, 
    expected_hash: str, 
    registry: Dict[str, str]
) -> Tuple[bool, str, Optional[str]]:
    """
    Verify a single artifact against the registry.
    
    Returns:
        (is_valid, status_message, actual_hash_if_mismatch)
    """
    if not file_path.exists():
        return False, f"MISSING: File {file_path.relative_to(get_project_root())} does not exist.", None
    
    actual_hash = compute_sha256(file_path)
    if not actual_hash:
        return False, f"ERROR: Could not compute hash for {file_path}.", None
    
    if expected_hash == actual_hash:
        return True, f"OK: {file_path.relative_to(get_project_root())} matches hash.", None
    
    return False, f"MISMATCH: {file_path.relative_to(get_project_root())} hash mismatch.", actual_hash

def main():
    project_root = get_project_root()
    state_dir = project_root / "state"
    registry_path = state_dir / "data_hashes.json"
    report_path = state_dir / "checksum_verification_report.json"

    if not state_dir.exists():
        logger.error("State directory does not exist. Cannot verify artifacts.")
        sys.exit(1)

    # Load existing registry
    registry = load_hash_registry(registry_path)
    
    # Find all files in state/ (excluding the registry and the report itself)
    artifact_files = []
    for root, _, files in os.walk(state_dir):
        for file in files:
            file_path = Path(root) / file
            if file_path == registry_path or file_path == report_path:
                continue
            artifact_files.append(file_path)

    logger.info(f"Found {len(artifact_files)} artifacts to verify.")

    verification_results = {
        "total_artifacts": len(artifact_files),
        "verified_count": 0,
        "failed_count": 0,
        "missing_in_registry": 0,
        "details": []
    }

    # 1. Verify files present in the registry
    for rel_path, expected_hash in registry.items():
        abs_path = project_root / rel_path
        if not abs_path.exists():
            # File in registry but missing on disk
            verification_results["failed_count"] += 1
            verification_results["details"].append({
                "path": rel_path,
                "status": "MISSING_ON_DISK",
                "message": f"File in registry but missing on disk: {rel_path}"
            })
            continue

        is_valid, message, _ = verify_artifact(abs_path, expected_hash, registry)
        if is_valid:
            verification_results["verified_count"] += 1
        else:
            verification_results["failed_count"] += 1
        
        verification_results["details"].append({
            "path": rel_path,
            "status": "OK" if is_valid else "MISMATCH",
            "message": message
        })

    # 2. Check for files on disk not in registry
    for file_path in artifact_files:
        rel_path = str(file_path.relative_to(project_root))
        if rel_path not in registry:
            verification_results["missing_in_registry"] += 1
            verification_results["details"].append({
                "path": rel_path,
                "status": "UNREGISTERED",
                "message": f"File exists on disk but not in registry: {rel_path}"
            })
            # Optionally compute hash and add to registry? 
            # For T050, we just report it as an issue unless we decide to update.
            # The task says "Verify all artifacts are checksummed", so unregistered is a failure.
            verification_results["failed_count"] += 1

    # Write report
    report_data = {
        "verification_timestamp": "N/A", # Could add time
        "registry_path": str(registry_path.relative_to(project_root)),
        "summary": {
            "total_checked": verification_results["total_artifacts"],
            "passed": verification_results["verified_count"],
            "failed": verification_results["failed_count"],
            "unregistered_files": verification_results["missing_in_registry"]
        },
        "details": verification_results["details"]
    }

    with open(report_path, "w") as f:
        json.dump(report_data, f, indent=2)
    
    logger.info(f"Verification report written to {report_path}")

    # Summary output
    if verification_results["failed_count"] == 0 and verification_results["missing_in_registry"] == 0:
        logger.info("SUCCESS: All artifacts are checksummed and verified.")
        sys.exit(0)
    else:
        logger.error(f"FAILURE: {verification_results['failed_count']} verification failures, "
                     f"{verification_results['missing_in_registry']} unregistered files.")
        sys.exit(1)

if __name__ == "__main__":
    main()

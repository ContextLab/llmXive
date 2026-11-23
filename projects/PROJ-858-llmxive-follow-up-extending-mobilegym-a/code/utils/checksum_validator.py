import json
import hashlib
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timezone

from utils.logging import get_logger, log_with_context

logger = get_logger("checksum_validator")

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def load_checksum_registry(registry_path: Path) -> Dict[str, str]:
    """Load the checksum registry from a JSON file."""
    if not registry_path.exists():
        raise FileNotFoundError(f"Checksum registry not found: {registry_path}")
    with open(registry_path, "r") as f:
        return json.load(f)

def verify_artifact(file_path: Path, expected_checksum: str, relative_path: str) -> Tuple[bool, str]:
    """Verify a single artifact against its expected checksum."""
    if not file_path.exists():
        return False, f"File missing: {file_path}"
    
    actual_checksum = calculate_sha256(file_path)
    if actual_checksum != expected_checksum:
        return False, f"Checksum mismatch for {relative_path}: expected {expected_checksum}, got {actual_checksum}"
    
    return True, f"Verified: {relative_path} ({actual_checksum})"

def run_validation(checksum_registry_path: Optional[Path] = None) -> bool:
    """
    Validate all artifacts listed in the checksum registry.
    
    Returns True if all artifacts are valid, False otherwise.
    """
    if checksum_registry_path is None:
        checksum_registry_path = Path("data/processed/checksum_registry.json")
    
    logger.info("Starting artifact checksum validation")
    
    try:
        registry = load_checksum_registry(checksum_registry_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        return False
    
    all_valid = True
    validation_results = []
    
    for relative_path, expected_checksum in registry.items():
        file_path = Path(relative_path)
        is_valid, message = verify_artifact(file_path, expected_checksum, relative_path)
        validation_results.append({
            "path": relative_path,
            "valid": is_valid,
            "message": message
        })
        
        if is_valid:
            logger.info(message)
        else:
            logger.error(message)
            all_valid = False
    
    # Write validation report
    report_path = Path("data/processed/validation_report.json")
    with open(report_path, "w") as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "registry_path": str(checksum_registry_path),
            "all_valid": all_valid,
            "results": validation_results
        }, f, indent=2)
    
    logger.info(f"Validation report written to {report_path}")
    
    if all_valid:
        logger.info("All artifacts verified successfully")
    else:
        logger.error("Some artifacts failed verification")
    
    return all_valid

def main():
    """Entry point for checksum validation script."""
    success = run_validation()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

"""
T009: Checksum verification utilities.
"""
import hashlib
import logging
import json
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Union

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChecksumError(Exception):
    pass

def compute_sha256(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_checksum(file_path: Path, expected_hash: str) -> bool:
    actual_hash = compute_sha256(file_path)
    return actual_hash == expected_hash

def verify_artifacts_from_manifest(manifest_path: Path) -> List[Dict[str, bool]]:
    results = []
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    
    for item in manifest.get("artifacts", []):
        file_path = Path(item["file"])
        expected = item["sha256"]
        is_valid = validate_checksum(file_path, expected)
        results.append({"file": file_path.name, "valid": is_valid})
        if not is_valid:
            logger.error(f"Checksum failed for {file_path}")
    
    return results

def generate_checksum_manifest(output_path: Path, manifest_path: Path):
    checksum = compute_sha256(output_path)
    manifest = {
        "file": output_path.name,
        "sha256": checksum,
        "generated_at": "timestamp"
    }
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

def verify_single_artifact(file_path: Path, expected_hash: str) -> bool:
    return validate_checksum(file_path, expected_hash)

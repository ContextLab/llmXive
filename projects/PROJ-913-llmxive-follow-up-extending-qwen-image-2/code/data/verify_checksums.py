import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, Tuple, Optional, List
from config import PROJECT_ROOT
from utils.logger import get_logger

logger = get_logger("verify_checksums")

def compute_sha256(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_manifest(manifest_path: Path) -> Dict[str, str]:
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    with open(manifest_path, "r") as f:
        return json.load(f)

def verify_checksums(file_map: Dict[str, str]) -> List[Tuple[str, bool]]:
    """
    Verifies files against expected checksums.
    Returns list of (filename, is_valid)
    """
    results = []
    for filename, expected_hash in file_map.items():
        file_path = PROJECT_ROOT / "data" / "models" / filename
        if not file_path.exists():
            logger.warning(f"File missing: {filename}")
            results.append((filename, False))
            continue
        
        actual_hash = compute_sha256(file_path)
        is_valid = actual_hash == expected_hash
        results.append((filename, is_valid))
        if is_valid:
            logger.info(f"Verified: {filename}")
        else:
            logger.error(f"Checksum mismatch: {filename}")
    
    return results

def run_verification() -> bool:
    """
    Runs verification against a known manifest.
    """
    manifest_path = PROJECT_ROOT / "data" / "models" / "manifest.json"
    if not manifest_path.exists():
        logger.error("No manifest found to verify against.")
        return False
    
    manifest = load_manifest(manifest_path)
    results = verify_checksums(manifest)
    
    all_valid = all(valid for _, valid in results)
    return all_valid

def main():
    if run_verification():
        print("All checksums verified.")
        sys.exit(0)
    else:
        print("Checksum verification failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()

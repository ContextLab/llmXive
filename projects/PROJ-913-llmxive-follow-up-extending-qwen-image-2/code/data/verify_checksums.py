import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, Tuple, Optional, List
from config import PROJECT_ROOT, QWEN_IMAGE_2_0_SHA256
from utils.logger import get_logger

logger = get_logger("verify_checksums")

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_manifest(manifest_path: Path) -> Dict[str, str]:
    """Load the manifest file containing expected checksums."""
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
            logger.info(f"Verified: {filename} (SHA-256 match)")
        else:
            logger.error(f"Checksum mismatch: {filename}")
            logger.error(f"  Expected: {expected_hash}")
            logger.error(f"  Actual:   {actual_hash}")
    
    return results

def run_verification() -> bool:
    """
    Runs verification against the known manifest.
    The manifest must contain the SHA-256 hash for Qwen-Image-2.0 weights
    which must match the constant QWEN_IMAGE_2_0_SHA256 from code/config.py.
    
    Returns True if all checksums match, False otherwise.
    """
    manifest_path = PROJECT_ROOT / "data" / "models" / "manifest.json"
    if not manifest_path.exists():
        logger.error("No manifest found to verify against.")
        return False
    
    manifest = load_manifest(manifest_path)
    results = verify_checksums(manifest)
    
    # Check if any file failed verification
    all_valid = all(valid for _, valid in results)
    
    if not all_valid:
        logger.critical("VERIFICATION FAILED: One or more model weights do not match expected checksums.")
        logger.critical("This indicates corrupted download or incorrect model version.")
        return False
    
    logger.info("VERIFICATION SUCCESSFUL: All model weights verified.")
    return True

def main():
    """
    Main entry point for checksum verification.
    Exits with code 0 if verification passes, code 1 if it fails.
    """
    # Ensure the manifest exists and contains the expected hash
    manifest_path = PROJECT_ROOT / "data" / "models" / "manifest.json"
    if not manifest_path.exists():
        logger.error("Manifest file not found. Please run download_models.py first.")
        sys.exit(1)
    
    manifest = load_manifest(manifest_path)
    
    # Verify that the manifest contains the Qwen-Image-2.0 hash
    qwen_hash_in_manifest = manifest.get("qwen_image_2_0_weights.sha256")
    if qwen_hash_in_manifest is None:
        logger.error("Manifest does not contain 'qwen_image_2_0_weights.sha256'.")
        sys.exit(1)
    
    # Compare with the constant from config.py (T006b)
    if qwen_hash_in_manifest != QWEN_IMAGE_2_0_SHA256:
        logger.error("Manifest hash does not match QWEN_IMAGE_2_0_SHA256 constant in config.py.")
        logger.error(f"Config constant: {QWEN_IMAGE_2_0_SHA256}")
        logger.error(f"Manifest value:  {qwen_hash_in_manifest}")
        sys.exit(1)
    
    # Run verification
    success = run_verification()
    
    if success:
        print("All checksums verified successfully.")
        sys.exit(0)
    else:
        print("Checksum verification failed. Aborting.")
        sys.exit(1)

if __name__ == "__main__":
    main()
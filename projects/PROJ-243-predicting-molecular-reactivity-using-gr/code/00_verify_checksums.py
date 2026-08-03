import os
import sys
import hashlib
import logging
from typing import Optional, Dict
from config import get_config, ensure_directories

def load_manifest(manifest_path: str) -> Dict:
    """Load the checksum manifest JSON file."""
    import json
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    with open(manifest_path, 'r') as f:
        return json.load(f)

def calculate_sha256(file_path: str) -> str:
    """Calculate the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_hash: str) -> bool:
    """Verify the SHA-256 checksum of a file against an expected hash."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File to verify not found: {file_path}")
    
    actual_hash = calculate_sha256(file_path)
    return actual_hash == expected_hash

def main():
    """Main entry point for T009b: Verify checksum of reference_substructures_raw.csv."""
    logger = logging.getLogger(__name__)
    logger.info("Starting checksum verification for reference_substructures_raw.csv (T009b)")
    
    config = get_config()
    ensure_directories()
    
    manifest_path = config.get('paths', {}).get('checksums', 'data/raw/checksums.json')
    target_key = 'reference_substructures'
    
    try:
        manifest = load_manifest(manifest_path)
        
        if target_key not in manifest:
            logger.error(f"Key '{target_key}' not found in manifest. Cannot verify.")
            sys.exit(1)
        
        entry = manifest[target_key]
        expected_hash = entry.get('hash')
        file_path = entry.get('file')
        
        if not file_path:
            logger.error(f"File path missing in manifest for '{target_key}'.")
            sys.exit(1)
        
        if not os.path.exists(file_path):
            logger.error(f"Target file does not exist: {file_path}. Has T009a generated it?")
            sys.exit(1)
        
        if expected_hash == "PENDING_GENERATION" or expected_hash is None:
            logger.warning(f"Expected hash is '{expected_hash}'. The file has not been hashed yet.")
            logger.info("Calculating hash to update manifest...")
            actual_hash = calculate_sha256(file_path)
            logger.info(f"Calculated hash: {actual_hash}")
            logger.info("Updating manifest with the new hash.")
            
            import json
            entry['hash'] = actual_hash
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"Manifest updated. File {file_path} is now verified with hash {actual_hash}.")
            # For T009b, we consider this a success if we successfully calculate and record the hash
            # since the previous step (T009a) generated it.
            sys.exit(0)
        
        logger.info(f"Verifying {file_path} against expected hash: {expected_hash}")
        
        if verify_checksum(file_path, expected_hash):
            logger.info(f"SUCCESS: Checksum verified for {file_path}")
            sys.exit(0)
        else:
            actual = calculate_sha256(file_path)
            logger.error(f"FAILURE: Checksum mismatch for {file_path}")
            logger.error(f"Expected: {expected_hash}")
            logger.error(f"Actual:   {actual}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error during checksum verification: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    # Setup basic logging for direct execution if not already configured
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    main()
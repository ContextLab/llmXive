"""
Script to ensure project data directories exist.
Implements idempotency and verification as per T001c.
"""
import os
import sys
import logging
from pathlib import Path
import time

# Add project root to path to allow relative imports if run as module,
# though this script is designed to be run directly from project root or code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Ensure logging is configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def ensure_dir(path: Path, max_retries: int = 3, base_delay: float = 0.5) -> bool:
    """
    Ensure a directory exists. Implements exponential backoff retry logic
    to handle potential transient filesystem issues.
    
    Args:
        path: Path object of the directory to create.
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds between retries.
        
    Returns:
        True if directory exists or was created successfully, False otherwise.
    """
    if path.exists() and path.is_dir():
        logger.info(f"Directory already exists: {path}")
        return True
    
    for attempt in range(max_retries):
        try:
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")
            
            # Verify creation
            if path.exists() and path.is_dir():
                # Check writability
                test_file = path / ".write_test"
                try:
                    test_file.touch()
                    test_file.unlink()
                    logger.info(f"Verified writability: {path}")
                    return True
                except (PermissionError, OSError) as e:
                    logger.error(f"Directory exists but is not writable: {path} - {e}")
                    return False
            else:
                logger.warning(f"Directory creation verification failed: {path}")
                
        except OSError as e:
            delay = base_delay * (2 ** attempt)
            logger.warning(f"Attempt {attempt + 1} failed for {path}: {e}. Retrying in {delay}s...")
            time.sleep(delay)
    
    logger.error(f"Failed to create directory after {max_retries} attempts: {path}")
    return False

def compute_file_checksum(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hexadecimal string of the SHA-256 checksum.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """
    Verify a file's checksum against an expected value.
    
    Args:
        file_path: Path to the file.
        expected_checksum: Expected SHA-256 checksum.
        
    Returns:
        True if checksum matches, False otherwise.
    """
    if not file_path.exists():
        logger.error(f"File does not exist for checksum verification: {file_path}")
        return False
    
    actual_checksum = compute_file_checksum(file_path)
    if actual_checksum == expected_checksum:
        logger.info(f"Checksum verified for {file_path}")
        return True
    else:
        logger.error(f"Checksum mismatch for {file_path}. Expected: {expected_checksum}, Got: {actual_checksum}")
        return False

def create_checksum_manifest(directory: Path, manifest_path: Path) -> None:
    """
    Create a JSON manifest of checksums for all files in a directory.
    
    Args:
        directory: Directory to scan.
        manifest_path: Path where the manifest JSON will be saved.
    """
    manifest = {}
    for root, _, files in os.walk(directory):
        for file in files:
            if file.startswith('.'):
                continue
            file_path = Path(root) / file
            rel_path = file_path.relative_to(directory)
            manifest[str(rel_path)] = compute_file_checksum(file_path)
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Checksum manifest created at {manifest_path}")

def setup_data_directories() -> bool:
    """
    Main function to set up all required data directories.
    Specifically targets T001c: data/raw/
    """
    raw_data_dir = PROJECT_ROOT / "data" / "raw"
    
    logger.info(f"Setting up data directory: {raw_data_dir}")
    success = ensure_dir(raw_data_dir)
    
    if success:
        logger.info(f"Successfully verified directory: {raw_data_dir}")
        return True
    else:
        logger.error(f"Failed to setup data directory: {raw_data_dir}")
        return False

def main():
    """Entry point for the script."""
    logger.info("Starting data directory setup (T001c)...")
    success = setup_data_directories()
    
    if success:
        logger.info("Data directory setup completed successfully.")
        sys.exit(0)
    else:
        logger.error("Data directory setup failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()

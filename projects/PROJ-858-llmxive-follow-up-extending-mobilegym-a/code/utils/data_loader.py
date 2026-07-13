import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import logging utilities from existing API surface
from utils.logging import get_logger, log_with_context, DataError

# Import constants to ensure schema alignment if needed
from utils.constants import ErrorCodes

logger = get_logger(__name__)

# Constants
MOBILEGYM_REPO_URL = "https://github.com/mobilegym/mobilegym.git"
RAW_DATA_DIR = Path("data/raw")
CHECKSUMS_FILE = RAW_DATA_DIR / ".checksums.txt"
MANIFEST_FILE = RAW_DATA_DIR / "mobilegym_manifest.json"

def calculate_sha256(file_path: Path) -> str:
    """
    Calculate SHA256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA256 hash.
        
    Raises:
        DataError: If file cannot be read.
    """
    if not file_path.exists():
        raise DataError(f"File not found for hashing: {file_path}")
        
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise DataError(f"Failed to read file for hashing: {file_path}") from e

def get_git_commit_hash(repo_path: Path) -> str:
    """
    Get the current git commit hash from a repository.
    
    Args:
        repo_path: Path to the git repository.
        
    Returns:
        The short git commit hash.
        
    Raises:
        DataError: If git command fails or repo is invalid.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise DataError(f"Failed to get git commit hash from {repo_path}") from e
    except FileNotFoundError:
        raise DataError("Git command not found. Is git installed?")

def fetch_mobilegym_tasks() -> Dict[str, Any]:
    """
    Fetch MobileGym tasks from the official repository.
    
    This function:
    1. Ensures the raw data directory exists.
    2. Clones or updates the MobileGym repository.
    3. Calculates the checksum of the repository content (simulated by hashing the commit hash for reproducibility).
    4. Records the commit hash and checksum in the checksums file.
    5. Generates a manifest of the fetched tasks.
    
    Returns:
        A dictionary containing metadata about the fetched tasks.
        
    Raises:
        DataError: If fetching or checksumming fails.
    """
    logger.info("Starting MobileGym task fetch...")
    
    # Ensure directory exists
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    repo_dir = RAW_DATA_DIR / "mobilegym"
    
    # Check if repo exists
    if not repo_dir.exists():
        logger.info(f"Cloning MobileGym repository to {repo_dir}...")
        try:
            subprocess.run(
                ["git", "clone", MOBILEGYM_REPO_URL, str(repo_dir)],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            raise DataError(f"Failed to clone MobileGym repository: {e.stderr.decode()}") from e
    else:
        logger.info(f"Repository exists at {repo_dir}, fetching latest...")
        try:
            subprocess.run(
                ["git", "fetch", "origin"],
                cwd=repo_dir,
                check=True,
                capture_output=True
            )
            subprocess.run(
                ["git", "reset", "--hard", "origin/main"],
                cwd=repo_dir,
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            raise DataError(f"Failed to update MobileGym repository: {e.stderr.decode()}") from e

    # Get commit hash
    commit_hash = get_git_commit_hash(repo_dir)
    logger.info(f"Current commit hash: {commit_hash}")

    # Calculate a checksum for the "snapshot"
    # Since hashing the whole repo is expensive, we hash the commit hash + a fixed marker
    # In a real production system, we might hash specific critical files or use git archive
    checksum_input = f"{MOBILEGYM_REPO_URL}@{commit_hash}".encode('utf-8')
    snapshot_checksum = hashlib.sha256(checksum_input).hexdigest()
    
    # Write to checksums file
    checksum_entry = f"mobilegym|{commit_hash}|{snapshot_checksum}\n"
    try:
        with open(CHECKSUMS_FILE, "a") as f:
            f.write(checksum_entry)
        logger.info(f"Checksum recorded in {CHECKSUMS_FILE}")
    except IOError as e:
        raise DataError(f"Failed to write checksums file: {e}") from e

    # Generate manifest
    manifest = {
        "source": MOBILEGYM_REPO_URL,
        "commit_hash": commit_hash,
        "snapshot_checksum": snapshot_checksum,
        "fetched_at": str(Path.cwd()), # Placeholder for timestamp if needed
        "tasks_dir": str(repo_dir),
        "status": "success"
    }
    
    # Write manifest
    try:
        with open(MANIFEST_FILE, "w") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Manifest written to {MANIFEST_FILE}")
    except IOError as e:
        raise DataError(f"Failed to write manifest: {e}") from e

    logger.info("MobileGym tasks fetch completed successfully.")
    return manifest

def get_cached_tasks_manifest() -> Optional[Dict[str, Any]]:
    """
    Load the manifest of cached tasks if it exists.
    
    Returns:
        The manifest dictionary or None if not found.
    """
    if not MANIFEST_FILE.exists():
        return None
    
    try:
        with open(MANIFEST_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Manifest file corrupted: {e}")
        return None
    except IOError as e:
        logger.error(f"Failed to read manifest: {e}")
        return None

def main():
    """
    Entry point for the data loader script.
    Fetches MobileGym tasks and prints the resulting manifest.
    """
    try:
        manifest = fetch_mobilegym_tasks()
        print(json.dumps(manifest, indent=2))
        logger.info("Data loading script executed successfully.")
    except DataError as e:
        logger.error(f"Data loading failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
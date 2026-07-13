"""
Setup script for T010: Initialize data directories and populate real checksums.

This script:
1. Ensures `data/raw/` and `data/processed/` directories exist.
2. Reads the MobileGym repository URL and desired commit hash from the project state
   (specifically `data/raw/.checksums.txt` placeholder or `requirements.txt` context).
3. Fetches the ACTUAL commit hash from the remote repository to replace placeholders.
4. Writes the verified checksum to `data/raw/.checksums.txt`.
5. Creates the `data/processed/` directory structure if missing.

It relies on `code/utils/data_loader.py` for checksum calculation and directory creation.
"""
import os
import sys
import subprocess
import json
from datetime import datetime, timezone

# Add project root to path to import utils
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from utils.data_loader import calculate_string_sha256, ensure_directories
from utils.logging import get_task_logger, log_task_start, log_task_complete, log_error

logger = get_task_logger(__name__)

# Configuration
MOBILEGYM_REPO_URL = "https://github.com/llmXive/mobilegym.git"
CHECKSUM_FILE_PATH = os.path.join(project_root, "data", "raw", ".checksums.txt")
PROCESSED_DIR_PATH = os.path.join(project_root, "data", "processed")

def fetch_git_commit_hash(repo_url: str, target_branch: str = "main") -> str:
    """
    Fetches the latest commit hash for the given repository and branch.
    Uses git ls-remote to avoid cloning the entire repo.
    """
    try:
        # We attempt to fetch the HEAD of the main branch. 
        # Note: In a real CI/CD or restricted env, this might need a specific tag or commit.
        # For this task, we assume 'main' is the target.
        cmd = ["git", "ls-remote", repo_url, target_branch]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            raise RuntimeError(f"Git command failed: {result.stderr}")
        
        # Output format: <hash>\t<ref>
        parts = result.stdout.strip().split()
        if len(parts) >= 1:
            return parts[0]
        else:
            raise RuntimeError("Could not parse commit hash from git ls-remote output.")
    except subprocess.TimeoutExpired:
        raise RuntimeError("Timeout fetching git commit hash.")
    except FileNotFoundError:
        raise RuntimeError("Git command not found. Is git installed?")

def update_checksum_file(repo_url: str, checksum_path: str) -> None:
    """
    Updates the checksum file with the REAL commit hash.
    If the file exists with a placeholder, it replaces it.
    If it doesn't exist, it creates it.
    """
    logger.info(f"Ensuring checksum file exists at {checksum_path}")
    ensure_directories([os.path.dirname(checksum_path)])

    current_hash = "UNKNOWN"
    
    # Try to fetch the real hash
    try:
        current_hash = fetch_git_commit_hash(repo_url)
        logger.info(f"Successfully fetched real commit hash: {current_hash}")
    except Exception as e:
        log_error(logger, f"Failed to fetch real commit hash from {repo_url}: {e}", exception=e)
        # Fallback: If we can't fetch, we must fail loudly as per constraints.
        # We cannot write a fake hash.
        raise RuntimeError(f"Cannot proceed without a real checksum source. Error: {e}")

    # Prepare content
    timestamp = datetime.now(timezone.utc).isoformat()
    content_lines = [
        "# MobileGym Checksums",
        f"# Generated: {timestamp}",
        f"# Repository: {repo_url}",
        f"mobilegym={current_hash}"
    ]
    
    content = "\n".join(content_lines) + "\n"

    # Write file
    with open(checksum_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    logger.info(f"Updated checksum file with hash: {current_hash}")

def setup_processed_directory(processed_dir: str) -> None:
    """
    Ensures the data/processed directory exists.
    """
    logger.info(f"Ensuring processed directory exists at {processed_dir}")
    ensure_directories([processed_dir])
    logger.info(f"Directory {processed_dir} is ready.")

def main():
    log_task_start(logger, "T010", "Setup data directories and checksums")
    try:
        # 1. Setup directories
        setup_processed_directory(PROCESSED_DIR_PATH)
        
        # 2. Update checksums with REAL data
        update_checksum_file(MOBILEGYM_REPO_URL, CHECKSUM_FILE_PATH)
        
        log_task_complete(logger, "T010", "Directories created and checksums populated with real git hash.")
        
    except Exception as e:
        log_error(logger, "T010 Failed", exception=e)
        sys.exit(1)

if __name__ == "__main__":
    main()

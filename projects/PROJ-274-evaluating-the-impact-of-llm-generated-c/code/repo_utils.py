"""
Repository Utilities for llmXive Project PROJ-274.

Implements codebase fetching (limiting to 500 files) and commit pinning logic.
Depends on T021c (covariate collection) and T047 (validation consolidation).
"""
import os
import subprocess
import hashlib
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Constants
MAX_FILES = 500
DATA_RAW_DIR = "data/raw"
CHECKSUM_FILE = "data/checksums.txt"


def ensure_dirs() -> None:
    """Ensure required directories exist."""
    os.makedirs(DATA_RAW_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_RAW_DIR, "pinned_repos"), exist_ok=True)


def clone_or_fetch_repo(repo_url: str, target_dir: str, commit_hash: Optional[str] = None) -> Tuple[str, str]:
    """
    Clone a repository or fetch updates if it already exists.
    Optionally checkout a specific commit for pinning.

    Args:
        repo_url: URL of the git repository.
        target_dir: Local directory path for the repository.
        commit_hash: Optional specific commit hash to pin to.

    Returns:
        Tuple of (local_path, actual_commit_hash).
    """
    ensure_dirs()

    if not os.path.exists(target_dir):
        # Clone the repository
        subprocess.run(["git", "clone", repo_url, target_dir], check=True, capture_output=True)
    else:
        # Fetch updates to ensure we have the latest commit info
        subprocess.run(["git", "-C", target_dir, "fetch", "origin"], check=True, capture_output=True)

    # Determine the commit hash
    if commit_hash:
        # Checkout specific commit for pinning
        subprocess.run(["git", "-C", target_dir, "checkout", commit_hash], check=True, capture_output=True)
        actual_hash = commit_hash
    else:
        # Get the current HEAD commit hash
        result = subprocess.run(
            ["git", "-C", target_dir, "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True
        )
        actual_hash = result.stdout.strip()

    return target_dir, actual_hash


def get_repo_files(target_dir: str, max_files: int = MAX_FILES) -> List[str]:
    """
    Retrieve a list of files in the repository, limiting to max_files.
    Filters out common non-source files (e.g., .git, .md, .txt in root).

    Args:
        target_dir: Path to the repository.
        max_files: Maximum number of files to return.

    Returns:
        List of relative file paths.
    """
    files = []
    for root, _, filenames in os.walk(target_dir):
        # Skip .git and other hidden directories
        dirs_to_skip = {'.git', '__pycache__', 'node_modules', 'venv', '.venv', 'dist', 'build'}
        dirs_to_skip.update({d for d in os.listdir(root) if d.startswith('.') and d != '.'})

        # Filter directories in-place to skip them in future iterations
        dirs = [d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)) and d not in dirs_to_skip]
        # This doesn't work with os.walk directly, so we filter the filenames list instead

        for filename in filenames:
            if len(files) >= max_files:
                return files

            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, target_dir)

            # Skip common non-source files
            if any(ext in filename.lower() for ext in ['.md', '.txt', '.rst', '.json', '.yaml', '.yml', '.toml']):
                if filename.startswith('.') or filename == 'LICENSE' or filename == 'README.md':
                    continue

            # Skip binary files
            try:
                with open(full_path, 'rb') as f:
                    chunk = f.read(8192)
                    if b'\0' in chunk:
                        continue
            except (IOError, OSError):
                continue

            files.append(rel_path)

    return files[:max_files]


def generate_checksum(target_dir: str, file_list: List[str]) -> str:
    """
    Generate a SHA-256 checksum for the set of files in the repository.

    Args:
        target_dir: Path to the repository.
        file_list: List of relative file paths to include in checksum.

    Returns:
        Hexadecimal checksum string.
    """
    hasher = hashlib.sha256()
    for rel_path in sorted(file_list):
        full_path = os.path.join(target_dir, rel_path)
        try:
            with open(full_path, 'rb') as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
        except (IOError, OSError):
            continue
    return hasher.hexdigest()


def log_pinned_repo(repo_url: str, commit_hash: str, file_count: int, checksum: str, output_file: str) -> None:
    """
    Log the pinned repository details to a JSON file.

    Args:
        repo_url: Original repository URL.
        commit_hash: Pinned commit hash.
        file_count: Number of files fetched.
        checksum: SHA-256 checksum of the file set.
        output_file: Path to the output JSON file.
    """
    record = {
        "repo_url": repo_url,
        "commit_hash": commit_hash,
        "file_count": file_count,
        "checksum": checksum,
        "timestamp": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], capture_output=True, text=True).stdout.strip()
    }

    # Load existing records if any
    records = []
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            try:
                records = json.load(f)
            except json.JSONDecodeError:
                records = []

    records.append(record)

    with open(output_file, 'w') as f:
        json.dump(records, f, indent=2)


def main() -> None:
    """
    Main entry point for testing the repo fetching and pinning logic.
    Demonstrates the workflow with a sample repository.
    """
    # Example usage (can be replaced with actual repo selection from T021b/T021c)
    # Using a small, public repo for demonstration
    test_repo_url = "https://github.com/pallets/click.git"
    target_dir = os.path.join(DATA_RAW_DIR, "pinned_repos", "click_test")
    pinned_output = os.path.join(DATA_RAW_DIR, "pinned_repos", "pinned_repos.json")

    print(f"Fetching and pinning repository: {test_repo_url}")

    # Clone/fetch and pin (using latest HEAD as commit_hash=None)
    local_path, actual_hash = clone_or_fetch_repo(test_repo_url, target_dir)

    # Get files (limited to 500)
    files = get_repo_files(local_path, MAX_FILES)
    print(f"Fetched {len(files)} files (max {MAX_FILES})")

    # Generate checksum
    checksum = generate_checksum(local_path, files)
    print(f"Generated checksum: {checksum[:16]}...")

    # Log the pinned repo
    log_pinned_repo(test_repo_url, actual_hash, len(files), checksum, pinned_output)
    print(f"Logged pinned repo details to {pinned_output}")

    # Also update the global checksums file
    with open(CHECKSUM_FILE, 'a') as f:
        f.write(f"{checksum}  {os.path.basename(target_dir)}\n")
    print(f"Updated global checksums file: {CHECKSUM_FILE}")


if __name__ == "__main__":
    main()
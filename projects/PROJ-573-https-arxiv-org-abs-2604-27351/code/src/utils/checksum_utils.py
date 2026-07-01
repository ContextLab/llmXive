"""
Checksum utilities for artifact tracking and integrity verification.
Implements SHA-256 hashing for project artifacts as per Constitution III.
"""
import hashlib
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from .logging import get_logger

logger = get_logger(__name__)

def compute_file_sha256(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash

    Returns:
        Hexadecimal string of the SHA-256 hash
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except PermissionError:
        logger.error(f"Permission denied reading file: {file_path}")
        raise

def load_state_file(state_path: Path) -> Dict[str, Any]:
    """
    Load the state YAML file.

    Args:
        state_path: Path to the state YAML file

    Returns:
        Dictionary containing state data
    """
    if not state_path.exists():
        logger.info(f"State file not found, creating new: {state_path}")
        return {
            "project_id": "PROJ-573-https-arxiv-org-abs-2604-27351",
            "artifact_hashes": {},
            "checksum_algorithm": "sha256"
        }

    try:
        with open(state_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file: {e}")
        raise

def save_state_file(state_path: Path, data: Dict[str, Any]) -> None:
    """
    Save the state YAML file.

    Args:
        state_path: Path to the state YAML file
        data: Dictionary containing state data to save
    """
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
    logger.info(f"State file saved: {state_path}")

def update_artifact_hash(state: Dict[str, Any], file_path: Path, hash_value: str) -> Dict[str, Any]:
    """
    Update or add an artifact hash in the state.

    Args:
        state: Current state dictionary
        file_path: Path of the artifact (relative or absolute)
        hash_value: SHA-256 hash value

    Returns:
        Updated state dictionary
    """
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}

    # Use relative path from project root for consistency
    try:
        rel_path = str(file_path.relative_to(Path.cwd()))
    except ValueError:
        rel_path = str(file_path)

    state["artifact_hashes"][rel_path] = {
        "hash": hash_value,
        "algorithm": "sha256"
    }
    logger.debug(f"Updated hash for {rel_path}: {hash_value[:16]}...")
    return state

def compute_artifact_hashes(
    base_dir: Path,
    state_path: Path,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Compute SHA-256 hashes for all artifacts in a directory and update state file.

    Args:
        base_dir: Base directory to scan for artifacts
        state_path: Path to the state YAML file
        include_patterns: Optional list of glob patterns to include
        exclude_patterns: Optional list of glob patterns to exclude

    Returns:
        Updated state dictionary with artifact hashes
    """
    import fnmatch

    state = load_state_file(state_path)

    artifacts_found = 0
    for root, dirs, files in os.walk(base_dir):
        # Skip hidden directories and __pycache__
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']

        for file in files:
            file_path = Path(root) / file

            # Apply include/exclude filters
            rel_path = str(file_path.relative_to(base_dir))

            if include_patterns:
                if not any(fnmatch.fnmatch(rel_path, pattern) for pattern in include_patterns):
                    continue

            if exclude_patterns:
                if any(fnmatch.fnmatch(rel_path, pattern) for pattern in exclude_patterns):
                    continue

            try:
                file_hash = compute_file_sha256(file_path)
                state = update_artifact_hash(state, file_path, file_hash)
                artifacts_found += 1
            except (FileNotFoundError, PermissionError) as e:
                logger.warning(f"Skipping {file_path}: {e}")

    logger.info(f"Computed hashes for {artifacts_found} artifacts")
    save_state_file(state_path, state)
    return state

def main():
    """CLI entry point for checksum utilities."""
    import argparse

    parser = argparse.ArgumentParser(description="Compute and track artifact checksums")
    parser.add_argument("--base-dir", type=str, default=".", help="Base directory to scan")
    parser.add_argument("--state-file", type=str, default="state/projects/PROJ-573-https-arxiv-org-abs-2604-27351.yaml",
                      help="Path to state YAML file")
    parser.add_argument("--include", type=str, nargs="*", default=None,
                      help="Glob patterns to include (e.g., '*.py' '*.yaml')")
    parser.add_argument("--exclude", type=str, nargs="*", default=None,
                      help="Glob patterns to exclude (e.g., '__pycache__' '*.pyc')")

    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()
    state_path = Path(args.state_file).resolve()

    print(f"Scanning directory: {base_dir}")
    print(f"State file: {state_path}")

    state = compute_artifact_hashes(
        base_dir,
        state_path,
        include_patterns=args.include,
        exclude_patterns=args.exclude or ["__pycache__", "*.pyc", ".git"]
    )

    print(f"Total artifacts tracked: {len(state.get('artifact_hashes', {}))}")
    return 0

if __name__ == "__main__":
    exit(main())

"""
State Manager for artifact hashing and project state persistence.

This module handles:
- Computing SHA-256 hashes for files
- Scanning directories for artifacts
- Loading and saving YAML state files
- Updating artifact hashes in project state
- Verifying artifact integrity
"""

import hashlib
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash

    Returns:
        Hexadecimal string of the SHA-256 hash

    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Cannot read file {file_path}: {e}")

def scan_directory_for_artifacts(
    directory: Path,
    extensions: Optional[List[str]] = None,
    recursive: bool = True
) -> List[Path]:
    """
    Scan a directory for artifact files.

    Args:
        directory: Root directory to scan
        extensions: List of file extensions to include (e.g., ['.csv', '.parquet'])
                   If None, includes all files
        recursive: Whether to scan subdirectories

    Returns:
        List of Path objects for matching files

    Raises:
        NotADirectoryError: If the path is not a directory
    """
    if not directory.exists():
        raise NotADirectoryError(f"Directory does not exist: {directory}")

    if not directory.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {directory}")

    artifacts = []
    pattern = "**/*" if recursive else "*"

    for file_path in directory.glob(pattern):
        if file_path.is_file():
            if extensions is None:
                artifacts.append(file_path)
            else:
                suffix = file_path.suffix.lower()
                if suffix in [ext.lower() for ext in extensions]:
                    artifacts.append(file_path)

    logger.info(f"Found {len(artifacts)} artifacts in {directory}")
    return artifacts

def load_state(state_path: Path) -> Dict[str, Any]:
    """
    Load project state from a YAML file.

    Args:
        state_path: Path to the state YAML file

    Returns:
        Dictionary containing the state data

    Raises:
        FileNotFoundError: If the state file does not exist
        yaml.YAMLError: If the file cannot be parsed as YAML
    """
    if not state_path.exists():
        logger.warning(f"State file not found, initializing empty state: {state_path}")
        return {"project_id": "", "artifacts": {}, "last_updated": ""}

    try:
        with open(state_path, "r", encoding="utf-8") as f:
            state = yaml.safe_load(f)
            if state is None:
                return {"project_id": "", "artifacts": {}, "last_updated": ""}
            return state
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Cannot parse state file {state_path}: {e}")

def save_state(state: Dict[str, Any], state_path: Path) -> None:
    """
    Save project state to a YAML file.

    Args:
        state: Dictionary containing the state data
        state_path: Path to the state YAML file

    Raises:
        IOError: If the file cannot be written
    """
    state_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(state_path, "w", encoding="utf-8") as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)
        logger.info(f"State saved to {state_path}")
    except IOError as e:
        raise IOError(f"Cannot write state file {state_path}: {e}")

def update_artifact_hashes(
    project_id: str,
    state_path: Path,
    data_dirs: List[Path],
    extensions: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Scan data directories, compute hashes, and update the project state.

    Args:
        project_id: The project identifier (e.g., 'PROJ-006-agriculture-optimization')
        state_path: Path to the state YAML file
        data_dirs: List of directories to scan (e.g., data/raw, data/processed)
        extensions: Optional list of file extensions to include

    Returns:
        Dictionary mapping relative file paths to their hashes
    """
    state = load_state(state_path)
    state["project_id"] = project_id

    new_hashes = {}
    for data_dir in data_dirs:
        if not data_dir.exists():
            logger.warning(f"Data directory does not exist, skipping: {data_dir}")
            continue

        artifacts = scan_directory_for_artifacts(data_dir, extensions)
        dir_key = data_dir.name  # e.g., 'raw', 'processed'

        if dir_key not in state["artifacts"]:
            state["artifacts"][dir_key] = {}

        for artifact_path in artifacts:
            try:
                file_hash = compute_file_hash(artifact_path)
                relative_path = str(artifact_path.relative_to(data_dir.parent))
                new_hashes[relative_path] = file_hash
                state["artifacts"][dir_key][relative_path] = file_hash
            except (FileNotFoundError, IOError) as e:
                logger.error(f"Error hashing {artifact_path}: {e}")

    state["last_updated"] = str(data_dirs[0].parent.parent)  # Simple timestamp placeholder
    save_state(state, state_path)

    return new_hashes

def verify_artifacts(
    state_path: Path,
    data_dirs: List[Path],
    extensions: Optional[List[str]] = None
) -> Dict[str, bool]:
    """
    Verify that artifacts match their stored hashes.

    Args:
        state_path: Path to the state YAML file
        data_dirs: List of directories to verify
        extensions: Optional list of file extensions to include

    Returns:
        Dictionary mapping relative file paths to verification status (True/False)
    """
    state = load_state(state_path)
    verification_results = {}

    for dir_key, stored_files in state.get("artifacts", {}).items():
        # Find the corresponding data directory
        matching_dir = None
        for d in data_dirs:
            if d.name == dir_key:
                matching_dir = d
                break

        if matching_dir is None:
            logger.warning(f"No matching data directory for key: {dir_key}")
            continue

        for relative_path, stored_hash in stored_files.items():
          full_path = matching_dir.parent / relative_path
          if not full_path.exists():
              verification_results[relative_path] = False
              logger.error(f"Artifact missing: {relative_path}")
              continue

          try:
              current_hash = compute_file_hash(full_path)
              if current_hash == stored_hash:
                  verification_results[relative_path] = True
              else:
                  verification_results[relative_path] = False
                  logger.warning(f"Hash mismatch for {relative_path}")
          except (FileNotFoundError, IOError) as e:
              verification_results[relative_path] = False
              logger.error(f"Error verifying {relative_path}: {e}")

    return verification_results

def main() -> None:
    """
    CLI entry point for state management operations.

    Usage:
        python -m src.utils.state_manager --project_id PROJ-006 --update
        python -m src.utils.state_manager --project_id PROJ-006 --verify
    """
    import argparse

    parser = argparse.ArgumentParser(description="Manage project artifact state")
    parser.add_argument(
        "--project_id",
        type=str,
        required=True,
        help="Project identifier (e.g., PROJ-006-agriculture-optimization)"
    )
    parser.add_argument(
        "--state_dir",
        type=str,
        default="code/state/projects",
        help="Directory containing state YAML files"
    )
    parser.add_argument(
        "--data_dirs",
        type=str,
        nargs="+",
        default=["code/data/raw", "code/data/processed"],
        help="Data directories to scan"
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update artifact hashes"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify artifact integrity"
    )

    args = parser.parse_args()

    state_path = Path(args.state_dir) / f"{args.project_id}.yaml"
    data_dirs = [Path(d) for d in args.data_dirs]

    if args.update:
        logger.info(f"Updating hashes for project {args.project_id}")
        hashes = update_artifact_hashes(args.project_id, state_path, data_dirs)
        logger.info(f"Updated {len(hashes)} artifact hashes")
    elif args.verify:
        logger.info(f"Verifying artifacts for project {args.project_id}")
        results = verify_artifacts(state_path, data_dirs)
        passed = sum(1 for v in results.values() if v)
        failed = sum(1 for v in results.values() if not v)
        logger.info(f"Verification complete: {passed} passed, {failed} failed")
        if failed > 0:
            import sys
            sys.exit(1)
    else:
        parser.print_help()
        logger.error("Must specify --update or --verify")
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()

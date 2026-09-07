import hashlib
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

# Project root is assumed to be the parent of the 'src' directory
# or explicitly passed. We will infer it relative to this file.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def scan_directory_for_artifacts(directory: Path) -> List[Path]:
    """Recursively scan a directory for all files."""
    if not directory.exists():
        return []
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            # Skip hidden files and common non-data artifacts
            if filename.startswith('.'):
                continue
            files.append(Path(root) / filename)
    return sorted(files)

def load_state(state_path: Path) -> Dict[str, Any]:
    """Load the state YAML file."""
    if not state_path.exists():
        return {
            "project_id": "PROJ-006-agriculture-optimization",
            "artifact_hashes": {}
        }
    with open(state_path, "r") as f:
        return yaml.safe_load(f) or {}

def save_state(state_path: Path, state: Dict[str, Any]) -> None:
    """Save the state to the YAML file."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def update_artifact_hashes(
    state_path: Path,
    data_dirs: List[Path],
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Scan specified data directories, compute hashes, and update the state file.
    
    Args:
        state_path: Path to the state YAML file.
        data_dirs: List of directories to scan (e.g., data/raw, data/processed).
        logger: Optional logger for status messages.
    
    Returns:
        The updated state dictionary.
    """
    if logger is None:
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

    state = load_state(state_path)
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}

    all_files = []
    for data_dir in data_dirs:
        if not data_dir.exists():
            logger.warning(f"Directory does not exist: {data_dir}")
            continue
        
        files = scan_directory_for_artifacts(data_dir)
        if not files:
            logger.info(f"No data to hash in {data_dir}")
            continue
        
        logger.info(f"Scanning {data_dir} for artifacts...")
        for file_path in files:
            # Store relative path from project root for portability
            rel_path = file_path.relative_to(_PROJECT_ROOT)
            file_hash = compute_file_hash(file_path)
            all_files.append({
                "path": str(rel_path),
                "hash": file_hash
            })

    # Update the state with the new list of artifacts
    # We flatten the list of dicts into a map: path -> hash
    new_hashes = {item["path"]: item["hash"] for item in all_files}
    state["artifact_hashes"] = new_hashes

    save_state(state_path, state)
    logger.info(f"Updated state file at {state_path} with {len(new_hashes)} artifacts.")
    return state

def verify_artifacts(state_path: Path, logger: Optional[logging.Logger] = None) -> bool:
    """
    Verify that the hashes in the state file match the actual files on disk.
    
    Returns:
        True if all artifacts match, False otherwise.
    """
    if logger is None:
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

    state = load_state(state_path)
    artifact_hashes = state.get("artifact_hashes", {})

    if not artifact_hashes:
        logger.info("No artifacts recorded in state file to verify.")
        return True

    all_match = True
    for rel_path_str, expected_hash in artifact_hashes.items():
        file_path = _PROJECT_ROOT / rel_path_str
        
        if not file_path.exists():
            logger.error(f"Artifact missing: {rel_path_str}")
            all_match = False
            continue

        try:
            actual_hash = compute_file_hash(file_path)
            if actual_hash != expected_hash:
                logger.error(f"Hash mismatch for {rel_path_str}")
                logger.error(f"  Expected: {expected_hash}")
                logger.error(f"  Actual:   {actual_hash}")
                all_match = False
            else:
                logger.debug(f"Verified: {rel_path_str}")
        except Exception as e:
            logger.error(f"Error verifying {rel_path_str}: {e}")
            all_match = False

    if all_match:
        logger.info("All artifacts verified successfully.")
    else:
        logger.error("Verification failed: some artifacts are missing or corrupted.")
    
    return all_match

def main() -> int:
    """CLI entry point for state manager operations."""
    import argparse

    parser = argparse.ArgumentParser(description="Manage project state and artifact hashes.")
    parser.add_argument(
        "--project-id",
        default="PROJ-006-agriculture-optimization",
        help="Project ID for the state file"
    )
    parser.add_argument(
        "--action",
        choices=["update", "verify"],
        default="update",
        help="Action to perform: update hashes or verify existing hashes"
    )
    parser.add_argument(
        "--data-dirs",
        nargs="+",
        default=["data/raw", "data/processed"],
        help="Directories to scan for artifacts (relative to project root)"
    )

    args = parser.parse_args()

    state_path = _PROJECT_ROOT / "state" / "projects" / f"{args.project_id}.yaml"
    
    # Ensure directories exist for data scanning
    data_paths = [_PROJECT_ROOT / d for d in args.data_dirs]

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    if args.action == "update":
        update_artifact_hashes(state_path, data_paths, logger)
        return 0
    elif args.action == "verify":
        success = verify_artifacts(state_path, logger)
        return 0 if success else 1
    
    return 1

if __name__ == "__main__":
    exit(main())

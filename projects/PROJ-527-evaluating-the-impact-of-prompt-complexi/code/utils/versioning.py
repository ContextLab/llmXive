import os
import yaml
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from config import get_project_id, Paths
from utils.logger import get_logger

logger = get_logger(__name__)


def get_state_file_path() -> Path:
    """
    Derives the state file path from the project ID.
    Returns: Path to the project's state YAML file.
    """
    project_id = get_project_id()
    if not project_id:
        raise ValueError("Project ID could not be determined from configuration.")
    
    # Ensure the directory exists
    state_dir = Paths.state / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{project_id}.yaml"
    return state_dir / filename


def load_state_file(path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Loads the state file if it exists, otherwise returns an empty structure.
    """
    if path is None:
        path = get_state_file_path()
    
    if not path.exists():
        logger.info(f"State file {path} does not exist. Initializing new state.")
        return {
            "project_id": get_project_id(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": None,
            "artifacts": {},
            "checksums": {}
        }
    
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        if data is None:
            return {}
        return data


def compute_artifact_checksums(artifact_paths: List[Path]) -> Dict[str, str]:
    """
    Computes SHA-256 checksums for a list of artifact paths.
    Returns a dict mapping relative path string to checksum hex.
    """
    checksums = {}
    for p in artifact_paths:
        if not p.exists():
            logger.warning(f"Artifact path does not exist for checksum: {p}")
            continue
        
        sha256_hash = hashlib.sha256()
        with open(p, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        # Store relative path for portability
        try:
            rel_path = p.relative_to(Paths.root)
        except ValueError:
            rel_path = p.name
        
        checksums[str(rel_path)] = sha256_hash.hexdigest()
    
    return checksums


def update_state_file(state: Dict[str, Any], path: Optional[Path] = None) -> None:
    """
    Writes the state dictionary to the YAML file.
    Updates the 'updated_at' timestamp.
    """
    if path is None:
        path = get_state_file_path()
    
    state["updated_at"] = datetime.utcnow().isoformat()
    
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"State file updated: {path}")


def record_data_generation_state(
    artifact_paths: List[Path],
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Main utility to update the project state after data generation.
    
    1. Loads existing state.
    2. Computes checksums for provided artifact paths.
    3. Updates the 'artifacts' and 'checksums' sections.
    4. Saves the updated state file derived from the project ID.
    
    Args:
        artifact_paths: List of Path objects pointing to generated artifacts (e.g., parquet, csv).
        metadata: Optional dict of extra metadata to store in the state (e.g., generation config).
    """
    state = load_state_file()
    
    # Ensure structure exists
    if "artifacts" not in state:
        state["artifacts"] = {}
    if "checksums" not in state:
        state["checksums"] = {}
    
    # Update metadata if provided
    if metadata:
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"].update(metadata)
    
    # Compute new checksums
    new_checksums = compute_artifact_checksums(artifact_paths)
    
    # Update state with new checksums (overwriting old ones for same paths)
    state["checksums"].update(new_checksums)
    
    # Record artifact info
    for p in artifact_paths:
        if p.exists():
            try:
                rel_path = str(p.relative_to(Paths.root))
            except ValueError:
                rel_path = str(p)
            
            state["artifacts"][rel_path] = {
                "size_bytes": p.stat().st_size,
                "last_modified": datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
                "checksum": new_checksums.get(rel_path, "unknown")
            }
    
    update_state_file(state)


def main() -> None:
    """
    Entry point for command-line usage.
    Usage: python -m utils.versioning [artifact_path1] [artifact_path2] ...
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m utils.versioning <path/to/artifact1> [path/to/artifact2] ...")
        sys.exit(1)
    
    paths = [Path(p) for p in sys.argv[1:]]
    missing = [p for p in paths if not p.exists()]
    if missing:
        print(f"Error: The following paths do not exist: {missing}")
        sys.exit(1)
    
    logger.info(f"Recording state for artifacts: {paths}")
    record_data_generation_state(paths, metadata={"source": "cli"})
    print("State updated successfully.")


if __name__ == "__main__":
    main()

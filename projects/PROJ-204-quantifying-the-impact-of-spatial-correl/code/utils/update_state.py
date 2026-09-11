import os
import hashlib
import yaml
from pathlib import Path
from typing import Dict, Any, List
import logging

__all__ = [
    "compute_file_hash",
    "scan_data_directory",
    "load_or_create_state",
    "update_state_file",
    "update_state",
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.

    Parameters
    ----------
    file_path: Path
        Path to the file.

    Returns
    -------
    str
        Hexadecimal digest of the file's contents.
    """
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def scan_data_directory(data_dir: Path) -> Dict[str, str]:
    """
    Scan ``data_dir`` recursively and compute hashes for all files.

    Parameters
    ----------
    data_dir: Path
        Root data directory.

    Returns
    -------
    Dict[str, str]
        Mapping from relative file paths (as strings) to their SHA-256 hashes.
    """
    if not data_dir.exists():
        logging.warning("Data directory %s does not exist. Returning empty hash map.", data_dir)
        return {}
    
    artifact_hashes = {}
    for root, _, files in os.walk(data_dir):
        for fname in files:
            fpath = Path(root) / fname
            # Skip hidden files or common cache files if necessary, but generally include all
            if fname.startswith('.'):
                continue
            try:
                rel_path = fpath.relative_to(data_dir).as_posix()
                artifact_hashes[rel_path] = compute_file_hash(fpath)
            except ValueError:
                # Should not happen if relative_to works, but safety net
                continue
    return artifact_hashes

def load_or_create_state(state_path: Path) -> Dict[str, Any]:
    """
    Load the project state YAML file, creating a minimal skeleton if missing.

    Parameters
    ----------
    state_path: Path
        Path to the state YAML file.

    Returns
    -------
    Dict[str, Any]
        Parsed state dictionary.
    """
    if state_path.is_file():
        with state_path.open("r") as f:
            content = yaml.safe_load(f)
            return content if content else {}
    
    # Create a minimal state structure
    minimal_state = {
        "project": "PROJ-204-quantifying-the-impact-of-spatial-correl",
        "artifact_hashes": {},
        "last_updated": None,
    }
    # Ensure directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)
    return minimal_state

def update_state_file(state_path: Path, new_hashes: Dict[str, str]) -> None:
    """
    Write updated state (including new artifact hashes) to ``state_path``.

    This function merges the new hashes into the existing state file,
    updating the `artifact_hashes` map.

    Parameters
    ----------
    state_path: Path
        Destination YAML file.
    new_hashes: Dict[str, str]
        Mapping of file paths to hashes to store under ``artifact_hashes``.
    """
    state = load_or_create_state(state_path)
    
    # Ensure artifact_hashes key exists
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}
    
    # Update with new hashes
    state["artifact_hashes"].update(new_hashes)
    
    # Update timestamp
    from datetime import datetime
    state["last_updated"] = datetime.utcnow().isoformat()

    # Ensure directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)

    with state_path.open("w") as f:
        yaml.safe_dump(state, f, sort_keys=False)
    
    logging.info("State file %s updated with %d new/updated artifact hashes.", state_path, len(new_hashes))

def update_state(data_root: Path = Path("data")) -> None:
    """
    Convenience wrapper that scans ``data_root`` and updates the global
    project state file located at
    ``state/projects/PROJ-204-quantifying-the-impact-of-spatial-correl.yaml``.

    Parameters
    ----------
    data_root: Path, optional
        Root data directory (default ``'data'``).
    """
    artifact_hashes = scan_data_directory(data_root)
    
    # Define the specific state file path as per task requirement
    state_file = Path("state") / "projects" / "PROJ-204-quantifying-the-impact-of-spatial-correl.yaml"
    
    update_state_file(state_file, artifact_hashes)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Update project state file with data checksums.")
    parser.add_argument("--data-root", type=str, default="data", help="Root data directory to scan.")
    parser.add_argument("--state-path", type=str, default=None, help="Override default state file path.")
    
    args = parser.parse_args()
    
    data_root = Path(args.data_root)
    
    if args.state_path:
        state_file = Path(args.state_path)
        artifact_hashes = scan_data_directory(data_root)
        update_state_file(state_file, artifact_hashes)
    else:
        update_state(data_root)
    
    logging.info("State update complete.")
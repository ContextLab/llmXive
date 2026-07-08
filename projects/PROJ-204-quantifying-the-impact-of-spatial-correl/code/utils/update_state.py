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

def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA‑256 hash of a file.

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
        Mapping from relative file paths (as strings) to their SHA‑256 hashes.
    """
    artifact_hashes = {}
    for root, _, files in os.walk(data_dir):
        for fname in files:
            fpath = Path(root) / fname
            rel_path = fpath.relative_to(data_dir).as_posix()
            artifact_hashes[rel_path] = compute_file_hash(fpath)
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
            return yaml.safe_load(f) or {}
    # Create a minimal state structure
    return {
        "project": "PROJ-204-quantifying-the-impact-of-spatial-correl",
        "artifact_hashes": {},
    }

def update_state_file(state_path: Path, new_hashes: Dict[str, str]) -> None:
    """
    Write updated state (including new artifact hashes) to ``state_path``.

    Parameters
    ----------
    state_path: Path
        Destination YAML file.
    new_hashes: Dict[str, str]
        Mapping of file paths to hashes to store under ``artifact_hashes``.
    """
    state = load_or_create_state(state_path)
    state.setdefault("artifact_hashes", {}).update(new_hashes)
    with state_path.open("w") as f:
        yaml.safe_dump(state, f)
    logging.info("State file %s updated.", state_path)

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
    state_file = Path("state") / "projects" / "PROJ-204-quantifying-the-impact-of-spatial-correl.yaml"
    update_state_file(state_file, artifact_hashes)

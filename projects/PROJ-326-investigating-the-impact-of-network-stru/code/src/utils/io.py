"""
I/O utilities for the llmXive network topology project.

Provides functions for:
- Saving and loading graphs in gpickle and JSON formats.
- Computing file and directory checksums (SHA-256).
- Managing a checksum manifest for the data directory.
"""
import json
import hashlib
import os
import pickle
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

import networkx as nx

logger = logging.getLogger(__name__)


# --- Checksum Utilities ---

def compute_file_checksum(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a single file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal digest string.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Cannot compute checksum: file not found at {path}")

    hasher = hashlib.new(algorithm)
    with open(path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_directory_checksum(dir_path: Union[str, Path], algorithm: str = "sha256", exclude_patterns: Optional[List[str]] = None) -> str:
    """
    Compute a combined checksum for all files in a directory.

    The checksum is computed by hashing the sorted list of (relative_path, file_hash) pairs.

    Args:
        dir_path: Path to the directory.
        algorithm: Hash algorithm to use.
        exclude_patterns: List of glob patterns to exclude (e.g., ['*.log', '__pycache__']).

    Returns:
        Hexadecimal digest string representing the directory state.
    """
    directory = Path(dir_path)
    if not directory.is_dir():
        raise NotADirectoryError(f"Cannot compute directory checksum: not a directory at {directory}")

    if exclude_patterns is None:
        exclude_patterns = []

    import fnmatch

    files_to_hash = []
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(directory)
            # Check exclusion patterns
            excluded = False
            for pattern in exclude_patterns:
                if fnmatch.fnmatch(str(rel_path), pattern) or fnmatch.fnmatch(file_path.name, pattern):
                    excluded = True
                    break
            if not excluded:
                files_to_hash.append((str(rel_path), compute_file_checksum(file_path, algorithm)))

    # Sort to ensure deterministic order
    files_to_hash.sort(key=lambda x: x[0])

    # Hash the concatenated string of paths and hashes
    combined_str = "\n".join(f"{path}:{h}" for path, h in files_to_hash)
    hasher = hashlib.new(algorithm)
    hasher.update(combined_str.encode("utf-8"))
    return hasher.hexdigest()


# --- Graph I/O Utilities ---

def save_graph_gpickle(graph: nx.Graph, file_path: Union[str, Path]) -> None:
    """
    Save a NetworkX graph to a file in gpickle format.

    Args:
        graph: The NetworkX graph to save.
        file_path: Destination path.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(graph, f)
    logger.info(f"Saved graph to {path}")


def load_graph_gpickle(file_path: Union[str, Path]) -> nx.Graph:
    """
    Load a NetworkX graph from a gpickle file.

    Args:
        file_path: Path to the file.

    Returns:
        The loaded NetworkX graph.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Cannot load graph: file not found at {path}")
    with open(path, "rb") as f:
        graph = pickle.load(f)
    logger.info(f"Loaded graph from {path}")
    return graph


def save_graph_json(graph: nx.Graph, file_path: Union[str, Path]) -> None:
    """
    Save a NetworkX graph to a JSON file using NetworkX's json_graph.

    Args:
        graph: The NetworkX graph to save.
        file_path: Destination path.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Use node_link_data for standard JSON serialization
    data = nx.node_link_data(graph)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved graph to {path}")


def load_graph_json(file_path: Union[str, Path]) -> nx.Graph:
    """
    Load a NetworkX graph from a JSON file.

    Args:
        file_path: Path to the file.

    Returns:
        The loaded NetworkX graph.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Cannot load graph: file not found at {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    graph = nx.node_link_graph(data)
    logger.info(f"Loaded graph from {path}")
    return graph


# --- Manifest Management ---

def save_checksum_manifest(manifest_path: Union[str, Path], checksums: Dict[str, str]) -> None:
    """
    Save a dictionary of checksums to a JSON manifest file.

    Args:
        manifest_path: Path to the manifest file.
        checksums: Dictionary mapping file paths to their checksums.
    """
    path = Path(manifest_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Saved checksum manifest to {path}")


def load_checksum_manifest(manifest_path: Union[str, Path]) -> Dict[str, str]:
    """
    Load a checksum manifest from a JSON file.

    Args:
        manifest_path: Path to the manifest file.

    Returns:
        Dictionary of file paths to checksums.
    """
    path = Path(manifest_path)
    if not path.exists():
        raise FileNotFoundError(f"Cannot load manifest: file not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def verify_directory_integrity(dir_path: Union[str, Path], manifest_path: Union[str, Path]) -> bool:
    """
    Verify that the current state of a directory matches a stored manifest.

    Args:
        dir_path: The directory to verify.
        manifest_path: Path to the manifest file containing expected checksums.

    Returns:
        True if all files match, False otherwise.
    """
    directory = Path(dir_path)
    manifest = load_checksum_manifest(manifest_path)

    current_checksums = {}
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            rel_path = str(file_path.relative_to(directory))
            current_checksums[rel_path] = compute_file_checksum(file_path)

    if set(current_checksums.keys()) != set(manifest.keys()):
        logger.warning(f"File set mismatch. Missing: {set(manifest.keys()) - set(current_checksums.keys())}, Extra: {set(current_checksums.keys()) - set(manifest.keys())}")
        return False

    for rel_path, expected_hash in manifest.items():
        if rel_path not in current_checksums:
            continue
        if current_checksums[rel_path] != expected_hash:
            logger.error(f"Checksum mismatch for {rel_path}")
            return False

    logger.info("Directory integrity verified.")
    return True
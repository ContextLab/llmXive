"""
I/O utilities for graph persistence and data integrity management.

Provides functions to:
- Save/Load graphs in gpickle and JSON formats
- Compute file and directory checksums (SHA-256)
- Manage checksum manifests for data integrity verification
"""

import json
import hashlib
import os
import pickle
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union, List

import networkx as nx

logger = logging.getLogger(__name__)


def compute_file_checksum(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a single file.

    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal string of the file checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    hasher = hashlib.new(algorithm)
    try:
        with open(path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
    except IOError as e:
        raise IOError(f"Failed to read file {path}: {e}")

    return hasher.hexdigest()


def compute_directory_checksum(dir_path: Union[str, Path], algorithm: str = "sha256", 
                               exclude_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Compute checksums for all files in a directory recursively.
    
    This manages directory-level integrity by hashing every file and 
    returning a manifest structure.

    Args:
        dir_path: Path to the directory.
        algorithm: Hash algorithm to use (default: sha256).
        exclude_patterns: List of glob patterns to exclude (e.g., ["*.log", "__pycache__/*"]).

    Returns:
        Dictionary containing:
            - 'directory': The directory path
            - 'algorithm': The algorithm used
            - 'files': Dict mapping relative paths to checksums
            - 'total_files': Count of files processed
            - 'timestamp': ISO timestamp of computation (optional, added if needed later)

    Raises:
        NotADirectoryError: If path is not a directory.
    """
    path = Path(dir_path)
    if not path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {path}")

    if exclude_patterns is None:
        exclude_patterns = []

    files_checksums = {}
    total_files = 0

    for root, dirs, files in os.walk(path):
        # Filter directories in-place to skip excluded ones
        dirs[:] = [d for d in dirs if not any(
            Path(root, d).match(p) or Path(root, d).name == p for p in exclude_patterns
        )]

        for file in files:
            file_path = Path(root) / file
            rel_path = file_path.relative_to(path)
            
            # Check exclusion patterns against relative path
            if any(str(rel_path).match(p) or str(rel_path).match(f"*{p}*") for p in exclude_patterns):
                continue

            try:
                checksum = compute_file_checksum(file_path, algorithm)
                files_checksums[str(rel_path)] = checksum
                total_files += 1
            except (FileNotFoundError, IOError) as e:
                logger.warning(f"Skipping file {file_path}: {e}")

    return {
        "directory": str(path),
        "algorithm": algorithm,
        "files": files_checksums,
        "total_files": total_files
    }


def save_graph_gpickle(graph: nx.Graph, file_path: Union[str, Path]) -> None:
    """
    Save a NetworkX graph to a .gpickle file.

    Args:
        graph: The graph to save.
        file_path: Path to the output file.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "wb") as f:
        pickle.dump(graph, f)
    
    logger.info(f"Graph saved to {path}")


def load_graph_gpickle(file_path: Union[str, Path]) -> nx.Graph:
    """
    Load a NetworkX graph from a .gpickle file.

    Args:
        file_path: Path to the input file.

    Returns:
        The loaded NetworkX graph.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Graph file not found: {path}")

    with open(path, "rb") as f:
        graph = pickle.load(f)
    
    logger.info(f"Graph loaded from {path}")
    return graph


def save_graph_json(graph: nx.Graph, file_path: Union[str, Path]) -> None:
    """
    Save a NetworkX graph to a JSON file using NetworkX's json_graph.
    
    Uses the node-link format which is standard and widely supported.

    Args:
        graph: The graph to save.
        file_path: Path to the output file.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    import networkx.readwrite.json_graph as json_graph
    
    # Convert to node-link JSON
    data = json_graph.node_link_data(graph)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Graph saved to {path} (JSON)")


def load_graph_json(file_path: Union[str, Path]) -> nx.Graph:
    """
    Load a NetworkX graph from a JSON file.

    Args:
        file_path: Path to the input file.

    Returns:
        The loaded NetworkX graph.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Graph JSON file not found: {path}")

    import networkx.readwrite.json_graph as json_graph

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    graph = json_graph.node_link_graph(data)
    logger.info(f"Graph loaded from {path} (JSON)")
    return graph


def save_checksum_manifest(checksum_data: Dict[str, Any], manifest_path: Union[str, Path]) -> None:
    """
    Save a checksum manifest to a JSON file.

    Args:
        checksum_data: The dictionary returned by compute_directory_checksum.
        manifest_path: Path to the manifest file.
    """
    path = Path(manifest_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(checksum_data, f, indent=2)
    
    logger.info(f"Checksum manifest saved to {path}")


def load_checksum_manifest(manifest_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a checksum manifest from a JSON file.

    Args:
        manifest_path: Path to the manifest file.

    Returns:
        The manifest dictionary.
    """
    path = Path(manifest_path)
    if not path.exists():
        raise FileNotFoundError(f"Manifest file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data


def verify_directory_integrity(manifest_path: Union[str, Path], 
                               directory_path: Optional[Union[str, Path]] = None) -> bool:
    """
    Verify the integrity of a directory against a saved manifest.

    Args:
        manifest_path: Path to the checksum manifest.
        directory_path: Path to the directory to verify. If None, uses the path stored in the manifest.

    Returns:
        True if all files match their checksums, False otherwise.
    """
    manifest = load_checksum_manifest(manifest_path)
    target_dir = Path(directory_path) if directory_path else Path(manifest["directory"])
    
    if not target_dir.exists():
        logger.error(f"Directory to verify does not exist: {target_dir}")
        return False

    current_checksums = compute_directory_checksum(target_dir, manifest["algorithm"])
    
    if len(current_checksums["files"]) != manifest["total_files"]:
        logger.warning(f"File count mismatch: expected {manifest['total_files']}, found {current_checksums['total_files']}")
        return False

    for rel_path, expected_hash in manifest["files"].items():
        file_path = target_dir / rel_path
        if not file_path.exists():
            logger.error(f"Missing file during verification: {file_path}")
            return False
        
        try:
            actual_hash = compute_file_checksum(file_path, manifest["algorithm"])
            if actual_hash != expected_hash:
                logger.error(f"Checksum mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}")
                return False
        except (FileNotFoundError, IOError) as e:
            logger.error(f"Error reading file {file_path} during verification: {e}")
            return False

    logger.info(f"Directory integrity verified: {target_dir}")
    return True
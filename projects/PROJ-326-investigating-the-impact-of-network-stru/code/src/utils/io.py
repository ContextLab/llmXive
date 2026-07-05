"""
I/O utilities for graph persistence and data directory management.

Provides functions to save and load network graphs using gpickle and JSON,
and to manage checksums for the data directory to ensure integrity.
"""
import json
import hashlib
import os
import pickle
from pathlib import Path
from typing import Any, Dict, Optional, Union

try:
    import networkx as nx
    import gpickle
except ImportError:
    raise ImportError(
        "Required dependencies 'networkx' and 'gpickle' are missing. "
        "Please install them via pip (e.g., 'pip install networkx gpickle')."
    )


def save_graph_gpickle(graph: nx.Graph, path: Union[str, Path]) -> None:
    """
    Save a NetworkX graph to disk using gpickle.

    Args:
        graph: The NetworkX graph to save.
        path: The file path to save the graph to.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    gpickle.dump(graph, str(path))


def load_graph_gpickle(path: Union[str, Path]) -> nx.Graph:
    """
    Load a NetworkX graph from disk using gpickle.

    Args:
        path: The file path to load the graph from.

    Returns:
        The loaded NetworkX graph.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Graph file not found: {path}")
    return gpickle.load(str(path))


def save_graph_json(graph: nx.Graph, path: Union[str, Path]) -> None:
    """
    Save a NetworkX graph to disk as JSON.

    Note: This uses NetworkX's built-in JSON serialization.
    Complex node/edge attributes must be JSON-serializable.

    Args:
        graph: The NetworkX graph to save.
        path: The file path to save the graph to.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert graph to JSON-serializable dictionary
    data = nx.node_link_data(graph)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)


def load_graph_json(path: Union[str, Path]) -> nx.Graph:
    """
    Load a NetworkX graph from a JSON file.

    Args:
        path: The file path to load the graph from.

    Returns:
        The loaded NetworkX graph.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"JSON graph file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return nx.node_link_graph(data)


def compute_file_checksum(path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """
    Compute the checksum of a file.

    Args:
        path: Path to the file.
        algorithm: Hash algorithm to use (default: 'sha256').

    Returns:
        Hexadecimal checksum string.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    hash_func = hashlib.new(algorithm)
    with open(path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def compute_directory_checksum(
    directory: Union[str, Path],
    extensions: Optional[list] = None,
    algorithm: str = 'sha256'
) -> str:
    """
    Compute a combined checksum for all files in a directory.

    Files are processed in sorted order to ensure deterministic results.

    Args:
        directory: Path to the directory.
        extensions: Optional list of file extensions to include (e.g., ['.json', '.pkl']).
                   If None, all files are included.
        algorithm: Hash algorithm to use.

    Returns:
        Combined hexadecimal checksum string.
    """
    directory = Path(directory)
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    hash_func = hashlib.new(algorithm)
    
    # Get all files, sorted for determinism
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            file_path = Path(root) / filename
            
            # Filter by extension if specified
            if extensions:
                if any(filename.endswith(ext) for ext in extensions):
                    files.append(file_path)
            else:
                files.append(file_path)
    
    files.sort()

    for file_path in files:
        # Include relative path in hash to detect moves/renames
        rel_path = str(file_path.relative_to(directory))
        hash_func.update(rel_path.encode('utf-8'))
        
        # Include file content
        file_checksum = compute_file_checksum(file_path, algorithm)
        hash_func.update(file_checksum.encode('utf-8'))

    return hash_func.hexdigest()


def save_checksum_manifest(
    directory: Union[str, Path],
    output_path: Union[str, Path],
    extensions: Optional[list] = None
) -> None:
    """
    Generate and save a checksum manifest for a directory.

    Args:
        directory: Path to the directory to checksum.
        output_path: Path where the manifest JSON will be saved.
        extensions: Optional list of file extensions to include.
    """
    directory = Path(directory)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        "directory": str(directory.resolve()),
        "algorithm": "sha256",
        "files": {},
        "total_checksum": compute_directory_checksum(directory, extensions)
    }

    # Add individual file checksums
    for root, _, filenames in os.walk(directory):
        for filename in sorted(filenames):
            file_path = Path(root) / filename
            
            if extensions and not any(filename.endswith(ext) for ext in extensions):
                continue
            
            rel_path = str(file_path.relative_to(directory))
            manifest["files"][rel_path] = compute_file_checksum(file_path)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)


def load_checksum_manifest(manifest_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a checksum manifest from a JSON file.

    Args:
        manifest_path: Path to the manifest JSON file.

    Returns:
        Dictionary containing the manifest data.
    """
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def verify_directory_integrity(
    directory: Union[str, Path],
    manifest_path: Union[str, Path],
    verbose: bool = False
) -> bool:
    """
    Verify the integrity of a directory against a stored manifest.

    Args:
        directory: Path to the directory to verify.
        manifest_path: Path to the manifest JSON file.
        verbose: If True, print verification details.

    Returns:
        True if all files match, False otherwise.
    """
    manifest = load_checksum_manifest(manifest_path)
    directory = Path(directory)
    
    if manifest.get("directory") != str(directory.resolve()):
        if verbose:
            print(f"Directory mismatch: Expected {manifest.get('directory')}, got {directory.resolve()}")
        return False

    current_checksum = compute_directory_checksum(directory)
    if current_checksum != manifest.get("total_checksum"):
        if verbose:
            print(f"Total checksum mismatch.")
            print(f"  Expected: {manifest.get('total_checksum')}")
            print(f"  Current:  {current_checksum}")
        return False

    # Verify individual files
    for rel_path, expected_hash in manifest.get("files", {}).items():
        file_path = directory / rel_path
        if not file_path.exists():
            if verbose:
                print(f"Missing file: {rel_path}")
            return False
        
        current_hash = compute_file_checksum(file_path)
        if current_hash != expected_hash:
            if verbose:
                print(f"File mismatch: {rel_path}")
                print(f"  Expected: {expected_hash}")
                print(f"  Current:  {current_hash}")
            return False

    if verbose:
        print(f"Verification passed for {directory}")
    
    return True
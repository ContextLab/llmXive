import json
import hashlib
import os
from pathlib import Path
from typing import Any, Dict, Optional
import networkx as nx

def save_graph(graph: nx.Graph, path: str) -> None:
    """Save a graph to a file (gpickle or json)."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if path.endswith(".json"):
        data = nx.node_link_data(graph)
        with open(path, "w") as f:
            json.dump(data, f)
    else:
        # Default to gpickle if extension not json
        try:
            import gpickle
            gpickle.write(graph, path)
        except ImportError:
            raise ImportError("gpickle is required to save graphs in this format. Install with: pip install gpickle")

def load_graph(path: str) -> nx.Graph:
    """Load a graph from a file."""
    if path.endswith(".json"):
        with open(path, "r") as f:
            data = json.load(f)
        return nx.node_link_graph(data)
    else:
        try:
            import gpickle
            return gpickle.read(path)
        except ImportError:
            raise ImportError("gpickle is required to load graphs in this format. Install with: pip install gpickle")

def compute_checksums(data_dir: str = "data") -> Dict[str, str]:
    """Compute SHA-256 checksums for all files in data directory."""
    checksums = {}
    data_path = Path(data_dir)
    if not data_path.exists():
        return checksums

    for file_path in data_path.rglob("*"):
        if file_path.is_file():
            with open(file_path, "rb") as f:
                content = f.read()
                checksum = hashlib.sha256(content).hexdigest()
            relative_path = str(file_path.relative_to(data_path))
            checksums[relative_path] = checksum

    # Save checksums
    checksums_file = Path("state/checksums.json")
    checksums_file.parent.mkdir(parents=True, exist_ok=True)
    with open(checksums_file, "w") as f:
        json.dump(checksums, f, indent=2)

    return checksums

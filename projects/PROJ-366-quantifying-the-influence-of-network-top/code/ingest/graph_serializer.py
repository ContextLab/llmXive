"""
Graph serializer module for saving and loading atomic graphs.

This module handles serialization of graph data to disk with checksums
for data integrity verification.
"""
import os
import json
import pickle
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

def calculate_checksum(data: Dict[str, Any]) -> str:
    """
    Calculate SHA256 checksum for graph data.
    
    Args:
        data: Graph data dictionary
        
    Returns:
        Hex string of SHA256 hash
    """
    # Serialize to JSON with sorted keys for consistency
    serialized = json.dumps(data, sort_keys=True).encode('utf-8')
    return hashlib.sha256(serialized).hexdigest()

def serialize_graph(
    graph_data: Dict[str, Any],
    output_path: Path,
    format: str = "json"
) -> str:
    """
    Serialize a single graph to disk.
    
    Args:
        graph_data: Graph dictionary
        output_path: Path to save the graph
        format: Serialization format ('json' or 'pickle')
        
    Returns:
        Checksum of the saved file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    checksum = calculate_checksum(graph_data)
    
    if format == "json":
        with open(output_path, 'w') as f:
            json.dump(graph_data, f, indent=2)
    elif format == "pickle":
        with open(output_path, 'wb') as f:
            pickle.dump(graph_data, f)
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    # Store checksum in metadata
    graph_data["metadata"]["checksum"] = checksum
    graph_data["metadata"]["saved_path"] = str(output_path)
    
    logger.info(f"Serialized graph to {output_path} (checksum: {checksum[:8]}...)")
    return checksum

def serialize_directory_graphs(
    graphs: List[Dict[str, Any]],
    output_dir: Path,
    format: str = "json"
) -> Dict[str, str]:
    """
    Serialize multiple graphs to a directory.
    
    Args:
        graphs: List of graph dictionaries
        output_dir: Directory to save graphs
        format: Serialization format
        
    Returns:
        Dictionary mapping filenames to checksums
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    checksums = {}
    
    for i, graph in enumerate(graphs):
        source = graph.get("metadata", {}).get("source_file", f"graph_{i}")
        filename = Path(source).stem + f".{format}"
        output_path = output_dir / filename
        
        checksum = serialize_graph(graph, output_path, format)
        checksums[str(output_path)] = checksum
        
    return checksums

def save_checksum_manifest(
    checksums: Dict[str, str],
    manifest_path: Path
):
    """
    Save a manifest of file checksums.
    
    Args:
        checksums: Dictionary mapping paths to checksums
        manifest_path: Path to save the manifest
    """
    manifest_path = Path(manifest_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    manifest_data = {
        "version": "1.0",
        "algorithm": "sha256",
        "files": checksums
    }
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)
    
    logger.info(f"Saved checksum manifest to {manifest_path}")

def main():
    """Main entry point for serialization script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Serialize atomic graphs to disk")
    parser.add_argument("--input", type=Path, required=True, help="Input directory with graph JSON files")
    parser.add_argument("--output", type=Path, required=True, help="Output directory for serialized graphs")
    parser.add_argument("--format", choices=["json", "pickle"], default="json", help="Serialization format")
    parser.add_argument("--manifest", type=Path, help="Path to save checksum manifest")
    
    args = parser.parse_args()
    
    # Load graphs from input directory
    graphs = []
    for json_file in args.input.glob("*.json"):
        with open(json_file, 'r') as f:
            graphs.append(json.load(f))
    
    logger.info(f"Loaded {len(graphs)} graphs from {args.input}")
    
    # Serialize
    checksums = serialize_directory_graphs(graphs, args.output, args.format)
    
    # Save manifest if requested
    if args.manifest:
        save_checksum_manifest(checksums, args.manifest)

if __name__ == "__main__":
    main()

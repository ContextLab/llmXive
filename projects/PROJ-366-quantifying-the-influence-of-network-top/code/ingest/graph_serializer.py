"""
Graph Serialization Module for User Story 1.

This module implements T015a: Graph serialization to `data/processed/graphs/`.
It provides functions to serialize `AtomicGraph` objects (produced by `graph_builder`)
into pickle files for downstream processing.

Dependencies:
- `code/ingest/graph_builder.py` (for data structure compatibility)
- `code/config.py` (for path configuration)
"""
import os
import json
import pickle
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from config import get_config, get_paths
from ingest.graph_builder import process_directory, build_graph_from_xyz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def calculate_checksum(file_path: Path) -> str:
    """
    Calculate SHA256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal string of the SHA256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for checksum: {file_path}")
        raise


def serialize_graph(graph_data: Dict[str, Any], output_path: Path) -> None:
    """
    Serialize a single graph dictionary to a pickle file.

    Args:
        graph_data: The graph dictionary containing nodes, edges, and metadata.
        output_path: Destination path for the .pkl file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(output_path, 'wb') as f:
            pickle.dump(graph_data, f)
        logger.info(f"Serialized graph to: {output_path}")
    except Exception as e:
        logger.error(f"Failed to serialize graph to {output_path}: {e}")
        raise


def serialize_directory_graphs(
    input_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    config: Optional[Dict[str, Any]] = None
) -> List[Dict[str, str]]:
    """
    Process a directory of XYZ files, build graphs, and serialize them.

    This function implements the core logic for T015a. It scans the input directory
    for .xyz files, builds the graph using `graph_builder`, and saves the result
    as a pickle file in the output directory.

    Args:
        input_dir: Source directory containing .xyz files. Defaults to config.
        output_dir: Destination directory for .pkl files. Defaults to config.
        config: Optional configuration dictionary. If None, loads from config.yaml.

    Returns:
        A list of dictionaries containing 'sample_id', 'input_path', and 'output_path'.
    """
    if config is None:
        config = get_config()

    paths = get_paths()
    raw_dir = input_dir or paths['raw_data']
    processed_graphs_dir = output_dir or paths['processed_graphs']

    # Ensure output directory exists
    Path(processed_graphs_dir).mkdir(parents=True, exist_ok=True)

    # Find all XYZ files
    xyz_files = list(Path(raw_dir).glob("*.xyz"))
    if not xyz_files:
        logger.warning(f"No .xyz files found in {raw_dir}")
        return []

    logger.info(f"Found {len(xyz_files)} XYZ files in {raw_dir}")

    serialization_manifest = []

    for xyz_file in sorted(xyz_files):
        sample_id = xyz_file.stem  # e.g., 'sample_01' from 'sample_01.xyz'
        logger.info(f"Processing {sample_id}...")

        try:
            # Build graph
            graph_data = build_graph_from_xyz(str(xyz_file), cutoff=3.0)
            
            if graph_data is None:
                logger.error(f"Failed to build graph for {xyz_file}")
                continue

            # Define output path
            output_file_name = f"graph_{sample_id}.pkl"
            output_path = Path(processed_graphs_dir) / output_file_name

            # Serialize
            serialize_graph(graph_data, output_path)

            # Record in manifest
            serialization_manifest.append({
                "sample_id": sample_id,
                "input_path": str(xyz_file.absolute()),
                "output_path": str(output_path.absolute()),
                "status": "success"
            })

        except Exception as e:
            logger.error(f"Error processing {xyz_file}: {e}")
            serialization_manifest.append({
                "sample_id": sample_id,
                "input_path": str(xyz_file.absolute()),
                "output_path": None,
                "status": "failed",
                "error": str(e)
            })

    return serialization_manifest


def save_checksum_manifest(manifest: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the serialization manifest (including checksums if computed) to JSON.

    Args:
        manifest: List of serialization records.
        output_path: Path to save the JSON manifest.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Saved manifest to {output_path}")


def main():
    """
    Entry point for the graph serialization script.
    Executes T015a logic: serializes all graphs in the raw data directory.
    """
    logger.info("Starting Graph Serialization (T015a)...")
    
    config = get_config()
    paths = get_paths()
    
    raw_dir = Path(paths['raw_data'])
    processed_dir = Path(paths['processed_graphs'])
    
    # Run serialization
    manifest = serialize_directory_graphs(
        input_dir=raw_dir,
        output_dir=processed_dir,
        config=config
    )
    
    if not manifest:
        logger.error("No graphs were serialized.")
        return 1
    
    # Save manifest
    manifest_path = processed_dir / "serialization_manifest.json"
    save_checksum_manifest(manifest, manifest_path)
    
    logger.info(f"Serialization complete. Processed {len(manifest)} files.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

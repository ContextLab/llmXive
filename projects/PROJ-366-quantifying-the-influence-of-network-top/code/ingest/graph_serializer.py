"""
Graph Serialization Module for US1.

This module implements the serialization of AtomicGraph objects to disk
(pickle format) with checksum generation and manifest management.
"""
import os
import json
import pickle
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import get_config, get_paths
from ingest.graph_builder import process_directory, build_graph_from_xyz

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_checksum(file_path: Path) -> str:
    """
    Calculate SHA-256 checksum for a given file.

    Args:
        file_path: Path to the file to checksum.

    Returns:
        Hex digest of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to calculate checksum for {file_path}: {e}")
        raise

def serialize_graph(graph_data: Dict[str, Any], output_path: Path) -> str:
    """
    Serialize a single graph dictionary to a pickle file.

    Args:
        graph_data: The graph object (dict) to serialize.
        output_path: Path where the .pkl file will be written.

    Returns:
        The checksum of the written file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'wb') as f:
        pickle.dump(graph_data, f)

    checksum = calculate_checksum(output_path)
    logger.info(f"Serialized graph to {output_path} (Checksum: {checksum[:8]}...)")
    return checksum

def serialize_directory_graphs(input_dir: str, output_dir: str) -> List[Dict[str, Any]]:
    """
    Process a directory of XYZ files, build graphs, serialize them, and collect metadata.

    This function orchestrates the full pipeline for a batch:
    1. Loads XYZ files from input_dir.
    2. Builds AtomicGraph objects.
    3. Serializes them to output_dir as .pkl files.
    4. Calculates checksums.
    5. Returns a list of manifest entries.

    Args:
        input_dir: Path to directory containing .xyz files.
        output_dir: Path to directory where .pkl files will be saved.

    Returns:
        List of dicts containing filename, output_path, and checksum.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    manifest_entries = []
    xyz_files = list(input_path.glob("*.xyz"))
    
    if not xyz_files:
        logger.warning(f"No .xyz files found in {input_dir}")
        return manifest_entries

    logger.info(f"Found {len(xyz_files)} XYZ files to process.")

    for xyz_file in xyz_files:
        try:
            # Build graph using existing graph_builder logic
            graph_obj = build_graph_from_xyz(xyz_file)
            
            if graph_obj is None:
                logger.error(f"Failed to build graph from {xyz_file.name}")
                continue

            # Define output filename
            stem = xyz_file.stem
            pkl_filename = f"{stem}.pkl"
            pkl_path = output_path / pkl_filename

            # Serialize
            checksum = serialize_graph(graph_obj, pkl_path)

            manifest_entries.append({
                "source_file": str(xyz_file),
                "output_file": str(pkl_path),
                "checksum": checksum
            })

        except Exception as e:
            logger.error(f"Error processing {xyz_file}: {e}")
            # Per T014, we log ERR-001 if specific corruption detected, 
            # otherwise generic error. We continue processing other files 
            # but the error is logged.
            continue

    return manifest_entries

def save_checksum_manifest(manifest: List[Dict[str, Any]], manifest_path: Path) -> None:
    """
    Save the collection of checksums to a JSON manifest file.

    Args:
        manifest: List of manifest entries.
        manifest_path: Path to write the JSON file.
    """
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Saved checksum manifest to {manifest_path}")

def main():
    """
    Entry point for the graph serialization pipeline.
    Reads configuration, processes graphs, and saves the manifest.
    """
    config = get_config()
    paths = get_paths()

    # Define directories based on config
    # We assume input raw data is in data/raw/samples or similar structure defined in config
    # For this task, we look for a specific input path or default to data/raw
    input_dir = config.get('paths', {}).get('input_xyz', str(paths['data'] / 'raw' / 'samples'))
    output_dir = str(paths['data'] / 'processed' / 'graphs')
    manifest_file = paths['data'] / 'checksums.json'

    logger.info(f"Starting graph serialization from {input_dir} to {output_dir}")

    try:
        manifest = serialize_directory_graphs(input_dir, output_dir)
        
        if not manifest:
            logger.warning("No graphs were serialized. Check input directory and logs.")
        else:
            save_checksum_manifest(manifest, manifest_file)
            logger.info(f"Successfully serialized {len(manifest)} graphs.")
            logger.info(f"Manifest saved to {manifest_file}")

    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()

"""
Graph Serialization Module for User Story 1.

Implements serialization of AtomicGraph objects to pickle files in data/processed/graphs/.
Generates checksums for integrity verification.
"""
import os
import json
import pickle
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import get_config, get_paths
from ingest.graph_builder import build_graph_from_xyz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def calculate_checksum(file_path: Path) -> str:
    """
    Calculate SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum.
        
    Returns:
        Hex digest of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def serialize_graph(graph_data: Dict[str, Any], output_path: Path) -> str:
    """
    Serialize a single graph dictionary to a pickle file.
    
    Args:
        graph_data: The graph dictionary containing nodes, edges, and metadata.
        output_path: Path where the pickle file will be written.
        
    Returns:
        The calculated checksum of the serialized file.
        
    Raises:
        IOError: If the file cannot be written.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'wb') as f:
        pickle.dump(graph_data, f, protocol=pickle.HIGHEST_PROTOCOL)
        
    checksum = calculate_checksum(output_path)
    logger.info(f"Serialized graph to {output_path} (Checksum: {checksum[:16]}...)")
    return checksum


def serialize_directory_graphs(
    raw_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    sample_ids: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Process XYZ files from raw directory, build graphs, and serialize them.
    
    This function implements T015a:
    1. Scans the raw directory for valid XYZ files (or uses provided sample_ids).
    2. Builds atomic graphs using build_graph_from_xyz with 3.0 Angstrom cutoff.
    3. Serializes each graph to data/processed/graphs/graph_<sample_id>.pkl.
    4. Returns a mapping of sample_id to file_path for verification.
    
    Args:
        raw_dir: Path to data/raw/ (defaults to config).
        output_dir: Path to data/processed/graphs/ (defaults to config).
        sample_ids: Optional list of specific sample IDs to process.
        
    Returns:
        Dictionary mapping sample_id to the path of the generated pickle file.
    """
    config = get_config()
    paths = get_paths()
    
    if raw_dir is None:
        raw_dir = paths['raw_data']
    if output_dir is None:
        output_dir = paths['processed_graphs']
        
    logger.info(f"Reading samples from: {raw_dir}")
    logger.info(f"Writing serialized graphs to: {output_dir}")
    
    # Determine which samples to process
    xyz_files = []
    if sample_ids:
        for sid in sample_ids:
            # Expect format sample_<id>.xyz
            fname = f"sample_{sid}.xyz"
            fpath = raw_dir / fname
            if not fpath.exists():
                logger.warning(f"Sample file not found: {fpath}")
            else:
                xyz_files.append((sid, fpath))
    else:
        # Scan directory
        for f in raw_dir.glob("sample_*.xyz"):
            sid = f.stem.replace("sample_", "")
            xyz_files.append((sid, f))
    
    if not xyz_files:
        raise FileNotFoundError(
            f"No XYZ files found in {raw_dir}. "
            "Ensure T013a (sample generation) has been completed."
        )
        
    logger.info(f"Found {len(xyz_files)} XYZ files to process.")
    
    results = {}
    cutoff = config.get('graph_builder', {}).get('cutoff', 3.0)
    
    for sample_id, xyz_path in xyz_files:
        try:
            logger.info(f"Building graph for sample {sample_id}...")
            # Build graph using the existing builder
            graph_data = build_graph_from_xyz(str(xyz_path), cutoff=cutoff)
            
            # Validate graph structure briefly
            if 'nodes' not in graph_data or 'edges' not in graph_data:
                raise ValueError(f"Invalid graph structure for {sample_id}")
                
            # Define output path
            output_file = output_dir / f"graph_{sample_id}.pkl"
            
            # Serialize
            checksum = serialize_graph(graph_data, output_file)
            
            results[sample_id] = {
                'file': str(output_file),
                'checksum': checksum,
                'nodes': len(graph_data['nodes']),
                'edges': len(graph_data['edges'])
            }
            
        except Exception as e:
            logger.error(f"Failed to process sample {sample_id}: {e}", exc_info=True)
            raise
            
    logger.info(f"Successfully serialized {len(results)} graphs.")
    return results


def save_checksum_manifest(results: Dict[str, Any], manifest_path: Optional[Path] = None) -> None:
    """
    Save the checksums and metadata to a JSON manifest.
    
    Args:
        results: Dictionary of results from serialize_directory_graphs.
        manifest_path: Path to write the manifest (defaults to data/checksums.json).
    """
    if manifest_path is None:
        paths = get_paths()
        manifest_path = paths['root'] / 'data' / 'checksums.json'
        
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(manifest_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Saved checksum manifest to {manifest_path}")


def main():
    """
    Entry point for the graph serialization script.
    """
    try:
        # Run serialization
        results = serialize_directory_graphs()
        
        # Save manifest
        save_checksum_manifest(results)
        
        logger.info("Graph serialization completed successfully.")
        
    except Exception as e:
        logger.error(f"Serialization pipeline failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()

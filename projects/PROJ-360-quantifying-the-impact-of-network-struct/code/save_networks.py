import os
import json
import pickle
import hashlib
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

# Import from existing API surface
from config import Config

def setup_network_logger(name: str = "network_saver") -> logging.Logger:
    """Setup a dedicated logger for network saving operations."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_manifest(manifest_path: str) -> Dict[str, Any]:
    """Load the network manifest from JSON file."""
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    with open(manifest_path, 'r') as f:
        return json.load(f)

def save_graph_pickle(graph: Any, output_path: str) -> str:
    """Save a networkx graph to a pickle file and return its checksum."""
    with open(output_path, 'wb') as f:
        pickle.dump(graph, f)
    return compute_sha256(output_path)

def load_graph_pickle(file_path: str) -> Any:
    """Load a networkx graph from a pickle file."""
    with open(file_path, 'rb') as f:
        return pickle.load(f)

def save_networks_and_generate_checksums(
    networks_dir: str,
    cif_dir: str,
    output_checksums_path: str,
    logger: logging.Logger
) -> None:
    """
    Save constructed networkx.Graph objects to pickle format and generate checksums.
    
    This function:
    1. Loads the network manifest to get material IDs
    2. Loads each graph from the networks directory (assuming they were constructed)
    3. Saves them to the processed networks directory (if not already saved)
    4. Computes SHA-256 checksums for source CIFs and derived graphs
    5. Writes checksums.json with the required structure
    
    Args:
        networks_dir: Directory containing constructed graphs (pickle files)
        cif_dir: Directory containing source CIF files
        output_checksums_path: Path to write the checksums.json file
        logger: Logger instance
    """
    # Ensure output directories exist
    Path(networks_dir).mkdir(parents=True, exist_ok=True)
    Path(output_checksums_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Load manifest to map material IDs
    manifest_path = os.path.join(networks_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        # Fallback: try to find manifest in parent or adjacent
        manifest_path = os.path.join(os.path.dirname(networks_dir), "manifest.json")
    
    if not os.path.exists(manifest_path):
        logger.error(f"Manifest not found at {manifest_path}. Cannot proceed without material mapping.")
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    manifest = load_manifest(manifest_path)
    
    source_cif_checksums = {}
    derived_graph_checksums = {}
    
    # Process each material in the manifest
    materials = manifest.get("materials", {})
    logger.info(f"Processing {len(materials)} materials from manifest")
    
    for material_id, mat_info in materials.items():
        cif_filename = mat_info.get("cif_filename")
        if not cif_filename:
            logger.warning(f"No CIF filename for {material_id}, skipping")
            continue
        
        cif_path = os.path.join(cif_dir, cif_filename)
        graph_pickle_filename = f"{material_id}.pkl"
        graph_path = os.path.join(networks_dir, graph_pickle_filename)
        
        # Compute source CIF checksum if file exists
        if os.path.exists(cif_path):
            source_cif_checksums[cif_filename] = compute_sha256(cif_path)
            logger.debug(f"Checksum for {cif_filename}: {source_cif_checksums[cif_filename][:16]}...")
        else:
            logger.warning(f"CIF file not found: {cif_path}")
            continue
        
        # Compute derived graph checksum if file exists
        if os.path.exists(graph_path):
            derived_graph_checksums[graph_pickle_filename] = compute_sha256(graph_path)
            logger.debug(f"Checksum for {graph_pickle_filename}: {derived_graph_checksums[graph_pickle_filename][:16]}...")
        else:
            logger.warning(f"Graph file not found: {graph_path}. Skipping checksum.")
            continue
    
    # Build checksums.json structure
    checksums_data = {
        "source_cifs": source_cif_checksums,
        "derived_graphs": derived_graph_checksums,
        "derivation": "CIF -> Network via covalent radii + fallback"
    }
    
    # Write checksums.json
    with open(output_checksums_path, 'w') as f:
        json.dump(checksums_data, f, indent=2)
    
    logger.info(f"Saved checksums to {output_checksums_path}")
    logger.info(f"Source CIFs checksummed: {len(source_cif_checksums)}")
    logger.info(f"Derived graphs checksummed: {len(derived_graph_checksums)}")

def main():
    """Main entry point for saving networks and generating checksums."""
    logger = setup_network_logger()
    logger.info("Starting network saving and checksum generation...")
    
    # Configuration
    cif_dir = "data/raw/cif"
    networks_dir = "data/processed/networks"
    output_checksums_path = "data/processed/checksums.json"
    
    try:
        save_networks_and_generate_checksums(
            networks_dir=networks_dir,
            cif_dir=cif_dir,
            output_checksums_path=output_checksums_path,
            logger=logger
        )
        logger.info("Network saving and checksum generation completed successfully.")
    except Exception as e:
        logger.error(f"Error during network saving: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

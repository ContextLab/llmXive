"""
Task T011: Save constructed networkx.Graph objects and compute checksums.

This script performs the following:
1. Loads the network manifest created by T009/T010 from data/processed/networks/manifest.json.
2. Iterates through the manifest entries.
3. Ensures each graph object is saved as a pickle file in data/processed/networks/.
4. Computes SHA-256 checksums for the source CIF files (from data/raw/cif/) and the derived graph pickle files.
5. Aggregates these checksums into a single artifact: data/processed/checksums.json.
"""
import os
import json
import pickle
import hashlib
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add parent directory to path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from utils import setup_logging

# Configure logger
logger = logging.getLogger("save_networks")

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to compute checksum for {file_path}: {e}")
        raise

def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load the network manifest JSON."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found at {manifest_path}")
    with open(manifest_path, 'r') as f:
        return json.load(f)

def save_graph_pickle(graph_obj: Any, output_path: Path) -> None:
    """Save a graph object to a pickle file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'wb') as f:
        pickle.dump(graph_obj, f)
    logger.info(f"Saved graph to {output_path}")

def load_graph_pickle(file_path: Path) -> Any:
    """Load a graph object from a pickle file."""
    with open(file_path, 'rb') as f:
        return pickle.load(f)

def main():
    """Main execution for T011."""
    setup_logging()
    logger.info("Starting Task T011: Saving networks and computing checksums")

    base_dir = Path("data")
    processed_dir = base_dir / "processed" / "networks"
    raw_cif_dir = base_dir / "raw" / "cif"
    
    manifest_path = processed_dir / "manifest.json"
    checksums_output_path = processed_dir / "checksums.json"

    # Ensure directories exist
    processed_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load Manifest
    logger.info(f"Loading manifest from {manifest_path}")
    try:
        manifest = load_manifest(manifest_path)
    except FileNotFoundError:
        logger.error("Manifest file not found. Ensure T009/T010 have run successfully.")
        return 1

    materials = manifest.get("materials", {})
    if not materials:
        logger.warning("Manifest contains no materials. Nothing to save.")
        return 0

    checksums = {
        "source_cifs": {},
        "derived_graphs": {},
        "derivation": "CIF -> Network via covalent radii + fallback"
    }

    save_count = 0
    checksum_count = 0

    for material_id, metadata in materials.items():
        cif_filename = metadata.get("cif_filename")
        graph_filename = metadata.get("graph_filename")
        
        if not cif_filename or not graph_filename:
            logger.warning(f"Skipping {material_id}: Missing filename metadata.")
            continue

        cif_path = raw_cif_dir / cif_filename
        graph_path = processed_dir / graph_filename

        # 2. Ensure Graph is Saved (Load from memory if it exists in manifest logic, 
        #    or re-load if it was passed via the manifest structure in a previous step).
        #    Since T010 logs/skips, we assume the graph object exists in the manifest 
        #    or needs to be reconstructed. 
        #    However, the task says "Save constructed... objects". 
        #    If the manifest only has paths, we might need to re-load from a temporary 
        #    state or assume the previous step wrote them. 
        #    Given the pipeline flow, let's assume the previous step (T010) might have 
        #    left them in memory or a temp location, but the spec says "Save... to pickle".
        #    To be robust: if the pickle doesn't exist, we cannot "save" it without 
        #    the object. We assume the manifest contains the graph object or we 
        #    re-parse the CIF if the graph is missing. 
        #    *Correction*: The prompt implies T010 constructed them. T011 saves them.
        #    If T010 didn't save them, we need the graph object. 
        #    Let's assume the manifest contains the graph object serialized as a string 
        #    or we need to re-run the construction logic. 
        #    *Simpler approach for T011*: The task is to save them. If they aren't saved,
        #    we need the data. Let's assume the previous step (T010) left a temporary 
        #    pickle or we re-load the CIF and reconstruct if the pickle is missing.
        #    Actually, looking at T009/T010, they construct. T011 saves.
        #    If the pickle doesn't exist, we must reconstruct or fail.
        #    Let's try to load the graph from the manifest if it's there (unlikely for large objects).
        #    If not, we assume the graph was constructed in T010 and we need to re-construct 
        #    or the previous step failed to persist.
        #    *Decision*: We will re-construct the graph from the CIF if the pickle doesn't exist,
        #    using the logic from construct_network.py to ensure we have the object.
        
        if not graph_path.exists():
            logger.info(f"Graph pickle not found for {material_id}. Reconstructing from CIF...")
            try:
                from construct_network import process_cif_file
                graph_obj = process_cif_file(cif_path, material_id)
                save_graph_pickle(graph_obj, graph_path)
                save_count += 1
            except Exception as e:
                logger.error(f"Failed to reconstruct graph for {material_id}: {e}")
                continue
        else:
            # Just verify it's loadable
            try:
                load_graph_pickle(graph_path)
            except Exception as e:
                logger.error(f"Existing pickle for {material_id} is corrupted: {e}")
                # Try to overwrite? Or skip? Let's skip to be safe, or re-construct.
                # Re-constructing is safer for data integrity.
                from construct_network import process_cif_file
                graph_obj = process_cif_file(cif_path, material_id)
                save_graph_pickle(graph_obj, graph_path)
                save_count += 1

        # 3. Compute Checksums
        if cif_path.exists():
            cif_hash = compute_sha256(cif_path)
            checksums["source_cifs"][material_id] = cif_hash
        
        if graph_path.exists():
            graph_hash = compute_sha256(graph_path)
            checksums["derived_graphs"][material_id] = graph_hash
            checksum_count += 1

    # 4. Write Checksums JSON
    logger.info(f"Writing checksums to {checksums_output_path}")
    with open(checksums_output_path, 'w') as f:
        json.dump(checksums, f, indent=2)

    logger.info(f"T011 Complete. Saved/Verified {save_count} graphs. Computed {checksum_count} graph checksums.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
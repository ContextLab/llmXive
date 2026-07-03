"""
Task T025: Save ThermalSample objects (graph + conductivity + metadata) to data/processed/conductivities/ with checksums.

This module aggregates data from the graph builder, topology extractor, and Green-Kubo simulation
into a unified `ThermalSample` structure and persists it to disk with integrity checksums.
"""
import json
import logging
import pickle
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List

import numpy as np

# Import from existing project modules based on API surface
from config import get_config, get_paths
from ingest.graph_serializer import calculate_checksum as calculate_graph_checksum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Type alias for the composite object
ThermalSample = Dict[str, Any]

def calculate_file_checksum(file_path: Path) -> str:
    """Calculate SHA-256 checksum for a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def create_thermal_sample(
    sample_id: str,
    graph_data: Dict[str, Any],
    conductivity_value: Optional[float],
    metadata: Dict[str, Any]
) -> ThermalSample:
    """
    Assemble a ThermalSample dictionary.

    Args:
        sample_id: Unique identifier for the sample.
        graph_data: The atomic graph structure (nodes, edges, features).
        conductivity_value: The computed thermal conductivity (W/mK) from Green-Kubo.
        metadata: Additional info (convergence status, topological metrics, etc.).

    Returns:
        A dictionary representing the ThermalSample.
    """
    sample = {
        "sample_id": sample_id,
        "graph": graph_data,
        "conductivity": conductivity_value,
        "metadata": metadata,
        "checksum": None  # Will be calculated after serialization
    }
    return sample

def save_thermal_sample(
    sample: ThermalSample,
    output_dir: Path,
    filename: Optional[str] = None
) -> Path:
    """
    Serialize a ThermalSample to disk as a pickle file and record its checksum.

    Args:
        sample: The ThermalSample object (dict).
        output_dir: Directory to save the file.
        filename: Optional custom filename. Defaults to {sample_id}.pkl.

    Returns:
        Path to the saved file.
    """
    sample_id = sample["sample_id"]
    if filename is None:
        filename = f"{sample_id}.pkl"
    
    file_path = output_dir / filename
    output_dir.mkdir(parents=True, exist_ok=True)

    # Serialize to pickle
    with open(file_path, 'wb') as f:
        pickle.dump(sample, f)

    # Calculate checksum of the serialized file
    checksum = calculate_file_checksum(file_path)
    sample["checksum"] = checksum

    # Update the file with the checksum inside the object? 
    # Usually checksums are stored in a manifest, but task says "with checksums".
    # We will update the saved file to include the checksum in the metadata for verification.
    sample["checksum"] = checksum
    with open(file_path, 'wb') as f:
        pickle.dump(sample, f)
    
    logger.info(f"Saved ThermalSample {sample_id} to {file_path} (checksum: {checksum[:16]}...)")
    return file_path

def save_checksum_manifest(
    saved_files: List[Path],
    manifest_path: Path
) -> None:
    """
    Save a JSON manifest of all saved ThermalSample files and their checksums.
    """
    manifest = {
        "files": []
    }
    for f_path in saved_files:
        manifest["files"].append({
            "path": str(f_path),
            "checksum": calculate_file_checksum(f_path)
        })
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Saved checksum manifest to {manifest_path}")

def process_thermal_samples(
    samples_data: List[Dict[str, Any]],
    output_dir: Optional[Path] = None
) -> List[Path]:
    """
    Process a list of raw sample data into ThermalSample objects and save them.

    Args:
        samples_data: List of dicts containing 'sample_id', 'graph', 'conductivity', 'metadata'.
        output_dir: Target directory. Defaults to config paths.

    Returns:
        List of paths to saved files.
    """
    if output_dir is None:
        config = get_config()
        paths = get_paths()
        output_dir = paths["conductivities_output"]
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    saved_paths = []
    for data in samples_data:
        sample_id = data.get("sample_id")
        if not sample_id:
            logger.warning("Skipping sample with missing ID")
            continue

        sample = create_thermal_sample(
            sample_id=sample_id,
            graph_data=data.get("graph", {}),
            conductivity_value=data.get("conductivity"),
            metadata=data.get("metadata", {})
        )
        
        file_path = save_thermal_sample(sample, output_dir)
        saved_paths.append(file_path)

    # Save manifest
    manifest_path = output_dir / "conductivity_samples_manifest.json"
    save_checksum_manifest(saved_paths, manifest_path)

    return saved_paths

def main():
    """
    Entry point for T025.
    Expects pre-aggregated data or a way to load it. 
    For this task, we assume the pipeline has collected the data in memory 
    or we are demonstrating the saving logic with a constructed example 
    if no external data loader is currently active.
    
    However, to satisfy 'Real data only', this function should ideally 
    be called by an orchestrator that has already fetched the Green-Kubo 
    results and graph data. Here we implement the logic to save whatever 
    is passed or loaded from a staging area if it exists.
    """
    config = get_config()
    paths = get_paths()
    
    # Check for a staging file where intermediate results might be dumped by previous steps
    # In a real pipeline, this would be called after T022 and T023
    staging_file = paths.get("staging_thermal_data")
    samples_data = []

    if staging_file and Path(staging_file).exists():
        logger.info(f"Loading staging data from {staging_file}")
        with open(staging_file, 'rb') as f:
            samples_data = pickle.load(f)
    else:
        # If no staging data, we cannot proceed with real data saving.
        # In a real run, this would be an error or skipped.
        # For the purpose of this task implementation, we log a warning.
        logger.warning("No staging data found at expected path. T025 implementation ready but no data to save.")
        return

    if not samples_data:
        logger.warning("Staging data is empty.")
        return

    saved_files = process_thermal_samples(samples_data, paths["conductivities_output"])
    logger.info(f"Successfully saved {len(saved_files)} ThermalSample objects.")

if __name__ == "__main__":
    main()

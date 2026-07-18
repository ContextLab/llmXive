"""
Data pipeline orchestration script for 2D material elastic moduli prediction.

This script orchestrates the full data ingestion pipeline:
1. Download raw CIF files and elastic tensors from the canonical source.
2. Parse CIF files into MaterialGraph objects.
3. Filter for valid 2D materials with complete elastic tensors.
4. Save the processed graphs to a Parquet file.
5. Generate and record a SHA256 checksum in the project state file.

WARNING: This model is a surrogate interpolating pre-computed DFT results.
It does NOT solve the Schrödinger equation or perform first-principles calculations.
"""

import os
import sys
import argparse
import logging
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml

import pandas as pd
import numpy as np

# Project imports
from utils.config import Config
from utils.logger import get_logger
from ingest.download import UnifiedDatasetLoader
from ingest.parse_cif import parse_cif_directory
from ingest.filter import filter_graphs, save_filter_stats
from data_models.material_graph import MaterialGraph

# Configure logging
logger = get_logger(__name__)


def serialize_graph(graph: MaterialGraph) -> Dict[str, Any]:
    """
    Serialize a MaterialGraph object to a dictionary for Parquet storage.

    Args:
        graph: The MaterialGraph object to serialize.

    Returns:
        A dictionary representation of the graph.
    """
    return {
        "material_id": graph.material_id,
        "node_features": graph.node_features.tolist() if graph.node_features is not None else None,
        "edge_features": graph.edge_features.tolist() if graph.edge_features is not None else None,
        "edge_index": graph.edge_index.tolist() if graph.edge_index is not None else None,
        "target_moduli": graph.target_moduli.tolist() if graph.target_moduli is not None else None,
        "family_id": graph.family_id,
        "space_group": graph.space_group,
        "composition": graph.composition,
        "num_atoms": graph.num_atoms
    }


def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hex digest of the SHA256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def update_state_checksum(state_path: Path, artifact_key: str, checksum: str) -> None:
    """
    Update the project state YAML file with a new artifact checksum.

    Args:
        state_path: Path to the state YAML file.
        artifact_key: The key path in the YAML (e.g., "artifact_hashes.data_processed.graphs_v1_parquet").
        checksum: The checksum string (e.g., "sha256:abc123...").
    """
    if not state_path.exists():
        logger.error(f"State file not found: {state_path}")
        raise FileNotFoundError(f"State file not found: {state_path}")

    with open(state_path, "r") as f:
        state_data = yaml.safe_load(f) or {}

    # Ensure nested structure exists
    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}

    # Split key path and navigate/create nested dict
    keys = artifact_key.split(".")
    current = state_data["artifact_hashes"]
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = checksum

    with open(state_path, "w") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Updated state checksum for {artifact_key}: {checksum}")


def run_pipeline(
    config: Config,
    download_source: str = "materials_project",
    force_download: bool = False
) -> Dict[str, Any]:
    """
    Run the full data ingestion pipeline.

    Args:
        config: The configuration object.
        download_source: The canonical data source to use.
        force_download: Whether to force re-download of data.

    Returns:
        A dictionary containing pipeline statistics and output paths.
    """
    logger.info("Starting data ingestion pipeline...")
    
    # Ensure output directories exist
    config.data_processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Download
    logger.info(f"Step 1: Downloading data from {download_source}...")
    loader = UnifiedDatasetLoader(
        source=download_source,
        data_dir=config.data_raw_dir,
        config=config
    )
    manifest = loader.load(force=force_download)
    
    if not manifest.files:
        logger.warning("No files downloaded. Pipeline cannot proceed.")
        return {"status": "failed", "reason": "No files downloaded"}
    
    logger.info(f"Downloaded {len(manifest.files)} files.")
    
    # Step 2: Parse CIFs
    logger.info("Step 2: Parsing CIF files...")
    graphs = parse_cif_directory(
        cif_dir=config.data_raw_dir,
        manifest=manifest
    )
    logger.info(f"Parsed {len(graphs)} graphs.")
    
    if not graphs:
        logger.warning("No graphs parsed. Pipeline cannot proceed.")
        return {"status": "failed", "reason": "No graphs parsed"}
    
    # Step 3: Filter
    logger.info("Step 3: Filtering for valid 2D materials...")
    filtered_graphs, stats = filter_graphs(graphs)
    save_filter_stats(stats, config.data_processed_dir / "filter_stats.json")
    logger.info(f"Filtered: {stats['total']} -> {stats['kept']} valid graphs.")
    
    if not filtered_graphs:
        logger.warning("No graphs passed filtering. Pipeline cannot proceed.")
        return {"status": "failed", "reason": "No graphs passed filtering"}
    
    # Step 4: Serialize and Save
    logger.info("Step 4: Serializing and saving to Parquet...")
    serialized_data = [serialize_graph(g) for g in filtered_graphs]
    
    output_path = config.data_processed_dir / "graphs_v1.parquet"
    df = pd.DataFrame(serialized_data)
    
    # Ensure schema requirements are met
    required_cols = ["node_features", "edge_features", "target_moduli", "family_id"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Schema validation failed. Missing columns: {missing_cols}")
    
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved {len(df)} graphs to {output_path}")
    
    # Step 5: Checksum and State Update
    logger.info("Step 5: Generating checksum and updating state...")
    checksum = compute_sha256(output_path)
    state_path = config.project_root / "state" / "projects" / "PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml"
    
    # Normalize checksum format for state file
    state_checksum = f"sha256:{checksum}"
    update_state_checksum(state_path, "artifact_hashes.data_processed.graphs_v1_parquet", state_checksum)
    
    # Return summary
    return {
        "status": "success",
        "downloaded_count": len(manifest.files),
        "parsed_count": len(graphs),
        "filtered_count": len(filtered_graphs),
        "output_path": str(output_path),
        "checksum": state_checksum,
        "filter_stats": stats
    }


def main():
    """Main entry point for the pipeline script."""
    parser = argparse.ArgumentParser(description="Run the 2D material data ingestion pipeline.")
    parser.add_argument(
        "--source",
        type=str,
        default="materials_project",
        choices=["materials_project", "aflow"],
        help="Canonical data source to use."
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Force re-download of data even if it exists."
    )
    parser.add_argument(
        "--config-path",
        type=str,
        default="code/utils/config.yaml",
        help="Path to the configuration file."
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = Config.load(args.config_path)
    
    try:
        result = run_pipeline(
            config=config,
            download_source=args.source,
            force_download=args.force_download
        )
        
        if result["status"] == "success":
            logger.info("Pipeline completed successfully.")
            logger.info(f"Output: {result['output_path']}")
            logger.info(f"Checksum: {result['checksum']}")
            logger.info(f"Filter stats: {json.dumps(result['filter_stats'], indent=2)}")
        else:
            logger.error(f"Pipeline failed: {result.get('reason', 'Unknown error')}")
            sys.exit(1)
            
    except Exception as e:
        logger.exception(f"Pipeline failed with exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
import os
import sys
import logging
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import networkx as nx

# Add project root to path to resolve imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.lib.config import get_processed_data_path, get_project_state_path, ensure_directories
from src.services.ingest import fetch_and_build_subgraph, save_graph_to_parquet

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state_file(file_hash: str, artifact_name: str):
    """Update the project state YAML file with the new artifact hash."""
    state_path = get_project_state_path()
    ensure_directories()
    
    # Ensure the directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)

    # Read existing state if it exists
    state_data = {}
    if state_path.exists():
        try:
            import yaml
            with open(state_path, 'r', encoding='utf-8') as f:
                state_data = yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Could not read existing state file: {e}. Starting fresh.")
            state_data = {}
    
    # Ensure artifact_hashes key exists
    if 'artifact_hashes' not in state_data:
        state_data['artifact_hashes'] = {}
    
    # Update hash
    state_data['artifact_hashes'][artifact_name] = file_hash
    
    # Update timestamp
    state_data['updated_at'] = datetime.now(timezone.utc).isoformat()

    # Write back to file
    try:
        import yaml
        with open(state_path, 'w', encoding='utf-8') as f:
            yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Updated state file at {state_path} with hash for {artifact_name}")
    except Exception as e:
        logger.error(f"Failed to write state file: {e}")
        raise

def main():
    """
    Main entry point for saving the processed graph with clusters and coefficients.
    This script:
    1. Fetches and builds the subgraph (using default or configured sample size).
    2. Saves the graph to `data/processed/subgraph_with_clusters.parquet`.
    3. Computes the SHA256 hash of the output file.
    4. Updates `state/projects/PROJ-854-llmxive-follow-up-extending-sciatlas-a-l.yaml` with the hash and timestamp.
    """
    logger.info("Starting graph save pipeline for T016...")
    
    # Ensure directories exist
    ensure_directories()
    
    output_path = get_processed_data_path() / "subgraph_with_clusters.parquet"
    logger.info(f"Target output path: {output_path}")

    try:
        # 1. Fetch and build the subgraph
        # Note: T012 is the prerequisite which orchestrates this. 
        # We call the core function directly here to ensure the data exists.
        # Assuming a small sample size for the run-book verification as per tasks.md
        logger.info("Fetching and building subgraph...")
        G = fetch_and_build_subgraph(target_size=100) # Using a small sample for verification
        
        if G is None or G.number_of_nodes() == 0:
            raise RuntimeError("Failed to build a non-empty subgraph.")

        logger.info(f"Subgraph built with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")

        # 2. Save the graph to Parquet
        logger.info(f"Saving graph to {output_path}...")
        save_graph_to_parquet(G, output_path)
        
        if not output_path.exists():
            raise FileNotFoundError(f"Output file {output_path} was not created.")

        logger.info(f"Graph saved successfully to {output_path}")

        # 3. Compute SHA256 hash
        logger.info("Computing SHA256 hash...")
        file_hash = compute_file_hash(output_path)
        logger.info(f"SHA256 Hash: {file_hash}")

        # 4. Update state file
        artifact_name = "subgraph_with_clusters.parquet"
        logger.info(f"Updating state file for {artifact_name}...")
        update_state_file(file_hash, artifact_name)

        logger.info("T016 Graph save pipeline completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())

"""
Data pipeline orchestration script for 2D material elastic moduli prediction.
Downloads, parses, filters, and saves material graphs to a Parquet file.
Includes volume constraint verification (T013e).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml

# Local imports
from ingest.download import UnifiedDatasetLoader
from ingest.filter import filter_graphs, is_2d_material, is_valid_6_component_tensor
from ingest.parse_cif import parse_cif_directory
from ingest.validator import enforce_single_source
from ingest.volume_checker import count_unique_entries, verify_volume_constraint
from utils.config import get_config
from utils.logger import get_logger, log_operation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return f"sha256:{sha256_hash.hexdigest()}"

def update_state_checksum(state_path: Path, artifact_name: str, checksum: str) -> None:
    """Update the project state file with the artifact checksum."""
    if not state_path.exists():
        state_data = {"artifact_hashes": {}}
    else:
        with open(state_path, 'r') as f:
            state_data = yaml.safe_load(f) or {"artifact_hashes": {}}

    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}

    # Navigate/create nested keys: data_processed -> graphs_v1_parquet
    if "data_processed" not in state_data["artifact_hashes"]:
        state_data["artifact_hashes"]["data_processed"] = {}

    state_data["artifact_hashes"]["data_processed"][artifact_name] = checksum

    with open(state_path, 'w') as f:
        yaml.safe_dump(state_data, f, default_flow_style=False)
        f.write("\n")

def serialize_graph(graph_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a MaterialGraph-like dict to a serializable format for Parquet."""
    # Ensure numpy arrays are converted to lists for JSON/Parquet serialization
    serialized = {}
    for key, value in graph_data.items():
        if hasattr(value, 'tolist'):
            serialized[key] = value.tolist()
        elif isinstance(value, (list, dict, str, int, float, bool, type(None))):
            serialized[key] = value
        else:
            # Fallback for other types
            try:
                serialized[key] = json.dumps(value)
            except (TypeError, ValueError):
                serialized[key] = str(value)
    return serialized

def run_pipeline(
    output_path: Path,
    state_path: Path,
    data_source: str = "materials_project"
) -> None:
    """
    Run the full data pipeline: download -> parse -> filter -> save.
    Includes T013e volume constraint check.
    """
    logger.info(f"Starting pipeline for data source: {data_source}")

    # Enforce single source constraint
    enforce_single_source(data_source)

    # Step 1: Download
    logger.info("Step 1: Downloading data...")
    loader = UnifiedDatasetLoader(source=data_source)
    download_manifest = loader.fetch_data()
    raw_data_path = Path(download_manifest["raw_dir"])

    if not raw_data_path.exists():
        raise FileNotFoundError(f"Downloaded data path does not exist: {raw_data_path}")

    # Step 2: Parse CIFs
    logger.info("Step 2: Parsing CIF files...")
    graphs = parse_cif_directory(raw_data_path)
    logger.info(f"Parsed {len(graphs)} materials.")

    if not graphs:
        logger.warning("No materials parsed. Pipeline may fail volume check.")

    # Step 3: Filter
    logger.info("Step 3: Filtering for 2D materials and valid tensors...")
    filtered_graphs, stats = filter_graphs(graphs)
    logger.info(f"Filtered to {len(filtered_graphs)} valid 2D materials.")

    # Log exclusion stats
    if stats and "exclusion_log" in stats:
        exclusion_log_path = output_path.parent / "exclusion_log.json"
        with open(exclusion_log_path, 'w') as f:
            json.dump(stats["exclusion_log"], f, indent=2)
        logger.info(f"Exclusion log saved to {exclusion_log_path}")

    if not filtered_graphs:
        logger.error("Pipeline failed: No valid materials after filtering.")
        # Write empty stats if needed, but fail early
        return

    # Step 4: Serialize and save to Parquet
    logger.info("Step 4: Saving to Parquet...")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    serialized_data = [serialize_graph(g) for g in filtered_graphs]
    df = pd.DataFrame(serialized_data)

    # Ensure columns are present even if empty
    required_cols = ["node_features", "edge_features", "target_moduli", "family_id"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = [None] * len(df)

    df.to_parquet(output_path, index=False)
    logger.info(f"Saved {len(df)} entries to {output_path}")

    # Step 5: Compute checksum and update state
    checksum = compute_sha256(output_path)
    update_state_checksum(state_path, "graphs_v1_parquet", checksum)
    logger.info(f"Checksum {checksum} recorded in state file.")

    # Step 6: T013e - Verify Volume Constraint
    logger.info("Step 5: Verifying volume constraint (T013e)...")
    count = count_unique_entries(output_path)
    threshold = 1000

    if count < threshold:
        error_msg = f"SC-001 Violation: Pipeline failed to ingest >1,000 entries. Current count: {count}."
        logger.critical(error_msg)
        # Exit with code 1 as required
        sys.exit(1)
    
    logger.info(f"Volume constraint satisfied: {count} entries >= {threshold}.")

def main():
    parser = argparse.ArgumentParser(description="Run 2D material data ingestion pipeline")
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/graphs_v1.parquet",
        help="Output path for the Parquet file"
    )
    parser.add_argument(
        "--state",
        type=str,
        default="state/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml",
        help="Path to the project state YAML file"
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Data source (e.g., materials_project, aflow). Defaults to env var."
    )
    
    args = parser.parse_args()

    # Determine data source
    data_source = args.source or os.getenv('DATA_SOURCE', 'materials_project')

    output_path = Path(args.output)
    state_path = Path(args.state)

    # Ensure state directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        run_pipeline(output_path, state_path, data_source)
    except SystemExit as e:
        # Re-raise SystemExit (e.g., from volume check)
        raise
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
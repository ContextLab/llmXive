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

# Import from sibling modules based on API surface
from ingest.download import UnifiedDatasetLoader
from ingest.filter import filter_graphs, is_2d_material, is_valid_6_component_tensor
from ingest.parse_cif import parse_cif_directory
from ingest.validator import enforce_single_source, persist_source
from utils.config import get_config
from utils.logger import get_logger, log_operation
from utils.memory_utils import verify_data_volume

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("pipeline")

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return f"sha256:{sha256_hash.hexdigest()}"

def update_state_checksum(
    state_path: Path,
    artifact_key: str,
    checksum: str,
    algorithm: str = "sha256"
) -> None:
    """Update the project state YAML with the artifact checksum."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    if state_path.exists():
        with open(state_path, "r") as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {"artifact_hashes": {}}

    # Ensure nested structure exists
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}
    
    # Navigate to the nested key (e.g., data_processed.graphs_v1_parquet)
    keys = artifact_key.split(".")
    current = state["artifact_hashes"]
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    # Set the checksum
    current[keys[-1]] = f"{algorithm}:{checksum}"

    with open(state_path, "w") as f:
        yaml.safe_dump(state, f, default_flow_style=False)

def serialize_graph(graph_data: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize a graph object for parquet storage."""
    # Convert numpy arrays to lists for JSON/Parquet compatibility
    serialized = {}
    for key, value in graph_data.items():
        if hasattr(value, "tolist"):
            serialized[key] = value.tolist()
        elif isinstance(value, (list, dict, str, int, float, bool, type(None))):
            serialized[key] = value
        else:
            serialized[key] = str(value)
    return serialized

def run_pipeline(
    input_dir: Path,
    output_dir: Path,
    source: str = "materials_project"
) -> Path:
    """
    Run the full ingestion pipeline:
    1. Download data (or load from raw if already present)
    2. Parse CIFs
    3. Filter for 2D materials with valid tensors
    4. Save to parquet
    5. Verify volume constraint
    6. Update state checksum
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = input_dir / "raw"
    processed_dir = input_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Enforce single source constraint
    enforce_single_source(source)
    persist_source(source)

    # Step 1: Download/Load Data
    # For this pipeline, we assume raw data is in input_dir/raw or we download
    # Since T013a handles download, we check if raw exists or trigger download
    if not raw_dir.exists() or not any(raw_dir.iterdir()):
        logger.info("Raw data not found. Triggering download...")
        loader = UnifiedDatasetLoader(source=source)
        loader.fetch_data(output_dir=raw_dir)
    else:
        logger.info(f"Loading existing raw data from {raw_dir}")

    # Step 2: Parse CIFs
    logger.info("Parsing CIF files...")
    # Assuming CIFs are in raw_dir
    graphs = parse_cif_directory(raw_dir)
    logger.info(f"Parsed {len(graphs)} graphs.")

    # Step 3: Filter for 2D materials and valid tensors
    logger.info("Filtering for 2D materials and valid tensors...")
    filtered_graphs = []
    exclusion_log = []

    for i, graph in enumerate(graphs):
        is_2d = is_2d_material(graph)
        is_valid = is_valid_6_component_tensor(graph)
        
        if is_2d and is_valid:
            filtered_graphs.append(graph)
        else:
            reason = []
            if not is_2d:
                reason.append("Not 2D")
            if not is_valid:
                reason.append("Invalid tensor")
            exclusion_log.append({
                "index": i,
                "reason": ", ".join(reason)
            })

    logger.info(f"Filtered {len(filtered_graphs)} valid 2D materials.")
    logger.info(f"Excluded {len(exclusion_log)} entries.")

    # Save exclusion log for bias check (T012)
    exclusion_log_path = processed_dir / "exclusion_log.json"
    with open(exclusion_log_path, "w") as f:
        json.dump(exclusion_log, f, indent=2)

    # Step 4: Save to Parquet
    output_file = processed_dir / "graphs_v1.parquet"
    logger.info(f"Saving {len(filtered_graphs)} graphs to {output_file}...")

    # Convert to DataFrame
    data_rows = []
    for g in filtered_graphs:
        data_rows.append(serialize_graph(g))
    
    df = pd.DataFrame(data_rows)
    df.to_parquet(output_file, index=False)
    logger.info(f"Saved {len(df)} rows to {output_file}")

    # Step 5: Verify Volume Constraint (T013e)
    count = len(df)
    threshold = 1000
    if count < threshold:
        error_msg = f"SC-001 Violation: Pipeline failed to ingest >{threshold} entries. Current count: {count}."
        logger.critical(error_msg)
        raise SystemExit(1)
    
    logger.info(f"Volume constraint satisfied: {count} entries >= {threshold}")

    # Step 6: Update State Checksum
    state_path = Path("state/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml")
    if state_path.exists():
        checksum = compute_sha256(output_file)
        update_state_checksum(state_path, "data_processed.graphs_v1_parquet", checksum)
        logger.info(f"Updated state checksum for graphs_v1.parquet: {checksum}")
    else:
        logger.warning(f"State file not found at {state_path}. Skipping checksum update.")

    return output_file

def main():
    parser = argparse.ArgumentParser(description="Run the 2D material ingestion pipeline.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data"),
        help="Base directory for input data (contains 'raw' and 'processed' subdirs)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed"),
        help="Output directory for processed data"
    )
    parser.add_argument(
        "--source",
        type=str,
        default=os.getenv("DATA_SOURCE", "materials_project"),
        help="Data source to use (materials_project or aflow)"
    )

    args = parser.parse_args()

    try:
        output_file = run_pipeline(args.input_dir, args.output_dir, args.source)
        logger.info(f"Pipeline completed successfully. Output: {output_file}")
    except SystemExit as e:
        raise
    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
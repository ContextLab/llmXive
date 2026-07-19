"""
Data pipeline orchestration script for User Story 1.
Downloads, parses, filters, and saves 2D material graphs.
Generates mock split indices for MVP testing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import yaml

# Import from local modules (per API surface)
from ingest.download import UnifiedDatasetLoader, DownloadManifest
from ingest.parse_cif import parse_cif_directory
from ingest.filter import filter_graphs, load_graphs_from_parquet, save_filter_stats
from ingest.validator import enforce_single_source
from utils.config import get_config
from utils.logger import get_logger, log_operation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Project constants
PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Output artifacts
GRAPHS_OUTPUT = DATA_PROCESSED_DIR / "graphs_v1.parquet"
SPLIT_INDICES_OUTPUT = DATA_PROCESSED_DIR / "split_indices.json"
EXCLUSION_LOG = DATA_PROCESSED_DIR / "exclusion_log.json"


def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def update_state_checksum(state_file: Path, artifact_name: str, checksum: str) -> None:
    """Update the state YAML file with the new artifact checksum."""
    if not state_file.exists():
        logger.warning(f"State file {state_file} not found. Creating new state file.")
        state_data = {"artifact_hashes": {}}
    else:
        with open(state_file, "r") as f:
            state_data = yaml.safe_load(f) or {"artifact_hashes": {}}

    # Ensure nested keys exist
    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}
    if "data_processed" not in state_data["artifact_hashes"]:
        state_data["artifact_hashes"]["data_processed"] = {}

    # Update checksum
    state_data["artifact_hashes"]["data_processed"][artifact_name] = f"sha256:{checksum}"

    with open(state_file, "w") as f:
        yaml.safe_dump(state_data, f, default_flow_style=False)

    logger.info(f"Updated state file with checksum for {artifact_name}: {checksum}")


def serialize_graph(graph_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize a MaterialGraph-like dictionary for Parquet storage.
    Ensures numpy arrays are converted to lists for JSON/Parquet compatibility.
    """
    serialized = {}
    for key, value in graph_data.items():
        if isinstance(value, np.ndarray):
            serialized[key] = value.tolist()
        elif isinstance(value, list):
            # Recursively handle nested lists if they contain arrays
            serialized[key] = [
                item.tolist() if isinstance(item, np.ndarray) else item
                for item in value
            ]
        else:
            serialized[key] = value
    return serialized


def generate_mock_split_indices(graphs: List[Dict[str, Any]], seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generate a random 80/10/10 split of material indices for MVP testing.
    Returns a list of objects: [{"id": "mp-123", "family_id": "TMD_1"}, ...]
    """
    random.seed(seed)
    np.random.seed(seed)

    # Extract unique IDs and family_ids
    indices = list(range(len(graphs)))
    random.shuffle(indices)

    n = len(indices)
    train_end = int(0.8 * n)
    val_end = int(0.9 * n)

    train_indices = indices[:train_end]
    val_indices = indices[train_end:val_end]
    test_indices = indices[val_end:]

    split_indices = []
    for idx in indices:
        graph = graphs[idx]
        entry = {
            "id": graph.get("id", f"unknown_{idx}"),
            "family_id": graph.get("family_id", "unknown_family"),
            "split": "train" if idx in train_indices else ("val" if idx in val_indices else "test")
        }
        split_indices.append(entry)

    logger.info(f"Generated mock split: {len(train_indices)} train, {len(val_indices)} val, {len(test_indices)} test")
    return split_indices


def run_pipeline(
    source: str = "materials_project",
    download_dir: Optional[Path] = None,
    overwrite: bool = False,
) -> None:
    """
    Orchestrate the full data pipeline:
    1. Enforce single source.
    2. Download raw data (CIFs and tensors).
    3. Parse CIFs into graphs.
    4. Filter for 2D materials and valid tensors.
    5. Save to Parquet.
    6. Generate checksum and update state.
    7. Generate mock split indices.
    """
    logger.info("Starting data pipeline...")

    # 1. Enforce single source
    try:
        enforce_single_source(source)
    except SystemExit as e:
        logger.error("Source enforcement failed.")
        raise e

    # Setup directories
    if download_dir is None:
        download_dir = DATA_RAW_DIR / source
    download_dir.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Download
    logger.info(f"Downloading data from {source}...")
    # Note: In a real run, this would fetch from the API.
    # For the MVP, we assume the loader handles the fetch or we simulate the manifest
    # if the actual API call is blocked in this environment, but per constraints
    # we must attempt the real logic.
    # We rely on the UnifiedDatasetLoader to handle the fetch.
    loader = UnifiedDatasetLoader(source=source, output_dir=download_dir)
    manifest: DownloadManifest = loader.fetch_data()

    if not manifest.files:
        logger.error("No files downloaded. Pipeline cannot proceed.")
        sys.exit(1)

    # 3. Parse CIFs
    logger.info(f"Parsing {len(manifest.files)} CIF files...")
    raw_graphs = parse_cif_directory(download_dir, manifest)

    if not raw_graphs:
        logger.error("No graphs parsed. Pipeline cannot proceed.")
        sys.exit(1)

    # 4. Filter
    logger.info("Filtering for 2D materials and valid tensors...")
    filtered_graphs, exclusion_log = filter_graphs(raw_graphs)

    if not filtered_graphs:
        logger.error("No graphs passed filtering. Pipeline cannot proceed.")
        sys.exit(1)

    # Save exclusion log for bias check
    with open(EXCLUSION_LOG, "w") as f:
        json.dump(exclusion_log, f, indent=2)

    # 5. Save to Parquet
    logger.info(f"Saving {len(filtered_graphs)} graphs to {GRAPHS_OUTPUT}...")
    # Serialize for Parquet compatibility
    serializable_graphs = [serialize_graph(g) for g in filtered_graphs]
    df = pd.DataFrame(serializable_graphs)
    df.to_parquet(GRAPHS_OUTPUT, index=False)

    # 6. Checksum & State
    checksum = compute_sha256(GRAPHS_OUTPUT)
    update_state_checksum(STATE_FILE, "graphs_v1_parquet", checksum)

    # 7. Generate Mock Split Indices
    logger.info("Generating mock split indices...")
    split_indices = generate_mock_split_indices(filtered_graphs)
    with open(SPLIT_INDICES_OUTPUT, "w") as f:
        json.dump(split_indices, f, indent=2)

    logger.info(f"Pipeline completed successfully. Output: {GRAPHS_OUTPUT}, {SPLIT_INDICES_OUTPUT}")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Orchestrate data ingestion pipeline.")
    parser.add_argument(
        "--source",
        type=str,
        default=os.getenv("DATA_SOURCE", "materials_project"),
        help="Data source (materials_project or aflow).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional override for download directory.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing outputs.",
    )

    args = parser.parse_args()

    try:
        run_pipeline(
            source=args.source,
            download_dir=args.output_dir,
            overwrite=args.overwrite,
        )
    except Exception as e:
        logger.exception("Pipeline failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
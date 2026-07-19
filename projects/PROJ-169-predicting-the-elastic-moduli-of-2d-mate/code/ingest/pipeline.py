import os
import sys
import argparse
import logging
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import yaml

from ingest.download import UnifiedDatasetLoader
from ingest.parse_cif import parse_cif_directory
from ingest.filter import filter_graphs
from ingest.bias_check import analyze_exclusion_bias, write_bias_report
from utils.config import get_config, set_global_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state_checksum(state_path: Path, artifact_name: str, checksum: str) -> None:
    """Update the project state YAML with the new checksum."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    if state_path.exists():
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {"artifact_hashes": {}}

    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}
    
    # Navigate to data_processed
    if "data_processed" not in state["artifact_hashes"]:
        state["artifact_hashes"]["data_processed"] = {}
    
    # Update the specific artifact
    # artifact_name is like "graphs_v1_parquet"
    state["artifact_hashes"]["data_processed"][artifact_name] = f"sha256:{checksum}"
    
    # Update timestamp
    state["updated_at"] = pd.Timestamp.now().isoformat()

    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)
    logger.info(f"Updated state checksum for {artifact_name}")

def serialize_graph(graph_obj: Any) -> Dict[str, Any]:
    """Convert a MaterialGraph object to a serializable dictionary."""
    # Assuming MaterialGraph has node_features, edge_features, target_moduli, family_id
    # This is a simplified serialization for the purpose of the pipeline
    return {
        "material_id": graph_obj.material_id,
        "node_features": graph_obj.node_features.tolist() if hasattr(graph_obj.node_features, 'tolist') else graph_obj.node_features,
        "edge_features": graph_obj.edge_features.tolist() if hasattr(graph_obj.edge_features, 'tolist') else graph_obj.edge_features,
        "target_moduli": graph_obj.target_moduli.tolist() if hasattr(graph_obj.target_moduli, 'tolist') else graph_obj.target_moduli,
        "family_id": graph_obj.family_id
    }

def run_pipeline(
    source: str,
    output_dir: Path,
    sample_size: Optional[int] = None
) -> None:
    """
    Run the full data ingestion pipeline:
    1. Download data
    2. Parse CIFs
    3. Filter for 2D materials
    4. Save to parquet
    5. Generate checksum
    6. Verify volume constraint
    """
    config = get_config()
    
    # Ensure directories exist
    output_dir.mkdir(parents=True, exist_ok=True)
    config.data_processed.mkdir(parents=True, exist_ok=True)
    config.state_projects.mkdir(parents=True, exist_ok=True)

    # 1. Download
    logger.info(f"Downloading data from {source}...")
    loader = UnifiedDatasetLoader(source=source, output_dir=config.data_raw, sample_size=sample_size)
    manifest = loader.fetch_data()
    
    if not manifest or not manifest.get('files'):
        raise RuntimeError("Download failed: no files retrieved.")

    # 2. Parse CIFs
    logger.info("Parsing CIF files...")
    graphs = []
    exclusion_log = []
    
    # Assuming manifest contains paths to CIFs
    cif_dir = config.data_raw / "cif"
    if not cif_dir.exists():
        # Fallback: if download puts files elsewhere, adjust
        cif_dir = config.data_raw
        
    parsed_graphs = parse_cif_directory(cif_dir)
    graphs.extend(parsed_graphs)

    # 3. Filter
    logger.info("Filtering for 2D materials...")
    filtered_graphs, stats = filter_graphs(graphs)
    
    # Log exclusion reasons
    if stats.get('excluded'):
        exclusion_log = stats['excluded']
        bias_report_path = config.data_processed / "exclusion_log.json"
        write_bias_report(exclusion_log, bias_report_path)
        logger.info(f"Bias check report saved to {bias_report_path}")

    if not filtered_graphs:
        raise RuntimeError("Filtering failed: no valid 2D materials found.")

    # 4. Save to Parquet
    logger.info("Saving processed graphs...")
    parquet_path = config.data_processed / "graphs_v1.parquet"
    
    # Convert to DataFrame
    data = [serialize_graph(g) for g in filtered_graphs]
    df = pd.DataFrame(data)
    
    # Ensure columns are correct
    required_cols = ['material_id', 'node_features', 'edge_features', 'target_moduli', 'family_id']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    df.to_parquet(parquet_path, index=False)
    logger.info(f"Saved {len(df)} graphs to {parquet_path}")

    # 5. Generate Checksum
    checksum = compute_sha256(parquet_path)
    state_path = config.state_projects / "PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml"
    update_state_checksum(state_path, "graphs_v1_parquet", checksum)

    # 6. Volume Constraint Check (T013e)
    count = len(df)
    if count < 1000:
        error_msg = f"SC-001 Violation: Pipeline failed to ingest >1,000 entries. Current count: {count}."
        logger.critical(error_msg)
        # Exit with code 1 as required
        sys.exit(1)
    else:
        logger.info(f"Volume constraint satisfied: {count} entries >= 1000")

    # 7. Save Split Indices (T013d requirement)
    # We need to generate train/val/test splits here or call the splitter.
    # For now, let's assume we generate a simple split or call the splitter module.
    # Since T017 (splitter) is a dependency, we should import and use it if available.
    try:
        from model.splitter import split_by_family, save_split_manifest
        # Load the graphs again or use the dataframe
        # split_by_family expects a list of graphs or a dataframe
        # Let's use the dataframe we just created
        split_manifest = split_by_family(df, test_size=0.2, val_size=0.1)
        split_indices_path = config.data_processed / "split_indices.json"
        save_split_manifest(split_manifest, split_indices_path)
        logger.info(f"Saved split indices to {split_indices_path}")
    except ImportError:
        logger.warning("Splitter module not found. Skipping split generation.")

def main():
    parser = argparse.ArgumentParser(description="Run the data ingestion pipeline")
    parser.add_argument("--source", type=str, default="materials_project", 
                      choices=["materials_project", "aflow", "oqmd"],
                      help="Data source to use")
    parser.add_argument("--output", type=Path, default=None, help="Output directory for raw data")
    parser.add_argument("--sample", type=int, default=None, help="Sample size for testing")
    
    args = parser.parse_args()
    
    # Initialize config
    set_global_config()
    config = get_config()
    
    output_dir = args.output if args.output else config.data_raw
    
    try:
        run_pipeline(source=args.source, output_dir=output_dir, sample_size=args.sample)
    except SystemExit:
        raise
    except Exception as e:
        logger.exception("Pipeline failed")
        sys.exit(1)

if __name__ == "__main__":
    main()

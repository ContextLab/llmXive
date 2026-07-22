from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from tqdm import tqdm

# Import from existing API surface
from utils.config import Config, get_config
from ingest.download import UnifiedDatasetLoader
from ingest.parse_cif import parse_cif_directory
from ingest.filter import is_2d_material, is_valid_6_component_tensor, load_graphs_from_parquet
from ingest.validator import enforce_single_source
from data_models.material_graph import MaterialGraph

def compute_sha256(filepath: str) -> str:
    """Compute SHA256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def update_state_checksum(filepath: str, state_file: str):
    """Update the checksum of a file in the state file."""
    sha256 = compute_sha256(filepath)
    # Ensure state directory exists
    state_path = Path(state_file)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Handle YAML vs JSON state file (task T001 specifies .yaml but content is JSON map)
    try:
        with open(state_file, "r") as f:
            content = f.read()
            if content.strip().startswith("{"):
                state = json.loads(content)
            else:
                # Simple YAML-like parsing for the specific format from T001
                state = {}
                for line in content.splitlines():
                    if ':' in line and not line.strip().startswith('#'):
                        k, v = line.split(':', 1)
                        if v.strip() == '{}':
                            state[k.strip()] = {}
                        else:
                            state[k.strip()] = v.strip()
    except (json.JSONDecodeError, FileNotFoundError, yaml.YAMLError):
        state = {}
    
    # Update the specific artifact_hashes map
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}
    
    state["artifact_hashes"][filepath] = sha256
    
    with open(state_file, "w") as f:
        # Write as JSON for simplicity and reliability
        json.dump(state, f, indent=4)


def serialize_graph(material_graph: dict, filepath: str):
    """Serialize a MaterialGraph to a file (internal helper)."""
    # This is handled by the parquet writer in the main loop
    pass

def validate_schema(df: pd.DataFrame) -> bool:
    """Verify the generated parquet matches the required schema.
    
    Required columns:
    - node_features: List[List[float32]]
    - edge_features: List[List[float32]]
    - target_moduli: Dict[str, float64]
    - family_id: str
    """
    required_cols = ["node_features", "edge_features", "target_moduli", "family_id"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        logging.error(f"Schema validation failed: Missing columns: {missing}")
        return False
    
    # Type checks (best effort for parquet)
    if len(df) > 0:
        # Check node_features is list-like
        if not isinstance(df.iloc[0]["node_features"], (list, np.ndarray)):
            logging.error("Schema validation failed: node_features is not a list")
            return False
        
        # Check edge_features is list-like
        if not isinstance(df.iloc[0]["edge_features"], (list, np.ndarray)):
            logging.error("Schema validation failed: edge_features is not a list")
            return False
        
        # Check target_moduli is dict-like
        if not isinstance(df.iloc[0]["target_moduli"], (dict, np.object_)):
            logging.error("Schema validation failed: target_moduli is not a dict")
            return False
        
        # Check family_id is string
        if not isinstance(df.iloc[0]["family_id"], str):
            logging.error("Schema validation failed: family_id is not a string")
            return False

    logging.info("Schema validation passed.")
    return True

def run_pipeline(
    source: str = "materials_project",
    output_dir: str = "data/processed",
    state_file: str = "state/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml",
    raw_dir: str = "data/raw",
    process_dir: str = "data/processed",
    chunk_size: int = 50
):
    """Run the entire data pipeline: download -> parse -> filter -> save.
    
    Requirements:
    - Output schema MUST include: node_features, edge_features, target_moduli, family_id
    - Implement error handling for missing tensors
    - Enforce single source (T009a)
    - Write to data/processed/graphs_v1.parquet
    """
    # 1. Enforce single source
    try:
        enforce_single_source(source)
    except SystemExit:
        logging.error("Source enforcement failed. Exiting.")
        sys.exit(1)

    # 2. Download data
    logging.info(f"Starting download from {source}...")
    loader = UnifiedDatasetLoader(source=source)
    manifest = loader.fetch_data(output_dir=raw_dir)
    
    if not manifest or not manifest.get("cif_paths"):
        logging.error("Download failed: No CIF files retrieved.")
        sys.exit(1)

    # 3. Parse CIFs
    logging.info("Parsing CIF files...")
    # parse_cif_directory expects a directory path, returns list of dicts
    # We need to handle the fact that loader might have downloaded to specific subdirs
    cif_dirs = [os.path.dirname(p) for p in manifest["cif_paths"]]
    # Deduplicate
    cif_dirs = list(set(cif_dirs))
    
    all_graphs = []
    total_files = len(manifest["cif_paths"])
    
    # Use the parse_cif_directory function from the API
    # Note: The API surface says `parse_cif_directory` exists in `ingest.parse_cif`
    # We assume it returns a list of MaterialGraph-like dicts
    try:
        # If the loader downloaded files to a flat structure or specific dirs
        # We iterate over the manifest paths directly if directory parsing is tricky
        # But the task requires using the parse_cif module
        
        # Strategy: Call parse_cif_directory on the raw_dir if all CIFs are there
        # Or iterate if they are scattered
        # For robustness, we assume `raw_dir` contains the CIFs
        parsed_data = parse_cif_directory(raw_dir)
        all_graphs.extend(parsed_data)
    except Exception as e:
        logging.error(f"Error parsing CIFs: {e}")
        # Fallback: try to parse individual files if directory parsing fails
        logging.warning("Falling back to individual file parsing...")
        for cif_path in manifest["cif_paths"]:
            try:
                # Assuming parse_cif_file exists and returns a dict
                from ingest.parse_cif import parse_cif_file
                graph = parse_cif_file(cif_path)
                if graph:
                    all_graphs.append(graph)
            except Exception as fe:
                logging.warning(f"Failed to parse {cif_path}: {fe}")

    if not all_graphs:
        logging.error("Parsing failed: No graphs generated.")
        sys.exit(1)

    logging.info(f"Parsed {len(all_graphs)} graphs.")

    # 4. Filter (2D + 6-component tensor)
    logging.info("Filtering for 2D materials and valid tensors...")
    filtered_graphs = []
    excluded_count = 0
    for i, graph in enumerate(tqdm(all_graphs, desc="Filtering")):
        # Check 2D
        if not is_2d_material(graph):
            excluded_count += 1
            continue
        
        # Check tensor validity
        if not is_valid_6_component_tensor(graph):
            excluded_count += 1
            continue
        
        filtered_graphs.append(graph)

    logging.info(f"Filtered: {len(filtered_graphs)} valid, {excluded_count} excluded.")

    if not filtered_graphs:
        logging.error("Filtering failed: No valid graphs remain.")
        sys.exit(1)

    # 5. Serialize to Parquet with required schema
    output_path = os.path.join(output_dir, "graphs_v1.parquet")
    os.makedirs(output_dir, exist_ok=True)
    
    logging.info(f"Writing {len(filtered_graphs)} graphs to {output_path}...")
    
    # Prepare DataFrame
    data_rows = []
    for g in filtered_graphs:
        # Ensure types match schema
        node_feats = [float(x) for x in g.get("node_features", [])]
        edge_feats = [float(x) for x in g.get("edge_features", [])]
        target_mod = g.get("target_moduli", {})
        family_id = g.get("family_id", "unknown")
        
        data_rows.append({
            "node_features": node_feats,
            "edge_features": edge_feats,
            "target_moduli": target_mod,
            "family_id": str(family_id)
        })
    
    df = pd.DataFrame(data_rows)
    
    # Validate schema before writing
    if not validate_schema(df):
        logging.error("Schema validation failed before write. Aborting.")
        sys.exit(1)
    
    # Write to parquet
    df.to_parquet(output_path, index=False)
    logging.info(f"Successfully wrote {output_path}")

    # 6. Update state file
    update_state_checksum(output_path, state_file)

    # 7. Verify volume constraint (T013e requirement - part of pipeline flow)
    # Note: T013e is a separate task, but the pipeline must produce the file
    # that T013e checks. We perform a lightweight check here to ensure we have data.
    entry_count = df['family_id'].nunique()
    config = get_config()
    threshold = getattr(config, 'MIN_ENTRY_THRESHOLD', 1000)
    
    if entry_count <= threshold:
        logging.warning(f"Volume constraint warning: {entry_count} unique entries (threshold: {threshold}).")
        # Do not exit here, as T013e is the gate. But log it.
    else:
        logging.info(f"Volume constraint met: {entry_count} unique entries.")

    return output_path

def main():
    """Main function to run the data pipeline."""
    parser = argparse.ArgumentParser(description="Run the data ingestion pipeline.")
    parser.add_argument("--source", type=str, default="materials_project", help="Data source (materials_project or aflow).")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Output directory for processed data.")
    parser.add_argument("--state-file", type=str, default="state/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml", help="Path to the state file.")
    parser.add_argument("--raw-dir", type=str, default="data/raw", help="Directory for raw downloaded data.")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        run_pipeline(
            source=args.source,
            output_dir=args.output_dir,
            state_file=args.state_file,
            raw_dir=args.raw_dir
        )
    except Exception as e:
        logging.error(f"Pipeline failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
Data pipeline orchestration script for 2D material elastic moduli prediction.
Implements: download -> parse -> filter -> save -> volume verification.
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

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from tqdm import tqdm

# Project imports
from utils.config import get_config
from utils.logger import get_logger, log_operation, log_bias_check
from ingest.download import UnifiedDatasetLoader
from ingest.parse_cif import parse_cif_directory
from ingest.filter import filter_graphs, is_2d_material, is_valid_6_component_tensor
from ingest.bias_check import analyze_exclusion_bias, ExclusionReason
from ingest.validator import enforce_single_source, persist_source, get_active_source

# Setup logging
logger = get_logger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state_checksum(state_file: Path, file_path: Path, key: str) -> None:
    """Update the state file with the checksum of a processed file."""
    if not state_file.exists():
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, 'w') as f:
            json.dump({}, f)
    
    with open(state_file, 'r') as f:
        state = json.load(f)
    
    state[key] = compute_sha256(file_path)
    
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)

def serialize_graph(graph: Any) -> Dict[str, Any]:
    """Convert a MaterialGraph object to a serializable dictionary."""
    # Assuming MaterialGraph has node_features, edge_features, target_moduli, family_id
    return {
        'node_features': graph.node_features.tolist() if hasattr(graph.node_features, 'tolist') else graph.node_features,
        'edge_features': graph.edge_features.tolist() if hasattr(graph.edge_features, 'tolist') else graph.edge_features,
        'edge_index': graph.edge_index.tolist() if hasattr(graph.edge_index, 'tolist') else graph.edge_index,
        'target_moduli': {
            'young': graph.target_moduli['young'],
            'shear': graph.target_moduli['shear'],
            'poisson': graph.target_moduli['poisson']
        },
        'family_id': graph.family_id,
        'material_id': graph.material_id,
        'composition': graph.composition
    }

def count_unique_entries(parquet_path: Path) -> int:
    """Count unique material entries in a Parquet file."""
    if not parquet_path.exists():
        logger.error(f"Parquet file not found: {parquet_path}")
        return 0
    
    df = pq.read_table(parquet_path).to_pandas()
    if 'material_id' not in df.columns:
        logger.error("Parquet file missing 'material_id' column")
        return 0
    
    unique_count = df['material_id'].nunique()
    return unique_count

def verify_volume_constraint(parquet_path: Path, min_threshold: int) -> bool:
    """
    Verify that the dataset meets the minimum entry threshold.
    Returns True if count >= threshold, False otherwise.
    """
    count = count_unique_entries(parquet_path)
    
    if count < min_threshold:
        logger.error(f"Volume constraint FAILED: Found {count} unique entries, but minimum required is {min_threshold}")
        logger.error("Pipeline terminated due to insufficient data volume.")
        return False
    
    logger.info(f"Volume constraint PASSED: Found {count} unique entries (threshold: {min_threshold})")
    return True

def run_pipeline(
    raw_dir: Path,
    processed_dir: Path,
    source: str = 'materials_project',
    min_entries: int = 10
) -> bool:
    """
    Run the full data pipeline: download -> parse -> filter -> save -> verify.
    
    Args:
        raw_dir: Directory to store raw downloaded data
        processed_dir: Directory to store processed Parquet files
        source: Data source ('materials_project' or 'aflow')
        min_entries: Minimum number of unique entries required
    
    Returns:
        True if pipeline completes successfully, False otherwise
    """
    logger.info("Starting data pipeline...")
    
    # Ensure directories exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Enforce single source
    try:
        enforce_single_source(source)
        persist_source(source, raw_dir / '.source_state')
    except SystemExit as e:
        logger.error(f"Source enforcement failed: {e}")
        return False
    
    # 2. Download data
    logger.info(f"Downloading data from {source}...")
    loader = UnifiedDatasetLoader(source=source)
    manifest = loader.fetch_data(raw_dir)
    
    if not manifest or not manifest.get('files'):
        logger.error("Download failed: No files retrieved")
        return False
    
    # 3. Parse CIFs
    logger.info("Parsing CIF files...")
    graphs = []
    exclusion_reasons: List[ExclusionReason] = []
    
    cif_dir = raw_dir / 'cif'
    if not cif_dir.exists():
        logger.error(f"CIF directory not found: {cif_dir}")
        return False
    
    parsed_graphs = parse_cif_directory(cif_dir)
    
    for graph in parsed_graphs:
        # 4. Filter for 2D materials and valid tensors
        if not is_2d_material(graph):
            exclusion_reasons.append(ExclusionReason(
                material_id=graph.material_id,
                reason="Not a 2D material",
                category="dimensionality"
            ))
            continue
        
        if not is_valid_6_component_tensor(graph):
            exclusion_reasons.append(ExclusionReason(
                material_id=graph.material_id,
                reason="Invalid elastic tensor (not 6 components)",
                category="tensor_validity"
            ))
            continue
        
        graphs.append(graph)
    
    # Log exclusion bias
    if exclusion_reasons:
        bias_report = analyze_exclusion_bias(exclusion_reasons)
        bias_log_path = processed_dir / 'exclusion_log.json'
        with open(bias_log_path, 'w') as f:
            json.dump(bias_report.to_dict() if hasattr(bias_report, 'to_dict') else bias_report, f, indent=2)
        log_bias_check(bias_report.summary, bias_report)
        logger.info(f"Exclusion log written to {bias_log_path}")
    
    if not graphs:
        logger.error("No valid graphs found after filtering")
        return False
    
    # 5. Serialize and save to Parquet
    logger.info(f"Saving {len(graphs)} graphs to Parquet...")
    output_path = processed_dir / 'graphs_v1.parquet'
    
    serialized_data = [serialize_graph(g) for g in graphs]
    df = pd.DataFrame(serialized_data)
    
    # Ensure correct dtypes for Parquet
    df['material_id'] = df['material_id'].astype(str)
    df['family_id'] = df['family_id'].astype(str)
    
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved to {output_path}")
    
    # Update state checksum
    state_file = processed_dir.parent / '.pipeline_state.json'
    update_state_checksum(state_file, output_path, 'graphs_v1.parquet')
    
    # 6. Verify volume constraint
    logger.info("Verifying volume constraint...")
    if not verify_volume_constraint(output_path, min_entries):
        return False
    
    logger.info("Pipeline completed successfully!")
    return True

def main() -> None:
    """Main entry point for the pipeline script."""
    parser = argparse.ArgumentParser(description="Run the 2D material data pipeline")
    parser.add_argument(
        '--raw-dir',
        type=str,
        default='data/raw',
        help='Directory for raw downloaded data'
    )
    parser.add_argument(
        '--processed-dir',
        type=str,
        default='data/processed',
        help='Directory for processed output'
    )
    parser.add_argument(
        '--source',
        type=str,
        default=None,
        help='Data source (overrides DATA_SOURCE env var)'
    )
    parser.add_argument(
        '--min-entries',
        type=int,
        default=None,
        help='Minimum number of unique entries required'
    )
    
    args = parser.parse_args()
    
    # Resolve source from args or env
    source = args.source or os.getenv('DATA_SOURCE', 'materials_project')
    
    # Resolve min_entries from args or config
    config = get_config()
    min_entries = args.min_entries or getattr(config, 'MIN_ENTRY_THRESHOLD', 10)
    
    raw_dir = Path(args.raw_dir)
    processed_dir = Path(args.processed_dir)
    
    success = run_pipeline(raw_dir, processed_dir, source, min_entries)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
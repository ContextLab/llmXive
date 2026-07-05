"""
Batch Aggregation Script for Network Topology Energy Transfer Project.

This script combines per-topology-class batches into a single global batch,
generates a manifest file, and verifies the combined total meets the >=100
threshold (FR-001/SC-001).
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.src.utils.reproducibility import ensure_data_directory, generate_run_id
from code.src.utils.io import compute_file_checksum
from code.src.utils.config import load_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MIN_BATCH_SIZE = 100
MANIFEST_FILENAME = "global_batch_manifest.json"
RAW_DATA_DIR = "data/raw"

def load_batch_file(batch_path: Path) -> List[Dict[str, Any]]:
    """Load a single batch JSON file."""
    if not batch_path.exists():
        logger.warning(f"Batch file not found: {batch_path}")
        return []
    
    try:
        with open(batch_path, 'r') as f:
            data = json.load(f)
            # Handle cases where data might be wrapped in a key like 'graphs'
            if isinstance(data, dict) and 'graphs' in data:
                return data['graphs']
            elif isinstance(data, list):
                return data
            else:
                logger.warning(f"Unexpected format in {batch_path}: {type(data)}")
                return []
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON in {batch_path}: {e}")
        return []

def find_batch_files(data_dir: Path) -> List[Path]:
    """Find all batch files in the data directory."""
    if not data_dir.exists():
        logger.warning(f"Data directory does not exist: {data_dir}")
        return []
    
    batch_files = list(data_dir.glob("batch_*.json"))
    logger.info(f"Found {len(batch_files)} batch files in {data_dir}")
    return batch_files

def aggregate_batches(batch_files: List[Path]) -> List[Dict[str, Any]]:
    """Aggregate multiple batch files into a single list of graphs."""
    all_graphs = []
    source_counts = {}

    for batch_file in batch_files:
        graphs = load_batch_file(batch_file)
        source_name = batch_file.stem
        count = len(graphs)
        source_counts[source_name] = count
        all_graphs.extend(graphs)
        logger.info(f"Loaded {count} graphs from {batch_file.name}")

    logger.info(f"Total graphs aggregated: {len(all_graphs)}")
    logger.info(f"Source counts: {source_counts}")
    
    return all_graphs

def generate_manifest(
    graphs: List[Dict[str, Any]],
    batch_files: List[Path],
    output_path: Path
) -> Dict[str, Any]:
    """Generate the global batch manifest."""
    total_count = len(graphs)
    checksum = compute_file_checksum(output_path) if output_path.exists() else "pending"
    
    # Calculate metadata for each graph
    topology_counts = {}
    for graph in graphs:
        topology = graph.get('topology_class', 'unknown')
        topology_counts[topology] = topology_counts.get(topology, 0) + 1

    manifest = {
        "manifest_id": generate_run_id(),
        "created_at": datetime.now().isoformat(),
        "total_graphs": total_count,
        "threshold_met": total_count >= MIN_BATCH_SIZE,
        "threshold_required": MIN_BATCH_SIZE,
        "source_files": [str(f.name) for f in batch_files],
        "topology_distribution": topology_counts,
        "checksum": checksum,
        "validation_status": "passed" if total_count >= MIN_BATCH_SIZE else "failed"
    }

    return manifest

def save_manifest(manifest: Dict[str, Any], output_path: Path) -> None:
    """Save the manifest to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Manifest saved to {output_path}")

def verify_threshold(manifest: Dict[str, Any]) -> bool:
    """Verify the manifest meets the minimum threshold."""
    total = manifest.get("total_graphs", 0)
    passed = total >= MIN_BATCH_SIZE
    
    if passed:
        logger.info(f"✓ Threshold met: {total} >= {MIN_BATCH_SIZE}")
    else:
        logger.error(f"✗ Threshold NOT met: {total} < {MIN_BATCH_SIZE}")
    
    return passed

def main():
    """Main entry point for batch aggregation."""
    parser = argparse.ArgumentParser(description="Aggregate batch files into a global batch")
    parser.add_argument(
        "--data-dir",
        type=str,
        default=RAW_DATA_DIR,
        help="Directory containing batch files (default: data/raw)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output path for manifest (default: data/raw/global_batch_manifest.json)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with error code if threshold is not met"
    )
    
    args = parser.parse_args()
    
    # Setup paths
    data_dir = Path(args.data_dir)
    output_path = Path(args.output) if args.output else data_dir / MANIFEST_FILENAME
    
    logger.info(f"Starting batch aggregation")
    logger.info(f"Data directory: {data_dir}")
    logger.info(f"Output manifest: {output_path}")
    
    # Ensure data directory exists
    ensure_data_directory(data_dir)
    
    # Find and load batch files
    batch_files = find_batch_files(data_dir)
    
    if not batch_files:
        logger.error("No batch files found to aggregate")
        sys.exit(1)
    
    # Aggregate graphs
    all_graphs = aggregate_batches(batch_files)
    
    if not all_graphs:
        logger.error("No graphs found in batch files")
        sys.exit(1)
    
    # Generate and save manifest
    manifest = generate_manifest(all_graphs, batch_files, output_path)
    save_manifest(manifest, output_path)
    
    # Verify threshold
    threshold_met = verify_threshold(manifest)
    
    # Exit with appropriate code
    if args.strict and not threshold_met:
        logger.error("Strict mode: Threshold not met, exiting with error")
        sys.exit(1)
    
    logger.info("Batch aggregation completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())

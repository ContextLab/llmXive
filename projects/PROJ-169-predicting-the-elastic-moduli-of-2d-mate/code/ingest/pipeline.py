"""
Data pipeline orchestration script for User Story 1.

Executes the full data ingestion workflow:
1. Download CIF files and elastic tensors from a unified canonical source.
2. Parse CIFs into MaterialGraph objects.
3. Filter for 2D materials and valid 6-component tensors.
4. Run bias checks on excluded entries.
5. Save the final processed dataset to Parquet format.

Output: data/processed/graphs_v1.parquet
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import Config
from utils.logger import get_logger, configure_log_file
from ingest.download import UnifiedDatasetLoader, DownloadManifest
from ingest.parse_cif import parse_cifs_to_graphs
from ingest.filter import filter_graphs, FilterStats, save_filter_stats
from ingest.bias_check import load_exclusion_log, analyze_exclusion_bias, write_bias_report, main as bias_main
from utils.memory_utils import verify_data_volume, enforce_memory_limit
from data_models.material_graph import MaterialGraph

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import numpy as np
import json

logger = get_logger(__name__)

def serialize_graph(graph: MaterialGraph) -> Dict[str, Any]:
    """Convert a MaterialGraph object to a dictionary suitable for serialization."""
    return {
        "material_id": graph.material_id,
        "formula": graph.formula,
        "nodes": graph.nodes,
        "edges": graph.edges,
        "edge_index": graph.edge_index.tolist() if hasattr(graph.edge_index, 'tolist') else graph.edge_index,
        "node_features": graph.node_features.tolist() if hasattr(graph.node_features, 'tolist') else graph.node_features,
        "target_youngs": float(graph.target_youngs) if graph.target_youngs is not None else None,
        "target_shear": float(graph.target_shear) if graph.target_shear is not None else None,
        "target_poisson": float(graph.target_poisson) if graph.target_poisson is not None else None,
        "elastic_tensor": graph.elastic_tensor.tolist() if graph.elastic_tensor is not None else None,
        "space_group": graph.space_group,
        "layer_thickness": graph.layer_thickness,
        "source": graph.source
    }

def run_pipeline(
    source: str = "materials_project",
    sample_size: Optional[int] = None,
    output_dir: Optional[str] = None,
    force_download: bool = False
) -> str:
    """
    Execute the full data ingestion pipeline.

    Args:
        source: Data source identifier ('materials_project' or 'aflow').
        sample_size: Optional limit on number of materials to process (for testing/memory).
        output_dir: Directory to write output files. Defaults to data/processed/.
        force_download: If True, re-download data even if manifest exists.

    Returns:
        Path to the generated Parquet file.
    """
    config = Config()
    output_path = Path(output_dir) if output_dir else config.data_path / "processed"
    output_path.mkdir(parents=True, exist_ok=True)

    log_file = output_path / "pipeline_run.log"
    configure_log_file(log_file)

    logger.info(f"Starting data pipeline for source: {source}")
    logger.info(f"Output directory: {output_path}")

    # Step 1: Download
    logger.info("Step 1: Downloading data...")
    loader = UnifiedDatasetLoader(source=source, data_dir=config.data_path / "raw")
    manifest = loader.run(force=force_download)
    
    if not manifest or not manifest.cif_files:
        logger.error("No data downloaded. Pipeline aborted.")
        return ""

    logger.info(f"Downloaded {len(manifest.cif_files)} CIF files.")

    # Step 2: Parse
    logger.info("Step 2: Parsing CIFs to graphs...")
    graphs = parse_cifs_to_graphs(
        cif_files=manifest.cif_files,
        elastic_tensors=manifest.elastic_tensors,
        sample_size=sample_size
    )
    logger.info(f"Parsed {len(graphs)} graphs.")

    # Step 3: Filter
    logger.info("Step 3: Filtering for 2D materials and valid tensors...")
    filtered_graphs, stats = filter_graphs(graphs)
    logger.info(f"Filtered to {len(filtered_graphs)} valid 2D materials.")
    
    filter_stats_path = output_path / "filter_stats.json"
    save_filter_stats(stats, filter_stats_path)
    logger.info(f"Filter stats saved to {filter_stats_path}")

    # Step 4: Bias Check
    logger.info("Step 4: Running bias checks on excluded entries...")
    exclusion_log_path = config.data_path / "exclusions" / "exclusion_log.json"
    if exclusion_log_path.exists():
        bias_report = analyze_exclusion_bias(exclusion_log_path)
        report_path = output_path / "bias_report.json"
        write_bias_report(bias_report, report_path)
        logger.info(f"Bias report saved to {report_path}")
    else:
        logger.warning("No exclusion log found. Skipping bias analysis.")

    # Step 5: Memory Verification
    if len(filtered_graphs) > 0:
        logger.info("Step 5: Verifying data volume against memory limits...")
        verify_data_volume(filtered_graphs, max_memory_gb=7.0)

    # Step 6: Save to Parquet
    logger.info("Step 6: Saving to Parquet...")
    parquet_path = output_path / "graphs_v1.parquet"
    
    data = [serialize_graph(g) for g in filtered_graphs]
    df = pd.DataFrame(data)
    
    # Handle numpy arrays in DataFrame for Parquet serialization
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, (list, np.ndarray))).any():
            df[col] = df[col].apply(lambda x: x.tolist() if isinstance(x, np.ndarray) else x)

    df.to_parquet(parquet_path, index=False)
    logger.info(f"Pipeline complete. Data saved to {parquet_path}")

    return str(parquet_path)

def main():
    parser = argparse.ArgumentParser(description="Run the data ingestion pipeline.")
    parser.add_argument(
        "--source", 
        type=str, 
        default="materials_project", 
        choices=["materials_project", "aflow"],
        help="Data source to use."
    )
    parser.add_argument(
        "--sample-size", 
        type=int, 
        default=None, 
        help="Optional limit on number of materials to process."
    )
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default=None, 
        help="Directory to write output files."
    )
    parser.add_argument(
        "--force-download", 
        action="store_true", 
        help="Re-download data even if manifest exists."
    )

    args = parser.parse_args()

    try:
        run_pipeline(
            source=args.source,
            sample_size=args.sample_size,
            output_dir=args.output_dir,
            force_download=args.force_download
        )
    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
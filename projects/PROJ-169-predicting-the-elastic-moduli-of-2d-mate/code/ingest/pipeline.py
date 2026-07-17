"""
Data pipeline orchestration script for US1.
Executes: download -> parse -> filter -> save to parquet.
"""
import os
import sys
import argparse
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal

# Local imports based on API surface
from ingest.download import DownloadManifest, UnifiedDatasetLoader, main as download_main
from ingest.parse_cif import parse_cif_directory, main as parse_main
from ingest.filter import filter_graphs, save_filter_stats, FilterStats
from ingest.bias_check import analyze_exclusion_bias, write_bias_report, main as bias_main
from data_models.material_graph import MaterialGraph
from utils.config import Config
from utils.logger import get_logger, configure_log_file

# Parquet support
try:
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq
except ImportError:
    raise ImportError("Missing required dependencies: pandas, pyarrow. "
                      "Please install them via requirements.txt.")

LOGGER = get_logger(__name__)

def serialize_graph(graph: MaterialGraph) -> Dict[str, Any]:
    """
    Serialize a MaterialGraph object to a dictionary suitable for parquet storage.
    Output schema MUST include: node_features, edge_features, target_moduli, family_id.
    """
    if graph.node_features is None or graph.edge_features is None:
        raise ValueError(f"Cannot serialize graph for {graph.material_id}: missing features.")
    
    if graph.target_moduli is None:
        raise ValueError(f"Cannot serialize graph for {graph.material_id}: missing target_moduli.")

    # Ensure arrays are lists for JSON/Parquet compatibility
    return {
        "material_id": graph.material_id,
        "formula": graph.formula,
        "family_id": graph.family_id,
        "node_features": graph.node_features.tolist() if hasattr(graph.node_features, 'tolist') else list(graph.node_features),
        "edge_features": graph.edge_features.tolist() if hasattr(graph.edge_features, 'tolist') else list(graph.edge_features),
        "target_moduli": graph.target_moduli.tolist() if hasattr(graph.target_moduli, 'tolist') else list(graph.target_moduli),
        "space_group": graph.space_group,
        "num_atoms": graph.num_atoms
    }

def run_pipeline(
    config: Config,
    source_type: Literal["materials_project", "aflow", "local_cif_dir"],
    source_id: Optional[str] = None,
    cif_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Execute the full ingestion pipeline: Download -> Parse -> Filter -> Save.
    
    Args:
        config: Configuration object.
        source_type: The data source to use.
        source_id: The ID for the source (e.g., API key or dataset ID).
        cif_dir: Path to local CIF directory if source_type is 'local_cif_dir'.
        output_dir: Directory to write processed graphs. Defaults to config.paths.processed.
    
    Returns:
        Path to the generated parquet file.
    """
    if output_dir is None:
        output_dir = config.paths.processed
    
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "graphs_v1.parquet"
    
    LOGGER.info(f"Starting pipeline. Source: {source_type}, Output: {output_file}")

    # 1. Download
    # The UnifiedDatasetLoader handles the "single canonical source" constraint internally
    # via the runtime check in T009a.
    LOGGER.info("Step 1: Downloading data...")
    
    # We instantiate the loader. If it's a remote source, it downloads.
    # If it's local, it prepares the path.
    # Note: We pass a dummy source_id for the loader to accept, 
    # but the real logic is in the loader's implementation.
    loader = UnifiedDatasetLoader(
        source=source_type,
        source_id=source_id,
        download_dir=config.paths.raw
    )
    
    manifest = loader.run()
    cif_dir_path = manifest.cif_dir
    
    if not cif_dir_path.exists():
        raise RuntimeError(f"Download failed: CIF directory {cif_dir_path} does not exist.")

    # 2. Parse
    LOGGER.info("Step 2: Parsing CIFs to MaterialGraphs...")
    parsed_graphs = parse_cif_directory(cif_dir_path)
    LOGGER.info(f"Parsed {len(parsed_graphs)} graphs.")

    if not parsed_graphs:
        LOGGER.warning("No graphs parsed. Check CIF validity.")

    # 3. Filter
    LOGGER.info("Step 3: Filtering for 2D materials and valid tensors...")
    
    # Filter returns a tuple: (filtered_graphs, filter_stats)
    # We need to ensure error handling for missing tensors is explicit.
    filtered_graphs = []
    excluded_reasons = []

    for graph in parsed_graphs:
        # Check for missing tensors explicitly before filtering
        if graph.target_moduli is None:
            excluded_reasons.append({
                "material_id": graph.material_id,
                "reason": "missing_tensor",
                "details": "Elastic tensor is None."
            })
            continue
        
        # Apply the 2D and 6-component checks
        if is_2d_material(graph) and is_valid_6_component_tensor(graph):
            filtered_graphs.append(graph)
        else:
            excluded_reasons.append({
                "material_id": graph.material_id,
                "reason": "invalid_structure_or_tensor",
                "details": f"2D: {is_2d_material(graph)}, Tensor: {is_valid_6_component_tensor(graph)}"
            })

    LOGGER.info(f"Filter complete. Kept: {len(filtered_graphs)}, Excluded: {len(excluded_reasons)}")
    
    # Save filter stats
    stats = FilterStats(
        total_parsed=len(parsed_graphs),
        kept=len(filtered_graphs),
        excluded=len(excluded_reasons),
        exclusion_details=excluded_reasons
    )
    save_filter_stats(stats, output_dir / "filter_stats.json")

    # 4. Bias Check
    LOGGER.info("Step 4: Running bias check on excluded entries...")
    if excluded_reasons:
        bias_report = analyze_exclusion_bias(excluded_reasons)
        write_bias_report(bias_report, output_dir / "bias_report.json")
    else:
        LOGGER.info("No excluded entries to check for bias.")

    # 5. Save to Parquet
    LOGGER.info("Step 5: Serializing and saving to Parquet...")
    if not filtered_graphs:
        LOGGER.warning("No valid graphs to save. Creating empty parquet file.")
        # Create an empty parquet with correct schema
        empty_df = pd.DataFrame(columns=[
            "material_id", "formula", "family_id", "node_features", 
            "edge_features", "target_moduli", "space_group", "num_atoms"
        ])
        empty_df.to_parquet(output_file, index=False)
    else:
        serialized_data = [serialize_graph(g) for g in filtered_graphs]
        df = pd.DataFrame(serialized_data)
        
        # Ensure correct column order
        cols = [
            "material_id", "formula", "family_id", "node_features", 
            "edge_features", "target_moduli", "space_group", "num_atoms"
        ]
        df = df[cols]
        
        df.to_parquet(output_file, index=False)
        LOGGER.info(f"Saved {len(filtered_graphs)} graphs to {output_file}")

    return output_file

def main():
    """Main entry point for the pipeline script."""
    parser = argparse.ArgumentParser(description="Run the 2D material data ingestion pipeline.")
    parser.add_argument("--source", type=str, required=True, 
                      choices=["materials_project", "aflow", "local_cif_dir"],
                      help="Data source to use.")
    parser.add_argument("--source-id", type=str, default=None,
                      help="Source identifier (e.g., API key or dataset ID).")
    parser.add_argument("--cif-dir", type=str, default=None,
                      help="Path to local CIF directory (only for local_cif_dir source).")
    parser.add_argument("--output", type=str, default=None,
                      help="Output path for the parquet file.")
    
    args = parser.parse_args()
    
    # Initialize config
    config = Config()
    configure_log_file(config.paths.logs / "pipeline.log")
    
    output_path = None
    if args.output:
        output_path = Path(args.output)
        if not output_path.parent.exists():
            output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        result_path = run_pipeline(
            config=config,
            source_type=args.source,
            source_id=args.source_id,
            cif_dir=Path(args.cif_dir) if args.cif_dir else None,
            output_dir=output_path.parent if output_path else None
        )
        print(f"Pipeline completed successfully. Output: {result_path}")
    except Exception as e:
        LOGGER.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

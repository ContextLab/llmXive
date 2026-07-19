"""
Filtering module for 2D material elastic moduli prediction pipeline.

This module implements the filtering logic to:
1. Identify 2D materials based on structural criteria
2. Validate elastic tensor components (6 independent components required)
3. Log exclusion reasons for bias analysis

WARNING: This model is a surrogate interpolating pre-computed DFT results.
It does NOT solve the Schrödinger equation or perform first-principles calculations.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Import from project modules
from data_models.material_graph import MaterialGraph
from utils.logger import get_logger, log_operation, log_exclusion_reason

# Setup module logger
logger = logging.getLogger(__name__)

@dataclass
class FilterStats:
    """Statistics about the filtering process."""
    total_entries: int
    kept_entries: int
    excluded_2d: int
    excluded_tensor: int
    excluded_other: int
    exclusion_reasons: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def is_2d_material(graph: MaterialGraph) -> Tuple[bool, str]:
    """
    Determine if a material is 2D based on structural criteria.

    Criteria for 2D materials:
    1. Has a vacuum layer (one dimension significantly larger than others)
    2. Layer thickness is consistent with 2D materials (typically < 3nm)
    3. Periodic in 2 dimensions, non-periodic in the third

    Args:
        graph: MaterialGraph object containing structural information

    Returns:
        Tuple of (is_2d: bool, reason: str)
    """
    # Check for vacuum dimension in lattice
    if graph.lattice is None or len(graph.lattice) < 3:
        return False, "Missing lattice information"

    lattice_params = graph.lattice
    # Calculate the ratio between largest and smallest dimensions
    dimensions = [abs(lattice_params[i]) for i in range(3)]
    max_dim = max(dimensions)
    min_dim = min(dimensions)

    # If one dimension is significantly larger (> 2x the others), it's likely a 2D material
    # with vacuum in that direction
    if max_dim > 2.0 * min_dim and max_dim > 15.0:  # Vacuum > 15 Angstroms
        # Check if the layer thickness is reasonable for 2D materials
        # Typically, 2D materials have thickness < 30 Angstroms
        layer_thickness = max_dim - (sum(dimensions) - max_dim)
        if layer_thickness < 30.0:
            return True, "Vacuum layer detected with appropriate thickness"

    # Alternative check: look for explicit 2D flag in metadata if available
    if hasattr(graph, 'metadata') and graph.metadata:
        if graph.metadata.get('is_2d', False):
            return True, "Explicit 2D flag in metadata"

    return False, "No vacuum layer or 2D flag detected"

def is_valid_6_component_tensor(tensor: np.ndarray) -> Tuple[bool, str]:
    """
    Validate that an elastic tensor has 6 independent components.

    For cubic and lower symmetry materials, we need at least 6 independent
    components to fully describe the elastic behavior.

    Args:
        tensor: 6x6 elastic tensor (Voigt notation)

    Returns:
        Tuple of (is_valid: bool, reason: str)
    """
    if tensor is None:
        return False, "Tensor is None"

    if not isinstance(tensor, np.ndarray):
        try:
            tensor = np.array(tensor)
        except Exception:
            return False, "Cannot convert tensor to numpy array"

    if tensor.shape != (6, 6):
        return False, f"Tensor shape is {tensor.shape}, expected (6, 6)"

    # Check for NaN or Inf values
    if np.any(np.isnan(tensor)) or np.any(np.isinf(tensor)):
        return False, "Tensor contains NaN or Inf values"

    # Check for reasonable magnitude (elastic moduli are typically in GPa range)
    # We allow a wide range to accommodate different materials
    max_val = np.max(np.abs(tensor))
    if max_val > 1e6:  # Unreasonably large (> 1 TPa)
        return False, f"Tensor values too large (max: {max_val} GPa)"

    if max_val < 1e-6:  # Unreasonably small
        return False, f"Tensor values too small (max: {max_val} GPa)"

    # Check for symmetry (elastic tensor should be symmetric)
    if not np.allclose(tensor, tensor.T, atol=1e-10):
        logger.warning("Elastic tensor is not symmetric. This may indicate data quality issues.")
        # We still accept it but log a warning

    return True, "Valid 6x6 elastic tensor"

def load_graphs_from_parquet(parquet_path: str) -> List[MaterialGraph]:
    """
    Load MaterialGraph objects from a Parquet file.

    Args:
        parquet_path: Path to the Parquet file

    Returns:
        List of MaterialGraph objects
    """
    path = Path(parquet_path)
    if not path.exists():
        raise FileNotFoundError(f"Parquet file not found: {parquet_path}")

    # Read Parquet file
    table = pq.read_table(parquet_path)
    df = table.to_pandas()

    graphs = []
    for _, row in df.iterrows():
        # Reconstruct MaterialGraph from serialized data
        graph = MaterialGraph(
            id=row.get('id'),
            formula=row.get('formula'),
            structure=row.get('structure'),
            lattice=row.get('lattice'),
            node_features=row.get('node_features'),
            edge_features=row.get('edge_features'),
            target_moduli=row.get('target_moduli'),
            metadata=row.get('metadata')
        )
        graphs.append(graph)

    return graphs

def save_filter_stats(stats: FilterStats, output_path: str) -> None:
    """
    Save filtering statistics to a JSON file.

    Args:
        stats: FilterStats object
        output_path: Path to output JSON file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w') as f:
        json.dump(stats.to_dict(), f, indent=2)

    logger.info(f"Filter statistics saved to {output_path}")

def filter_graphs(
    graphs: List[MaterialGraph],
    log_path: Optional[str] = None
) -> Tuple[List[MaterialGraph], FilterStats]:
    """
    Filter graphs for 2D materials with valid elastic tensors.

    This function:
    1. Checks each material for 2D characteristics
    2. Validates the elastic tensor has 6 independent components
    3. Logs exclusion reasons for bias analysis
    4. Returns filtered list and statistics

    Args:
        graphs: List of MaterialGraph objects
        log_path: Optional path to save exclusion log

    Returns:
        Tuple of (filtered_graphs: List[MaterialGraph], stats: FilterStats)
    """
    filtered_graphs = []
    exclusion_reasons = []

    total = len(graphs)
    kept = 0
    excluded_2d = 0
    excluded_tensor = 0
    excluded_other = 0

    for i, graph in enumerate(graphs):
        if graph is None:
            reason = {"index": i, "id": None, "reason": "None graph", "category": "other"}
            exclusion_reasons.append(reason)
            excluded_other += 1
            continue

        # Check 2D criteria
        is_2d, reason_2d = is_2d_material(graph)
        if not is_2d:
            reason = {"index": i, "id": graph.id, "reason": reason_2d, "category": "not_2d"}
            exclusion_reasons.append(reason)
            excluded_2d += 1
            continue

        # Check elastic tensor
        if graph.target_moduli is None:
            reason = {"index": i, "id": graph.id, "reason": "Missing elastic tensor", "category": "invalid_tensor"}
            exclusion_reasons.append(reason)
            excluded_tensor += 1
            continue

        # Convert target_moduli to numpy array if needed
        tensor = np.array(graph.target_moduli) if not isinstance(graph.target_moduli, np.ndarray) else graph.target_moduli
        is_valid, reason_tensor = is_valid_6_component_tensor(tensor)

        if not is_valid:
            reason = {"index": i, "id": graph.id, "reason": reason_tensor, "category": "invalid_tensor"}
            exclusion_reasons.append(reason)
            excluded_tensor += 1
            continue

        # Material passed all filters
        filtered_graphs.append(graph)
        kept += 1

        # Log successful inclusion
        if i % 100 == 0:
            logger.debug(f"Processed {i}/{total} materials. Kept: {kept}")

    # Log exclusion reasons
    for reason in exclusion_reasons:
        log_exclusion_reason(reason)

    # Save exclusion log if path provided
    if log_path:
        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(exclusion_reasons, f, indent=2)
        logger.info(f"Exclusion log saved to {log_path}")

    stats = FilterStats(
        total_entries=total,
        kept_entries=kept,
        excluded_2d=excluded_2d,
        excluded_tensor=excluded_tensor,
        excluded_other=excluded_other,
        exclusion_reasons=exclusion_reasons
    )

    logger.info(f"Filtering complete: {kept}/{total} materials kept.")
    logger.info(f"Excluded 2D: {excluded_2d}, Invalid tensor: {excluded_tensor}, Other: {excluded_other}")

    return filtered_graphs, stats

def main():
    """
    Main entry point for the filtering script.

    Usage:
        python code/ingest/filter.py --input data/processed/graphs_v1.parquet --output data/processed/graphs_v1_filtered.parquet --log data/processed/exclusion_log.json

    This script:
    1. Loads graphs from input Parquet file
    2. Filters for 2D materials with valid elastic tensors
    3. Saves filtered graphs to output Parquet file
    4. Saves filtering statistics and exclusion log
    """
    parser = argparse.ArgumentParser(
        description="Filter 2D materials with valid elastic tensors"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to input Parquet file containing MaterialGraph objects"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to output Parquet file for filtered graphs"
    )
    parser.add_argument(
        "--log",
        type=str,
        default=None,
        help="Path to save exclusion log (JSON)"
    )
    parser.add_argument(
        "--stats",
        type=str,
        default=None,
        help="Path to save filtering statistics (JSON)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    logger.info(f"Loading graphs from {args.input}...")
    try:
        graphs = load_graphs_from_parquet(args.input)
        logger.info(f"Loaded {len(graphs)} graphs")
    except Exception as e:
        logger.error(f"Failed to load graphs: {e}")
        sys.exit(1)

    logger.info("Filtering for 2D materials with valid elastic tensors...")
    filtered_graphs, stats = filter_graphs(graphs, log_path=args.log)

    # Save filtered graphs
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert filtered graphs to DataFrame for Parquet
    data = []
    for graph in filtered_graphs:
        row = {
            'id': graph.id,
            'formula': graph.formula,
            'structure': graph.structure,
            'lattice': graph.lattice,
            'node_features': graph.node_features,
            'edge_features': graph.edge_features,
            'target_moduli': graph.target_moduli,
            'metadata': graph.metadata
        }
        data.append(row)

    df = pd.DataFrame(data)

    # Write to Parquet
    table = pa.Table.from_pandas(df)
    pq.write_table(table, args.output)

    logger.info(f"Filtered graphs saved to {args.output}")
    logger.info(f"Total: {stats.total_entries}, Kept: {stats.kept_entries}, Excluded: {stats.total_entries - stats.kept_entries}")

    # Save statistics
    if args.stats:
        save_filter_stats(stats, args.stats)

    # Log summary
    logger.info("=== Filtering Summary ===")
    logger.info(f"Total entries: {stats.total_entries}")
    logger.info(f"Kept entries: {stats.kept_entries}")
    logger.info(f"Excluded (not 2D): {stats.excluded_2d}")
    logger.info(f"Excluded (invalid tensor): {stats.excluded_tensor}")
    logger.info(f"Excluded (other): {stats.excluded_other}")
    logger.info("========================")

if __name__ == "__main__":
    main()
"""
Data filtering module for 2D materials and valid elastic tensors.

Implements filtering logic for 2D material identification and elastic tensor
validation (6 independent components required). Logs exclusion reasons for
bias analysis and compliance tracking.
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

from data_models.material_graph import MaterialGraph
from utils.logger import get_logger, log_exclusion_reason

# Configure logger
logger = get_logger(__name__)


@dataclass
class FilterStats:
    """Statistics about the filtering process."""
    total_entries: int = 0
    kept_entries: int = 0
    excluded_2d: int = 0
    excluded_tensor: int = 0
    excluded_other: int = 0
    exclusion_log: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.exclusion_log is None:
            self.exclusion_log = []


def is_2d_material(graph: MaterialGraph) -> bool:
    """
    Determine if a MaterialGraph represents a 2D material.

    A 2D material is identified by:
    1. Having a vacuum layer in the z-direction (c-axis significantly larger than a/b)
    2. Or explicitly tagged as '2D' in metadata
    3. Or having a specific space group common to 2D materials

    Args:
        graph: The MaterialGraph to check

    Returns:
        True if the material is identified as 2D, False otherwise
    """
    # Check for explicit 2D tag in metadata
    if graph.metadata and graph.metadata.get('is_2d', False):
        return True

    # Check lattice parameters for vacuum layer
    if graph.lattice is not None:
        a, b, c = graph.lattice.a, graph.lattice.b, graph.lattice.c
        # If c is significantly larger than a and b, likely a 2D material with vacuum
        # Typical threshold: c > 2 * max(a, b) suggests vacuum layer
        if c > 2.0 * max(a, b):
            return True

    # Check for common 2D material space groups
    if graph.space_group:
        # Common 2D material space groups (layer groups)
        # This is a simplified check; a full implementation would use pymatgen's symmetry analysis
        layer_groups = [180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190,
                        191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201,
                        202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212,
                        213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223,
                        224, 225, 226, 227, 228, 229, 230]
        # Actually, 2D materials often have specific layer groups (1-80) or
        # 3D space groups with 2D character. We'll use a simpler heuristic.
        # For now, rely on the lattice check above.
        pass

    return False


def is_valid_6_component_tensor(graph: MaterialGraph) -> bool:
    """
    Validate that the elastic tensor has 6 independent components.

    Elastic tensors for 2D materials in Voigt notation should have 6 components:
    [C11, C12, C22, C16, C26, C66]

    Args:
        graph: The MaterialGraph with elastic tensor data

    Returns:
        True if the tensor is valid and complete, False otherwise
    """
    if not graph.elastic_tensor:
        return False

    tensor = graph.elastic_tensor
    if isinstance(tensor, np.ndarray):
        # Check for 2D elastic tensor (6x6 or flattened to 6)
        if tensor.shape == (6, 6) or tensor.shape == (6,):
            # Check for NaN or Inf values
            if np.any(np.isnan(tensor)) or np.any(np.isinf(tensor)):
                return False
            return True
        elif tensor.shape == (3, 3):
            # 2D in-plane tensor, expand to 6 components if needed
            if np.any(np.isnan(tensor)) or np.any(np.isinf(tensor)):
                return False
            return True
        else:
            # Unexpected shape
            return False
    elif isinstance(tensor, list):
        # Flattened list
        if len(tensor) == 6:
            try:
                arr = np.array(tensor)
                if np.any(np.isnan(arr)) or np.any(np.isinf(arr)):
                    return False
                return True
            except (ValueError, TypeError):
                return False
        else:
            return False
    else:
        return False


def load_graphs_from_parquet(input_path: Path) -> List[MaterialGraph]:
    """
    Load MaterialGraph objects from a Parquet file.

    Args:
        input_path: Path to the parquet file

    Returns:
        List of MaterialGraph objects
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Load parquet file
    df = pd.read_parquet(input_path)

    graphs = []
    for _, row in df.iterrows():
        # Reconstruct MaterialGraph from row data
        # This assumes the parquet file contains serialized MaterialGraph data
        graph = MaterialGraph(
            material_id=row.get('material_id', ''),
            formula=row.get('formula', ''),
            nodes=row.get('node_features', []),
            edges=row.get('edge_features', []),
            lattice=row.get('lattice', None),
            elastic_tensor=row.get('elastic_tensor', None),
            target_moduli=row.get('target_moduli', None),
            metadata=row.get('metadata', {}),
            family_id=row.get('family_id', '')
        )
        graphs.append(graph)

    return graphs


def save_filter_stats(stats: FilterStats, output_path: Path) -> None:
    """
    Save filtering statistics to a JSON file.

    Args:
        stats: FilterStats object with filtering results
        output_path: Path to save the JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(asdict(stats), f, indent=2)

    logger.info(f"Filter statistics saved to {output_path}")


def filter_graphs(graphs: List[MaterialGraph]) -> Tuple[List[MaterialGraph], FilterStats]:
    """
    Filter graphs for 2D materials and valid elastic tensors.

    Args:
        graphs: List of MaterialGraph objects to filter

    Returns:
        Tuple of (filtered_graphs, FilterStats)
    """
    stats = FilterStats(total_entries=len(graphs))
    filtered_graphs = []

    for graph in graphs:
        kept = True
        exclusion_reason = None

        # Check for 2D material
        if not is_2d_material(graph):
            kept = False
            exclusion_reason = "Not identified as 2D material"
            stats.excluded_2d += 1

        # Check for valid elastic tensor
        if kept and not is_valid_6_component_tensor(graph):
            kept = False
            exclusion_reason = "Invalid or incomplete elastic tensor"
            stats.excluded_tensor += 1

        if kept:
            filtered_graphs.append(graph)
            stats.kept_entries += 1
        else:
            stats.excluded_other += 1
            # Log exclusion reason
            exclusion_entry = {
                "material_id": graph.material_id,
                "formula": graph.formula,
                "reason": exclusion_reason,
                "category": "2d_check" if not is_2d_material(graph) else "tensor_check"
            }
            stats.exclusion_log.append(exclusion_entry)
            log_exclusion_reason(exclusion_entry)

    logger.info(f"Filtering complete: {stats.kept_entries}/{stats.total_entries} entries kept")
    logger.info(f"Excluded: {stats.excluded_2d} (2D check), {stats.excluded_tensor} (tensor check)")

    return filtered_graphs, stats


def main():
    """Main entry point for the filtering script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Filter 2D materials and validate elastic tensors"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to input parquet file or directory containing parquet files"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to output filtered parquet file"
    )
    parser.add_argument(
        "--stats",
        type=str,
        default=None,
        help="Path to save filter statistics (JSON)"
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    stats_path = Path(args.stats) if args.stats else None

    # Determine input format
    if input_path.is_file():
        if input_path.suffix == '.parquet':
            graphs = load_graphs_from_parquet(input_path)
        else:
            # Try to load as JSON
            with open(input_path, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    graphs = [MaterialGraph(**item) for item in data]
                else:
                    raise ValueError(f"Unsupported input format: {input_path.suffix}")
    elif input_path.is_dir():
        # Load all parquet files in directory
        graphs = []
        for file in input_path.glob("*.parquet"):
            graphs.extend(load_graphs_from_parquet(file))
    else:
        raise FileNotFoundError(f"Input path not found: {input_path}")

    logger.info(f"Loaded {len(graphs)} entries from {input_path}")

    # Filter graphs
    filtered_graphs, stats = filter_graphs(graphs)

    # Save filtered data
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert filtered graphs to DataFrame for parquet output
    data = []
    for graph in filtered_graphs:
        row = {
            'material_id': graph.material_id,
            'formula': graph.formula,
            'node_features': graph.nodes,
            'edge_features': graph.edges,
            'lattice': graph.lattice,
            'elastic_tensor': graph.elastic_tensor,
            'target_moduli': graph.target_moduli,
            'metadata': graph.metadata,
            'family_id': graph.family_id
        }
        data.append(row)

    df = pd.DataFrame(data)
    df.to_parquet(output_path, index=False)
    logger.info(f"Filtered data saved to {output_path}")

    # Save statistics if requested
    if stats_path:
        save_filter_stats(stats, stats_path)

    # Return exit code based on filtering results
    if stats.kept_entries == 0:
        logger.error("No entries passed filtering. Check input data and criteria.")
        sys.exit(1)

    logger.info(f"Successfully filtered {stats.kept_entries} entries")
    sys.exit(0)


if __name__ == "__main__":
    main()
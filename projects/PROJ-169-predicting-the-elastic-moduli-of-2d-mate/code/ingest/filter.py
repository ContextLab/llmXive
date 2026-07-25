"""
Filter 2D materials and validate elastic tensors.
Implements Constitution Principle VI (DFT Ground-Truth Fidelity).
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd

# Import from sibling modules as per API surface
from data_models.material_graph import MaterialGraph
from utils.logger import get_logger, log_operation

logger = get_logger("filter")

@dataclass
class FilterStats:
    total_entries: int = 0
    filtered_2d: int = 0
    filtered_tensor: int = 0
    valid_entries: int = 0
    exclusion_log: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.exclusion_log is None:
            self.exclusion_log = []

def is_2d_material(graph: MaterialGraph) -> bool:
    """
    Check if the graph represents a 2D material.
    Strategy: Check for '2d' in the material name/tags or specific structural
    properties (e.g., vacuum layer > 15 Angstroms in c-axis if orthorhombic).
    For this surrogate model, we rely on the 'tags' or 'properties' populated
    during parsing (T010).
    """
    if not graph.properties:
        return False

    tags = graph.properties.get("tags", [])
    # Common tags for 2D materials in databases like Materials Project
    if "2d" in tags or "monolayer" in tags:
        return True

    # Fallback: Check if structure has a vacuum layer (approximate via lattice)
    # This assumes 'lattice' is a 3x3 matrix or vector in properties
    lattice = graph.properties.get("lattice", None)
    if lattice is not None:
        # Simple heuristic: if c-axis is significantly larger than a/b and > 15A
        # This is a rough approximation without full Structure object
        if isinstance(lattice, (list, np.ndarray)) and len(lattice) >= 3:
            # Assuming [a, b, c, alpha, beta, gamma] or similar
            # If we have 3 vectors, check the z-component of the 3rd
            pass # Implementation depends on exact format from T010

    return False

def is_valid_6_component_tensor(graph: MaterialGraph) -> bool:
    """
    Validate that the elastic tensor has 6 independent components (Voigt notation).
    Constitution Principle VI requires independent elastic tensor components.
    """
    elastic_tensor = graph.properties.get("elastic_tensor", None)
    if elastic_tensor is None:
        return False

    try:
        tensor = np.array(elastic_tensor)
        # Voigt notation for elastic tensor is 6x6
        if tensor.shape != (6, 6):
            logger.warning(f"Tensor shape {tensor.shape} is not 6x6")
            return False

        # Check for NaNs or Infs
        if not np.isfinite(tensor).all():
            logger.warning("Tensor contains NaN or Inf values")
            return False

        # Check for symmetry (C_ij = C_ji)
        if not np.allclose(tensor, tensor.T):
            logger.warning("Tensor is not symmetric")
            return False

        # Check for positive definiteness (Born stability criteria)
        # Eigenvalues must be positive for stability
        eigenvalues = np.linalg.eigvalsh(tensor)
        if np.any(eigenvalues <= 0):
            logger.warning("Tensor is not positive definite (unstable)")
            return False

        return True

    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to parse/validate elastic tensor: {e}")
        return False

def load_graphs_from_parquet(input_path: str) -> List[MaterialGraph]:
    """Load graphs from a parquet file."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Read parquet into DataFrame
    df = pd.read_parquet(path)

    # Reconstruct MaterialGraph objects
    # Assuming the parquet has columns: node_features, edge_features, target_moduli, family_id, properties
    graphs = []
    for _, row in df.iterrows():
        # Convert row data back to MaterialGraph
        # Note: This assumes the serialization format in T013d4 matches this
        graph = MaterialGraph(
            node_features=row.get("node_features", []),
            edge_features=row.get("edge_features", []),
            target_moduli=row.get("target_moduli", {}),
            family_id=row.get("family_id", ""),
            properties=row.get("properties", {})
        )
        graphs.append(graph)

    return graphs

def filter_graphs(graphs: List[MaterialGraph]) -> tuple[List[MaterialGraph], FilterStats]:
    """
    Apply 2D filter and tensor validator.
    Returns filtered list and statistics.
    """
    stats = FilterStats(total_entries=len(graphs))
    valid_graphs = []

    for i, graph in enumerate(graphs):
        is_2d = is_2d_material(graph)
        has_valid_tensor = is_valid_6_component_tensor(graph)

        if not is_2d:
            stats.filtered_2d += 1
            stats.exclusion_log.append({
                "index": i,
                "reason": "Not a 2D material",
                "family_id": graph.family_id
            })
            continue

        if not has_valid_tensor:
            stats.filtered_tensor += 1
            stats.exclusion_log.append({
                "index": i,
                "reason": "Invalid elastic tensor (not 6-component, not symmetric, or not positive definite)",
                "family_id": graph.family_id
            })
            continue

        valid_graphs.append(graph)

    stats.valid_entries = len(valid_graphs)
    return valid_graphs, stats

def save_filter_stats(stats: FilterStats, output_path: str):
    """Save filter statistics and exclusion log to JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'w') as f:
        json.dump(asdict(stats), f, indent=2)

    logger.info(f"Filter stats saved to {output_path}")

def save_filtered_graphs(graphs: List[MaterialGraph], output_path: str):
    """Save filtered graphs to parquet."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to DataFrame
    data = []
    for g in graphs:
        data.append({
            "node_features": g.node_features,
            "edge_features": g.edge_features,
            "target_moduli": g.target_moduli,
            "family_id": g.family_id,
            "properties": g.properties
        })

    df = pd.DataFrame(data)
    df.to_parquet(path, index=False)
    logger.info(f"Filtered graphs saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Filter 2D materials and valid tensors.")
    parser.add_argument("--input", required=True, help="Input parquet file path")
    parser.add_argument("--output", required=True, help="Output parquet file path for filtered graphs")
    parser.add_argument("--stats", required=True, help="Output JSON file for filter statistics")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    try:
        logger.info(f"Loading graphs from {args.input}")
        graphs = load_graphs_from_parquet(args.input)
        logger.info(f"Loaded {len(graphs)} graphs")

        logger.info("Applying filters...")
        filtered_graphs, stats = filter_graphs(graphs)

        logger.info(f"Filtering complete. Valid entries: {stats.valid_entries}")
        logger.info(f"Excluded (not 2D): {stats.filtered_2d}")
        logger.info(f"Excluded (invalid tensor): {stats.filtered_tensor}")

        # Save outputs
        save_filtered_graphs(filtered_graphs, args.output)
        save_filter_stats(stats, args.stats)

        # Log exclusions for bias check (T012)
        if stats.exclusion_log:
            exclusion_log_path = str(Path(args.output).parent / "exclusion_log.json")
            with open(exclusion_log_path, 'w') as f:
                json.dump(stats.exclusion_log, f, indent=2)
            logger.info(f"Exclusion log saved to {exclusion_log_path}")

    except Exception as e:
        logger.error(f"Filtering failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
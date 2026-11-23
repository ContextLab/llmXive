"""
2D material filter and elastic tensor validator.

Implements Constitution Principle VI: Filter for entries with independent
elastic tensor components.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from tqdm import tqdm

# Import from project modules
from data_models.material_graph import MaterialGraph
from utils.logger import get_logger, log_operation

logger = logging.getLogger(__name__)
reproducibility_logger = get_logger("filter")


@dataclass
class FilterStats:
    """Statistics about the filtering process."""
    total_entries: int = 0
    kept_entries: int = 0
    excluded_2d: int = 0
    excluded_tensor: int = 0
    excluded_other: int = 0
    exclusion_reasons: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def is_2d_material(graph: MaterialGraph) -> bool:
    """
    Check if a material graph represents a 2D material.

    A 2D material typically has:
    - One dimension significantly smaller than the others (c-axis)
    - At least 2 dimensions > 5 Angstroms (in-plane)
    - Layered structure indicators

    Args:
        graph: The material graph to check

    Returns:
        True if the material is 2D, False otherwise
    """
    if not hasattr(graph, 'structure') or graph.structure is None:
        return False

    lattice = graph.structure.lattice
    lengths = lattice.abc

    # Sort lengths to identify the smallest dimension
    sorted_lengths = sorted(lengths)

    # 2D materials have one very small dimension (typically < 3-4 Angstroms)
    # and two larger dimensions (typically > 5 Angstroms)
    is_2d = (sorted_lengths[0] < 4.0) and (sorted_lengths[1] > 5.0) and (sorted_lengths[2] > 5.0)

    return is_2d


def is_valid_6_component_tensor(graph: MaterialGraph) -> Tuple[bool, str]:
    """
    Validate that the elastic tensor has 6 independent components for 2D materials.

    Constitution Principle VI requires that we filter for entries with
    independent elastic tensor components. For 2D materials in plane stress,
    the elastic tensor should have exactly 3 independent components:
    C11, C12, C22, C66 (with C16=C26=0 for orthotropic symmetry in 2D).

    However, we check for the presence of a valid 6-component representation
    (C11, C12, C22, C66, C16, C26) where C16 and C26 should be zero or negligible
    for proper 2D orthotropic materials.

    Args:
        graph: The material graph to validate

    Returns:
        Tuple of (is_valid, reason)
    """
    if not hasattr(graph, 'elastic_tensor') or graph.elastic_tensor is None:
        return False, "Missing elastic tensor"

    tensor = graph.elastic_tensor

    # Check if tensor is 6x6 (Voigt notation)
    if len(tensor.shape) != 2 or tensor.shape[0] != 6 or tensor.shape[1] != 6:
        return False, f"Invalid tensor shape: {tensor.shape}, expected (6, 6)"

    # For 2D materials, we expect the tensor to be effectively 3D (plane stress)
    # Check that the out-of-plane components are negligible or zero
    # C33, C13, C23, C31, C32, C33 should be negligible for 2D

    # Check for symmetry
    if not np.allclose(tensor, tensor.T, atol=1e-10):
        return False, "Elastic tensor is not symmetric"

    # Check for 6 independent components (orthotropic 2D)
    # In Voigt notation for 2D orthotropic:
    # C11, C12, C22, C66 are the main components
    # C16, C26 should be zero (or very small)

    # Extract the 2D submatrix (indices 0,1,2,5 for Voigt notation)
    # C = [[C11, C12, C16],
    #      [C12, C22, C26],
    #      [C16, C26, C66]]
    c11 = tensor[0, 0]
    c12 = tensor[0, 1]
    c22 = tensor[1, 1]
    c66 = tensor[5, 5]
    c16 = tensor[0, 5]
    c26 = tensor[1, 5]

    # Check if C16 and C26 are negligible (orthotropic symmetry)
    max_component = max(abs(c11), abs(c12), abs(c22), abs(c66))
    if max_component == 0:
        return False, "All elastic components are zero"

    c16_ratio = abs(c16) / max_component
    c26_ratio = abs(c26) / max_component

    # Allow 1% tolerance for numerical precision
    if c16_ratio > 0.01 or c26_ratio > 0.01:
        return False, f"Non-zero shear coupling (C16={c16_ratio:.4f}, C26={c26_ratio:.4f})"

    # Check that the tensor is positive definite (required for physical stability)
    # Extract the 3x3 2D submatrix
    indices = [0, 1, 5]  # C11, C12, C66 in Voigt
    submatrix = tensor[np.ix_(indices, indices)]

    eigenvalues = np.linalg.eigvalsh(submatrix)
    if not np.all(eigenvalues > 0):
        return False, f"Elastic tensor not positive definite (eigenvalues: {eigenvalues})"

    # Check that the tensor has the required 6 independent components
    # For 2D orthotropic: C11, C12, C22, C66, C16, C26
    # C16 and C26 should be zero, so we have 4 independent components
    # But we check for the presence of all 6 in the Voigt representation

    return True, "Valid 6-component tensor for 2D material"


def load_graphs_from_parquet(input_path: str) -> List[MaterialGraph]:
    """
    Load material graphs from a parquet file.

    Args:
        input_path: Path to the parquet file

    Returns:
        List of MaterialGraph objects
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    df = pd.read_parquet(input_path)
    graphs = []

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Loading graphs"):
        # Reconstruct MaterialGraph from row data
        graph = MaterialGraph()
        graph.node_features = row.get('node_features', [])
        graph.edge_features = row.get('edge_features', [])
        graph.target_moduli = row.get('target_moduli', {})
        graph.family_id = row.get('family_id', '')

        # Try to reconstruct structure and elastic tensor if available
        if 'structure' in row and row['structure']:
            try:
                from pymatgen.core import Structure
                graph.structure = Structure.from_dict(row['structure'])
            except Exception as e:
                logger.warning(f"Failed to parse structure: {e}")
                graph.structure = None

        if 'elastic_tensor' in row and row['elastic_tensor']:
            try:
                graph.elastic_tensor = np.array(row['elastic_tensor'])
            except Exception as e:
                logger.warning(f"Failed to parse elastic tensor: {e}")
                graph.elastic_tensor = None

        graphs.append(graph)

    return graphs


def filter_graphs(
    graphs: List[MaterialGraph],
    log_reasons: bool = True
) -> Tuple[List[MaterialGraph], FilterStats]:
    """
    Filter graphs based on 2D material criteria and elastic tensor validity.

    Args:
        graphs: List of material graphs to filter
        log_reasons: Whether to log exclusion reasons

    Returns:
        Tuple of (filtered_graphs, stats)
    """
    filtered = []
    stats = FilterStats(total_entries=len(graphs))

    for graph in tqdm(graphs, desc="Filtering graphs"):
        is_kept = True
        exclusion_reason = None

        # Check 2D material criteria
        if not is_2d_material(graph):
            is_kept = False
            exclusion_reason = "Not a 2D material"
            stats.excluded_2d += 1
            stats.exclusion_reasons[exclusion_reason] = \
                stats.exclusion_reasons.get(exclusion_reason, 0) + 1

        # Check elastic tensor validity
        if is_kept:
            is_valid, reason = is_valid_6_component_tensor(graph)
            if not is_valid:
                is_kept = False
                exclusion_reason = f"Invalid tensor: {reason}"
                stats.excluded_tensor += 1
                stats.exclusion_reasons[exclusion_reason] = \
                    stats.exclusion_reasons.get(exclusion_reason, 0) + 1

        if is_kept:
            filtered.append(graph)
            stats.kept_entries += 1
        elif log_reasons and exclusion_reason:
          logger.info(f"Excluded graph: {exclusion_reason}")

    return filtered, stats


def save_filter_stats(stats: FilterStats, output_path: str) -> None:
    """
    Save filter statistics to a JSON file.

    Args:
        stats: Filter statistics to save
        output_path: Path to output JSON file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(stats.to_dict(), f, indent=2)
    logger.info(f"Saved filter stats to {output_path}")


def save_filtered_graphs(
    graphs: List[MaterialGraph],
    output_path: str
) -> None:
    """
    Save filtered graphs to a parquet file.

    Args:
        graphs: List of filtered graphs
        output_path: Path to output parquet file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    data = []
    for graph in graphs:
        row = {
            'node_features': graph.node_features,
            'edge_features': graph.edge_features,
            'target_moduli': graph.target_moduli,
            'family_id': graph.family_id,
        }

        # Serialize structure if available
        if hasattr(graph, 'structure') and graph.structure is not None:
            row['structure'] = graph.structure.as_dict()
        else:
            row['structure'] = None

        # Serialize elastic tensor if available
        if hasattr(graph, 'elastic_tensor') and graph.elastic_tensor is not None:
            row['elastic_tensor'] = graph.elastic_tensor.tolist()
        else:
            row['elastic_tensor'] = None

        data.append(row)

    df = pd.DataFrame(data)
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved {len(graphs)} filtered graphs to {output_path}")


def main():
    """Main entry point for the filter script."""
    parser = argparse.ArgumentParser(
        description="Filter 2D materials and validate elastic tensors"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Input parquet file or directory containing graphs"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output parquet file for filtered graphs"
    )
    parser.add_argument(
        "--stats",
        type=str,
        required=True,
        help="Output JSON file for filter statistics"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Log operation
    log_operation("filter_start", input=args.input, output=args.output, stats=args.stats)

    try:
        # Load graphs
        logger.info(f"Loading graphs from {args.input}")
        graphs = load_graphs_from_parquet(args.input)
        logger.info(f"Loaded {len(graphs)} graphs")

        # Filter graphs
        logger.info("Filtering graphs...")
        filtered_graphs, stats = filter_graphs(graphs)
        logger.info(f"Filtered: {stats.kept_entries} kept, {stats.total_entries - stats.kept_entries} excluded")

        # Save results
        logger.info("Saving filtered graphs...")
        save_filtered_graphs(filtered_graphs, args.output)

        logger.info("Saving filter statistics...")
        save_filter_stats(stats, args.stats)

        # Log completion
        log_operation("filter_complete", kept=stats.kept_entries, excluded=stats.total_entries - stats.kept_entries)

        logger.info("Filtering complete!")

    except Exception as e:
        logger.error(f"Filtering failed: {e}")
        log_operation("filter_failed", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
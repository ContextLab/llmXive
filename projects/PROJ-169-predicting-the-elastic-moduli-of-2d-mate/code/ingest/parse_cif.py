"""
CIF Parser for 2D Material Elastic Moduli Prediction.

Converts CIF files to MaterialGraph objects using pymatgen.
Extracts node features (atomic properties) and edge features (bond distances).
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

# Import the verified real data source loader if needed, though this task focuses on parsing
# The download.py task handles fetching, this task handles parsing existing CIFs

# Import MaterialGraph from the data models
try:
    from data_models.material_graph import MaterialGraph
except ImportError:
    # Fallback for direct execution context if path is not set up correctly
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from data_models.material_graph import MaterialGraph

# Lazy import of pymatgen to handle optional dependency gracefully
# but fail loudly if requested and missing, per constraints
PYMATGEN_AVAILABLE = False
try:
    from pymatgen.core import Structure, Lattice
    from pymatgen.analysis.graphs import StructureGraph
    from pymatgen.analysis.local_env import VoronoiNN
    PYMATGEN_AVAILABLE = True
except ImportError:
    pass

logger = logging.getLogger(__name__)

# Node feature keys
NODE_FEATURES = [
    'atomic_number',
    'electronegativity',
    'atomic_mass',
    'valence',
    'radius',
]

# Edge feature keys
EDGE_FEATURES = [
    'distance',
]


def get_atomic_properties(site: Any) -> Dict[str, float]:
    """
    Extracts atomic properties for a site in a pymatgen Structure.

    Args:
        site: A pymatgen Site object.

    Returns:
        Dictionary of atomic properties.
    """
    if not PYMATGEN_AVAILABLE:
        raise RuntimeError("pymatgen is not installed. Cannot extract atomic properties.")

    element = site.species_string
    # Using pymatgen's Element class for properties
    from pymatgen.core.periodic_table import Element
    el = Element(element)

    # Map to standardized features
    props = {
        'atomic_number': float(el.number),
        'electronegativity': float(el.X) if el.X else 0.0,
        'atomic_mass': float(el.atomic_mass),
        'valence': float(el.oxi_state_guesses()[0]) if el.oxi_state_guesses() else 0.0, # Simplified valence
        'radius': float(el.atomic_radius) if el.atomic_radius else 0.0,
    }
    return props


def parse_cif_file(cif_path: Path) -> Optional[MaterialGraph]:
    """
    Parses a single CIF file into a MaterialGraph object.

    Args:
        cif_path: Path to the CIF file.

    Returns:
        MaterialGraph object or None if parsing fails.
    """
    if not PYMATGEN_AVAILABLE:
        logger.error("pymatgen not installed. CIF parsing disabled.")
        return None

    try:
        structure = Structure.from_file(cif_path)
    except Exception as e:
        logger.warning(f"Failed to parse CIF {cif_path}: {e}")
        return None

    # Validate structure
    if structure is None or len(structure) == 0:
        logger.warning(f"Empty structure in {cif_path}")
        return None

    # Create graph using Voronoi NN
    try:
        sgraph = StructureGraph.with_local_env_strategy(structure, VoronoiNN())
    except Exception as e:
        logger.warning(f"Failed to create graph for {cif_path}: {e}")
        return None

    # Extract nodes
    nodes = []
    node_features = []
    for site in structure:
        node_data = {
            'species': site.species_string,
            'coords': list(site.coords),
            'properties': get_atomic_properties(site)
        }
        nodes.append(node_data)
        # Flatten features for the graph
        feat = [node_data['properties'][k] for k in NODE_FEATURES]
        node_features.append(feat)

    # Extract edges
    edges = []
    edge_features = []
    edge_indices = []

    # sgraph.graph is a networkx graph
    nx_graph = sgraph.graph
    for u, v, data in nx_graph.edges(data=True):
        # u and v are indices in the structure
        dist = data.get('distance', 0.0)
        edges.append([int(u), int(v)])
        edge_features.append([dist])
        edge_indices.append([int(u), int(v)])

    # Convert to numpy
    node_features_np = np.array(node_features, dtype=np.float32)
    edge_features_np = np.array(edge_features, dtype=np.float32)
    edge_indices_np = np.array(edge_indices, dtype=np.int64).T  # Shape: (2, num_edges)

    # Target: Elastic tensor is NOT extracted here, it is expected to be attached later
    # or passed separately. For this parser, we initialize target as None or empty.
    # The task T010 focuses on structure parsing.
    target_moduli = None

    # Create MaterialGraph
    graph = MaterialGraph(
        node_features=node_features_np,
        edge_features=edge_features_np,
        edge_indices=edge_indices_np,
        target_moduli=target_moduli,
        metadata={
            'source_file': str(cif_path),
            'num_atoms': len(nodes),
            'num_bonds': len(edges),
            'species_list': [n['species'] for n in nodes]
        }
    )

    return graph


def parse_cif_directory(cif_dir: Path, output_path: Optional[Path] = None) -> List[MaterialGraph]:
    """
    Parses all CIF files in a directory and returns a list of MaterialGraphs.

    Args:
        cif_dir: Directory containing CIF files.
        output_path: Optional path to save a JSON summary of the parsed graphs.

    Returns:
        List of MaterialGraph objects.
    """
    if not PYMATGEN_AVAILABLE:
        raise RuntimeError("pymatgen not installed. CIF parsing disabled.")

    cif_files = list(cif_dir.glob('*.cif')) + list(cif_dir.glob('*.CIF'))
    if not cif_files:
        logger.warning(f"No CIF files found in {cif_dir}")
        return []

    graphs = []
    for cif_file in cif_files:
        graph = parse_cif_file(cif_file)
        if graph is not None:
            graphs.append(graph)

    logger.info(f"Parsed {len(graphs)} valid graphs from {len(cif_files)} CIF files.")

    if output_path:
        # Save a summary JSON (not the full graph data, just metadata)
        summary = []
        for i, g in enumerate(graphs):
            summary.append({
                'index': i,
                'source': g.metadata.get('source_file', 'unknown'),
                'num_nodes': len(g.node_features),
                'num_edges': g.edge_indices.shape[1] if g.edge_indices is not None else 0
            })
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Wrote summary to {output_path}")

    return graphs


def main():
    """
    CLI entry point for parsing CIFs.
    """
    import argparse

    parser = argparse.ArgumentParser(description='Parse CIF files into MaterialGraphs.')
    parser.add_argument('--input', type=str, required=True, help='Path to input CIF file or directory.')
    parser.add_argument('--output', type=str, required=True, help='Path to output directory (for summary) or file (for single graph).')
    parser.add_argument('--format', type=str, choices=['json', 'parquet'], default='json', help='Output format.')

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not PYMATGEN_AVAILABLE:
        print("ERROR: pymatgen not installed. Install it to enable CIF parsing.")
        # Per constraint 9: Fail loudly, never silently.
        # We do not generate synthetic data.
        raise RuntimeError("pymatgen is required for this task.")

    if input_path.is_file():
        if input_path.suffix.lower() != '.cif':
            logger.error(f"Input file {input_path} is not a CIF file.")
            return 1
        graph = parse_cif_file(input_path)
        if graph is None:
            return 1
        # Save single graph as JSON for simplicity in this script, or parquet if requested
        # For now, save metadata summary as JSON as requested by the pattern in tasks.md
        # If a directory is expected, we create a summary.
        # The task T013 expects graphs_v1.parquet, but that is handled by the pipeline.
        # This script T010 focuses on the parsing logic.
        # Let's output a JSON summary to the specified output path if it's a directory,
        # or a JSON file if it's a file.
        if output_path.suffix == '.json' or output_path.suffix == '.parquet':
             # Save single graph data to JSON (simplified for CLI demo)
             # In real pipeline, T013 handles parquet.
             data = {
                 'num_nodes': len(graph.node_features),
                 'num_edges': graph.edge_indices.shape[1] if graph.edge_indices is not None else 0,
                 'metadata': graph.metadata
             }
             with open(output_path, 'w') as f:
                 json.dump(data, f, indent=2)
        else:
             # Assume directory
             output_path.mkdir(parents=True, exist_ok=True)
             summary_path = output_path / f"{input_path.stem}_summary.json"
             parse_cif_directory(input_path.parent, summary_path)
    elif input_path.is_dir():
        output_path.mkdir(parents=True, exist_ok=True)
        summary_path = output_path / "parsed_graphs_summary.json"
        parse_cif_directory(input_path, summary_path)
    else:
        logger.error(f"Input path {input_path} does not exist.")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())

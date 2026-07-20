from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from pymatgen.core import Structure
from pymatgen.io.cif import CifParser
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

# Import the data model defined in the project
from data_models.material_graph import MaterialGraph

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_atomic_properties(element_symbol: str) -> Dict[str, float]:
    """
    Extracts physical properties for a given element symbol.
    Uses a simplified mapping for demonstration; in a real pipeline,
    this would query a database like pymatgen's Element class or a custom CSV.
    """
    # Basic periodic table properties (placeholder values for robustness)
    # In a full implementation, use: from pymatgen.core import Element; Element(el).atomic_mass
    properties = {
        "atomic_number": 0,
        "atomic_mass": 0.0,
        "electronegativity": 0.0,
        "valence": 0.0,
        "radius": 0.0
    }

    try:
        from pymatgen.core import Element
        el = Element(element_symbol)
        properties["atomic_number"] = el.number
        properties["atomic_mass"] = el.atomic_mass
        properties["electronegativity"] = el.X
        # Valence is tricky; using common oxidation states or a heuristic
        # For now, we use a simplified heuristic or default to 0 if not found
        properties["valence"] = el.oxi_state_guesses(max_states=1)[0] if el.oxi_state_guesses(max_states=1) else 0.0
        properties["radius"] = el.atomic_radius
    except Exception as e:
        logger.warning(f"Could not fetch properties for {element_symbol}: {e}. Using defaults.")
        # Fallback to defaults (0.0) to prevent crash on missing data
        pass

    return properties


def parse_cif_file(cif_path: Path) -> Optional[MaterialGraph]:
    """
    Parses a single CIF file into a MaterialGraph object.
    Handles disconnected graphs and missing fields gracefully.
    """
    if not cif_path.exists():
        logger.error(f"CIF file not found: {cif_path}")
        return None

    try:
        parser = CifParser(str(cif_path))
        # pymatgen might return multiple structures if there are multiple
        # distinct phases in the CIF. We take the first one for simplicity,
        # or could aggregate them. Here we take the first valid structure.
        structures = parser.get_structures()
        if not structures:
            logger.warning(f"No structures found in {cif_path}")
            return None

        structure = structures[0]
    except Exception as e:
        logger.error(f"Failed to parse CIF {cif_path}: {e}")
        return None

    try:
        # Extract node features
        node_features = []
        for site in structure.sites:
            props = get_atomic_properties(site.species_string)
            node_features.append(props)

        # If the structure is empty or has no sites, return None
        if not node_features:
            logger.warning(f"Structure in {cif_path} has no sites.")
            return None

        # Handle disconnected graphs:
        # Pymatgen structures are typically connected lattices.
        # However, if the CIF contains disconnected fragments (rare in DFT data),
        # we treat the whole set of sites as one graph.
        # We construct edges based on a cutoff distance or neighbor list.
        # Here we use a simple distance-based neighbor list.
        lattice = structure.lattice
        coords = structure.frac_coords
        species = [site.species_string for site in structure.sites]

        # Convert fractional to Cartesian for distance calculation
        cartesian_coords = lattice.get_cartesian_coords(coords)
        num_atoms = len(cartesian_coords)

        # Build adjacency (edges)
        # Use a cutoff based on bond lengths or a fixed value (e.g., 5.0 Angstroms)
        # A more robust way is to use pymatgen's get_bonded_sites or similar,
        # but we'll implement a simple distance cutoff for the graph construction.
        cutoff = 5.0  # Angstroms
        edge_indices = []
        edge_features = []

        for i in range(num_atoms):
            for j in range(i + 1, num_atoms):
                dist = np.linalg.norm(cartesian_coords[i] - cartesian_coords[j])
                if dist < cutoff:
                    # Add edge i -> j and j -> i (undirected)
                    edge_indices.append([i, j])
                    edge_indices.append([j, i])
                    
                    # Edge features: distance and maybe species pair
                    # Simple feature: normalized distance
                    edge_features.append([dist / cutoff])
                    edge_features.append([dist / cutoff])

        # Convert to numpy arrays
        node_features_np = np.array(node_features, dtype=np.float32)
        edge_indices_np = np.array(edge_indices, dtype=np.int64)
        edge_features_np = np.array(edge_features, dtype=np.float32) if edge_features else np.zeros((0, 1), dtype=np.float32)

        # Extract target moduli (if available in the CIF or associated metadata)
        # Since the task is parsing CIFs, we assume elastic moduli might be in
        # the CIF's metadata or we default to None if not present.
        # In a real pipeline, this would be joined from the download step.
        # For this task, we extract what we can or set to None.
        target_moduli = None
        
        # Attempt to find elastic data in CIF's site properties or metadata
        # This is highly format-dependent. We'll check for common keys.
        if hasattr(structure, 'properties'):
            for key in ['elastic_tensor', 'youngs_modulus', 'shear_modulus', 'poisson_ratio']:
                if key in structure.properties:
                    val = structure.properties[key]
                    if isinstance(val, (list, tuple, np.ndarray)):
                        target_moduli = np.array(val, dtype=np.float32)
                    else:
                        target_moduli = np.array([val], dtype=np.float32)
                    break
        
        # Create MaterialGraph
        graph = MaterialGraph(
            node_features=node_features_np,
            edge_indices=edge_indices_np,
            edge_features=edge_features_np,
            target_moduli=target_moduli,
            source_id=str(cif_path.stem),
            source_path=str(cif_path)
        )

        return graph

    except Exception as e:
        logger.error(f"Error processing structure from {cif_path}: {e}")
        return None


def parse_cif_directory(directory: Path, recursive: bool = True) -> List[MaterialGraph]:
    """
    Parses all CIF files in a directory into a list of MaterialGraph objects.
    Handles missing fields and parsing errors gracefully by skipping invalid files.
    """
    graphs = []
    pattern = "**/*.cif" if recursive else "*.cif"
    cif_files = list(directory.glob(pattern))

    if not cif_files:
        logger.warning(f"No CIF files found in {directory}")
        return graphs

    logger.info(f"Found {len(cif_files)} CIF files to parse.")

    for i, cif_path in enumerate(cif_files):
        try:
            graph = parse_cif_file(cif_path)
            if graph is not None:
                graphs.append(graph)
        except Exception as e:
            logger.error(f"Unexpected error processing {cif_path}: {e}")
            continue

    logger.info(f"Successfully parsed {len(graphs)} out of {len(cif_files)} CIF files.")
    return graphs


def main():
    """
    CLI entry point for parsing CIFs.
    Expects --input (path to CIF or directory) and --output (path to JSON summary).
    """
    import argparse

    parser = argparse.ArgumentParser(description="Parse CIF files into MaterialGraph objects and save summary.")
    parser.add_argument("--input", type=str, required=True, help="Path to a CIF file or directory containing CIFs.")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON summary file.")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if input_path.is_file():
        if input_path.suffix.lower() != '.cif':
            logger.error(f"Input file {input_path} is not a CIF file.")
            sys.exit(1)
        graphs = [parse_cif_file(input_path)]
        graphs = [g for g in graphs if g is not None]
    elif input_path.is_dir():
        graphs = parse_cif_directory(input_path)
    else:
        logger.error(f"Input path {input_path} is neither a file nor a directory.")
        sys.exit(1)

    if not graphs:
        logger.warning("No graphs were generated. Writing empty summary.")
        summary = {
            "total_files": 0,
            "parsed_files": 0,
            "graphs": []
        }
    else:
        # Serialize graphs to a JSON-serializable format
        # MaterialGraph has numpy arrays, so we need to convert them
        serializable_graphs = []
        for g in graphs:
            serializable_graphs.append({
                "source_id": g.source_id,
                "source_path": g.source_path,
                "num_nodes": len(g.node_features),
                "num_edges": len(g.edge_indices) // 2, # edge_indices are directed pairs
                "node_features_shape": list(g.node_features.shape),
                "edge_features_shape": list(g.edge_features.shape),
                "target_moduli": g.target_moduli.tolist() if g.target_moduli is not None else None
            })

        summary = {
            "total_files": len(cif_files) if input_path.is_dir() else 1,
            "parsed_files": len(graphs),
            "graphs": serializable_graphs
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Summary written to {output_path}")


if __name__ == "__main__":
    import sys
    main()

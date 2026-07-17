"""CIF Parser for 2D materials.

Converts CIF files to MaterialGraph objects using pymatgen.
Extracts node/edge features for GNN input.
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

try:
    from pymatgen.core import Structure
    from pymatgen.analysis.graphs import StructureGraph
    from pymatgen.analysis.ewald import EwaldSummation
except ImportError:
    Structure = None
    StructureGraph = None
    EwaldSummation = None
    logging.getLogger(__name__).warning("pymatgen not installed. CIF parsing disabled.")

from data_models.material_graph import MaterialGraph

logger = logging.getLogger(__name__)

def parse_cif_file(cif_path: Path) -> Optional[MaterialGraph]:
    """Parse a single CIF file into a MaterialGraph.

    Args:
        cif_path: Path to the CIF file.

    Returns:
        MaterialGraph object or None if parsing fails.
    """
    if Structure is None:
        logger.error("pymatgen not available. Cannot parse CIF.")
        return None

    try:
        structure = Structure.from_file(str(cif_path))
        
        # Check if 2D (simplified: check for vacuum in c-direction)
        # In real implementation, use pymatgen's 2D detection
        is_2d = structure.lattice.c > 15.0  # Heuristic: large c-axis implies vacuum

        if not is_2d:
            logger.debug(f"Skipping non-2D structure: {cif_path}")
            return None

        # Build graph
        # Use DistanceGraph or MinimumDistanceNN
        try:
            s_graph = StructureGraph.with_local_env_strategy(structure, "MinimumDistanceNN")
        except Exception as e:
            logger.warning(f"Failed to build graph for {cif_path}: {e}")
            return None

        # Extract nodes (atoms)
        nodes = []
        for site in structure:
            nodes.append({
                'element': site.species_string,
                'x': site.frac_coords[0],
                'y': site.frac_coords[1],
                'z': site.frac_coords[2],
                'atomic_number': site.specie.number
            })

        # Extract edges (bonds)
        edges = []
        edge_index = []
        for edge in s_graph.graph.edges(data=True):
            src, dst = edge[0], edge[1]
            # Get indices
            src_idx = structure.sites.index(next(s for s in structure if s.species_string == structure[src].species_string and abs(s.frac_coords[0]-structure[src].frac_coords[0])<0.01))
            dst_idx = structure.sites.index(next(s for s in structure if s.species_string == structure[dst].species_string and abs(s.frac_coords[0]-structure[dst].frac_coords[0])<0.01))
            # Simplified: just use edge list from graph
            # In real code, map structure graph edges to indices properly
            edges.append({
                'src': src,
                'dst': dst,
                'distance': edge[2].get('bond_length', 0.0)
            })
            edge_index.append([src, dst])

        # Extract composition
        composition = {str(spec): count for spec, count in structure.composition.items()}

        # Placeholder for elastic tensor (would be fetched from DB in real pipeline)
        target_tensor = None

        return MaterialGraph(
            material_id=cif_path.stem,
            composition=composition,
            nodes=nodes,
            edges=edges,
            edge_index=np.array(edge_index).T if edge_index else np.zeros((2, 0), dtype=int),
            target_tensor=target_tensor,
            family=None,
            space_group=structure.get_space_group_info()[1] if structure else None
        )

    except Exception as e:
        logger.error(f"Error parsing {cif_path}: {e}")
        return None

def parse_cif_directory(cif_dir: Path) -> List[MaterialGraph]:
    """Parse all CIF files in a directory."""
    graphs = []
    for cif_file in cif_dir.glob("*.cif"):
        g = parse_cif_file(cif_file)
        if g:
            graphs.append(g)
    return graphs

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Path to CIF file or directory')
    parser.add_argument('--output', required=True, help='Output JSON file')
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if input_path.is_file():
        graphs = [g for g in [parse_cif_file(input_path)] if g]
    else:
        graphs = parse_cif_directory(input_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump([g.to_dict() for g in graphs], f, indent=2)
    print(f"Parsed {len(graphs)} graphs -> {output_path}")

if __name__ == '__main__':
    main()

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
    from pymatgen.analysis.graphs import StructureGraph, MinimumDistanceNN
    from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
except ImportError:
    Structure = None
    StructureGraph = None
    MinimumDistanceNN = None
    SpacegroupAnalyzer = None
    logging.getLogger(__name__).warning("pymatgen not installed. CIF parsing disabled.")

from data_models.material_graph import MaterialGraph

logger = logging.getLogger(__name__)

# Constants for feature extraction
ATOMIC_NUMBERS = {
    "H": 1, "He": 2, "Li": 3, "Be": 4, "B": 5, "C": 6, "N": 7, "O": 8,
    "F": 9, "Ne": 10, "Na": 11, "Mg": 12, "Al": 13, "Si": 14, "P": 15,
    "S": 16, "Cl": 17, "Ar": 18, "K": 19, "Ca": 20, "Sc": 21, "Ti": 22,
    "V": 23, "Cr": 24, "Mn": 25, "Fe": 26, "Co": 27, "Ni": 28, "Cu": 29,
    "Zn": 30, "Ga": 31, "Ge": 32, "As": 33, "Se": 34, "Br": 35, "Kr": 36,
    "Rb": 37, "Sr": 38, "Y": 39, "Zr": 40, "Nb": 41, "Mo": 42, "Tc": 43,
    "Ru": 44, "Rh": 45, "Pd": 46, "Ag": 47, "Cd": 48, "In": 49, "Sn": 50,
    "Sb": 51, "Te": 52, "I": 53, "Xe": 54, "Cs": 55, "Ba": 56, "La": 57,
    "Ce": 58, "Pr": 59, "Nd": 60, "Pm": 61, "Sm": 62, "Eu": 63, "Gd": 64,
    "Tb": 65, "Dy": 66, "Ho": 67, "Er": 68, "Tm": 69, "Yb": 70, "Lu": 71,
    "Hf": 72, "Ta": 73, "W": 74, "Re": 75, "Os": 76, "Ir": 77, "Pt": 78,
    "Au": 79, "Hg": 80, "Tl": 81, "Pb": 82, "Bi": 83, "Po": 84, "At": 85,
    "Rn": 86, "Fr": 87, "Ra": 88, "Ac": 89, "Th": 90, "Pa": 91, "U": 92,
    "Np": 93, "Pu": 94, "Am": 95, "Cm": 96, "Bk": 97, "Cf": 98, "Es": 99,
    "Fm": 100, "Md": 101, "No": 102, "Lr": 103, "Rf": 104, "Db": 105,
    "Sg": 106, "Bh": 107, "Hs": 108, "Mt": 109, "Ds": 110, "Rg": 111,
    "Cn": 112, "Nh": 113, "Fl": 114, "Mc": 115, "Lv": 116, "Ts": 117,
    "Og": 118
}

def _is_2d_structure(structure: Structure, vacuum_threshold: float = 15.0) -> bool:
    """
    Heuristic check for 2D material based on vacuum layer in c-direction.
    
    Args:
        structure: Pymatgen Structure object.
        vacuum_threshold: Minimum c-axis length (Angstrom) to consider as vacuum.
        
    Returns:
        True if the structure is likely 2D (has vacuum layer).
    """
    if structure is None:
        return False
    # Check if c-axis is significantly larger than a and b, implying vacuum
    a, b, c = structure.lattice.a, structure.lattice.b, structure.lattice.c
    # If c is much larger than a and b, it's likely a slab with vacuum
    if c > vacuum_threshold and (c > 1.5 * max(a, b)):
        return True
    return False

def _extract_nodes(structure: Structure) -> List[Dict[str, Any]]:
    """
    Extract node features from a pymatgen Structure.
    
    Args:
        structure: Pymatgen Structure object.
        
    Returns:
        List of node feature dictionaries.
    """
    nodes = []
    for site in structure:
        element = site.species_string
        atomic_number = site.specie.number
        nodes.append({
            'element': element,
            'x': site.frac_coords[0],
            'y': site.frac_coords[1],
            'z': site.frac_coords[2],
            'atomic_number': atomic_number
        })
    return nodes

def _extract_edges(structure: Structure, s_graph: StructureGraph) -> Tuple[List[Dict[str, Any]], np.ndarray]:
    """
    Extract edge features and edge index from a StructureGraph.
    
    Args:
        structure: Pymatgen Structure object.
        s_graph: StructureGraph object.
        
    Returns:
        Tuple of (list of edge dicts, numpy array of edge indices).
    """
    edges = []
    edge_indices = []
    
    # Build a mapping from site coordinates to indices for lookup
    # Since sites are ordered, we can use index directly if we match properly
    site_map = {}
    for idx, site in enumerate(structure.sites):
        key = (tuple(site.frac_coords), site.species_string)
        site_map[key] = idx
    
    for edge in s_graph.graph.edges(data=True):
        src_site, dst_site = edge[0], edge[1]
        # Find indices in the structure
        # We need to find the index of the site in the structure list that matches
        # This is tricky because pymatgen graph sites might be referenced differently
        # We'll use the site's properties to find the index
        
        # Find src index
        src_idx = -1
        dst_idx = -1
        
        for i, site in enumerate(structure.sites):
            if site.frac_coords[0] == src_site.frac_coords[0] and \
               site.frac_coords[1] == src_site.frac_coords[1] and \
               site.frac_coords[2] == src_site.frac_coords[2] and \
               site.species_string == src_site.species_string:
                src_idx = i
                break
        
        for i, site in enumerate(structure.sites):
            if site.frac_coords[0] == dst_site.frac_coords[0] and \
               site.frac_coords[1] == dst_site.frac_coords[1] and \
               site.frac_coords[2] == dst_site.frac_coords[2] and \
               site.species_string == dst_site.species_string:
                dst_idx = i
                break
        
        if src_idx == -1 or dst_idx == -1:
            logger.warning(f"Could not map edge sites to structure indices for {src_site} -> {dst_site}")
            continue
            
        distance = edge[2].get('bond_length', 0.0)
        edges.append({
            'src': src_idx,
            'dst': dst_idx,
            'distance': float(distance)
        })
        edge_indices.append([src_idx, dst_idx])
    
    edge_array = np.array(edge_indices).T if edge_indices else np.zeros((2, 0), dtype=int)
    return edges, edge_array

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
        is_2d = _is_2d_structure(structure)

        if not is_2d:
            logger.debug(f"Skipping non-2D structure: {cif_path}")
            return None

        # Build graph using MinimumDistanceNN
        try:
            s_graph = StructureGraph.with_local_env_strategy(structure, "MinimumDistanceNN")
        except Exception as e:
            logger.warning(f"Failed to build graph for {cif_path}: {e}")
            return None

        # Extract nodes (atoms)
        nodes = _extract_nodes(structure)

        # Extract edges (bonds)
        edges, edge_index = _extract_edges(structure, s_graph)

        # Extract composition
        composition = {str(spec): count for spec, count in structure.composition.items()}

        # Placeholder for elastic tensor (would be fetched from DB in real pipeline)
        # In the full pipeline, this would be injected by the download/filter stage
        target_tensor = None

        # Get space group info
        try:
            analyzer = SpacegroupAnalyzer(structure)
            space_group = analyzer.get_space_group_symbol()
        except Exception:
            space_group = None

        return MaterialGraph(
            material_id=cif_path.stem,
            composition=composition,
            nodes=nodes,
            edges=edges,
            edge_index=edge_index,
            target_tensor=target_tensor,
            family=None,
            space_group=space_group
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
    parser = argparse.ArgumentParser(description="Parse CIF files to MaterialGraph JSON")
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

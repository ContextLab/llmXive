import os
import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from pymatgen.core import Structure
from pymatgen.analysis.bond_determiner import get_bond_orders_from_structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
import networkx as nx

from config import get_config
from utils import setup_logging

# Configure logging
logger = setup_logging("construct_network", level=logging.INFO)

# Constants
COVALENT_RADII = {
    'H': 0.31, 'He': 0.28, 'Li': 1.28, 'Be': 0.96, 'B': 0.84, 'C': 0.76,
    'N': 0.71, 'O': 0.66, 'F': 0.57, 'Ne': 0.58, 'Na': 1.66, 'Mg': 1.41,
    'Al': 1.21, 'Si': 1.11, 'P': 1.07, 'S': 1.05, 'Cl': 1.02, 'Ar': 1.06,
    'K': 2.03, 'Ca': 1.74, 'Sc': 1.44, 'Ti': 1.36, 'V': 1.25, 'Cr': 1.27,
    'Mn': 1.39, 'Fe': 1.25, 'Co': 1.26, 'Ni': 1.21, 'Cu': 1.38, 'Zn': 1.31,
    'Ga': 1.26, 'Ge': 1.22, 'As': 1.19, 'Se': 1.20, 'Br': 1.20, 'Kr': 1.16,
    'Rb': 2.20, 'Sr': 1.92, 'Y': 1.62, 'Zr': 1.48, 'Nb': 1.37, 'Mo': 1.45,
    'Tc': 1.56, 'Ru': 1.26, 'Rh': 1.35, 'Pd': 1.31, 'Ag': 1.53, 'Cd': 1.48,
    'In': 1.44, 'Sn': 1.41, 'Sb': 1.38, 'Te': 1.35, 'I': 1.39, 'Xe': 1.40,
    'Cs': 2.44, 'Ba': 1.98, 'La': 1.69, 'Ce': 1.65, 'Pr': 1.65, 'Nd': 1.64,
    'Pm': 1.63, 'Sm': 1.62, 'Eu': 1.60, 'Gd': 1.61, 'Tb': 1.59, 'Dy': 1.57,
    'Ho': 1.56, 'Er': 1.55, 'Tm': 1.54, 'Yb': 1.53, 'Lu': 1.52, 'Hf': 1.50,
    'Ta': 1.38, 'W': 1.46, 'Re': 1.59, 'Os': 1.28, 'Ir': 1.37, 'Pt': 1.39,
    'Au': 1.44, 'Hg': 1.49, 'Tl': 1.48, 'Pb': 1.47, 'Bi': 1.46, 'Po': 1.48,
    'At': 1.40, 'Rn': 1.34
}

# Tolerance for covalent radius summation (empirically determined)
BOND_TOLERANCE = 0.45

# Fallback distance cutoffs (in Angstroms) for disconnected graphs
FALLBACK_CUTOFFS = [3.0, 3.5, 4.0, 4.5]

def get_element_covalent_radius(element_symbol: str) -> float:
    """
    Retrieve the covalent radius for a given element symbol.
    Returns a default value if the element is not in the dictionary.
    """
    return COVALENT_RADII.get(element_symbol, 1.5)  # Default fallback radius

def detect_bonds_covalent(structure: Structure) -> List[Tuple[int, int]]:
    """
    Detect bonds based on the sum of covalent radii + tolerance.
    Returns a list of (atom_index_i, atom_index_j) tuples.
    """
    bonds = []
    for i in range(len(structure)):
        for j in range(i + 1, len(structure)):
            dist = structure.get_distance(i, j)
            r_i = get_element_covalent_radius(structure[i].species_string)
            r_j = get_element_covalent_radius(structure[j].species_string)
            threshold = r_i + r_j + BOND_TOLERANCE
            if dist <= threshold:
                bonds.append((i, j))
    return bonds

def detect_bonds_fallback(structure: Structure) -> List[Tuple[int, int]]:
    """
    Detect bonds using progressive distance cutoffs if the covalent method fails
    to produce a connected graph or any edges.
    """
    for cutoff in FALLBACK_CUTOFFS:
        bonds = []
        for i in range(len(structure)):
            for j in range(i + 1, len(structure)):
                dist = structure.get_distance(i, j)
                if dist <= cutoff:
                    bonds.append((i, j))
        if len(bonds) > 0:
            logger.info(f"Using fallback cutoff {cutoff} Å, found {len(bonds)} bonds.")
            return bonds
    return []

def construct_network_from_structure(structure: Structure) -> Optional[nx.Graph]:
    """
    Construct a networkx Graph from a pymatgen Structure.
    Returns None if the graph is invalid (less than 2 nodes or 0 edges).
    """
    # Create graph
    G = nx.Graph()
    for i, site in enumerate(structure):
        G.add_node(i, species=site.species_string, coords=site.coords)

    # Attempt covalent bond detection
    bonds = detect_bonds_covalent(structure)

    # If no bonds found or graph is disconnected, try fallbacks
    if len(bonds) == 0:
        logger.warning("No bonds found via covalent radii. Attempting fallback detection.")
        bonds = detect_bonds_fallback(structure)

    if len(bonds) == 0:
        logger.warning("No bonds found after all fallback attempts. Skipping structure.")
        return None

    for i, j in bonds:
        G.add_edge(i, j)

    # T012 Validation: Ensure every graph has >= 2 nodes and >= 1 edge
    if G.number_of_nodes() < 2:
        logger.warning(f"Graph has only {G.number_of_nodes()} node(s). Skipping structure.")
        return None

    if G.number_of_edges() < 1:
        logger.warning(f"Graph has 0 edges despite having {G.number_of_nodes()} nodes. Skipping structure.")
        return None

    return G

def process_cif_file(cif_path: Path) -> Optional[Tuple[nx.Graph, str]]:
    """
    Parse a CIF file and construct a network graph.
    Returns (graph, material_id) or None if construction fails.
    """
    try:
        structure = Structure.from_file(cif_path)
        material_id = structure.composition.reduced_formula
        graph = construct_network_from_structure(structure)
        if graph is None:
            return None
        return graph, material_id
    except Exception as e:
        logger.error(f"Error processing {cif_path}: {e}")
        return None

def save_graph_to_pickle(graph: nx.Graph, material_id: str, output_dir: Path) -> Path:
    """
    Save a networkx graph to a pickle file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    # Sanitize material_id for filename
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in material_id)
    filepath = output_dir / f"{safe_id}.pkl"
    with open(filepath, 'wb') as f:
        pickle.dump(graph, f)
    return filepath

def build_network_manifest(graphs_info: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Build a manifest JSON file listing all processed graphs.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(graphs_info, f, indent=2)

def main():
    """
    Main entry point for constructing networks from CIF files.
    """
    config = get_config()
    cif_dir = Path(config['data_raw_cif'])
    output_dir = Path(config['data_processed_networks'])
    manifest_path = Path(config['data_processed_networks']) / "network_manifest.json"

    cif_files = list(cif_dir.glob("*.cif"))
    if not cif_files:
        logger.error(f"No CIF files found in {cif_dir}")
        return

    logger.info(f"Found {len(cif_files)} CIF files to process.")
    graphs_info = []
    skipped_count = 0

    for cif_file in cif_files:
        result = process_cif_file(cif_file)
        if result is None:
            skipped_count += 1
            continue

        graph, material_id = result
        save_path = save_graph_to_pickle(graph, material_id, output_dir)
        
        graphs_info.append({
            "material_id": material_id,
            "file_path": str(save_path),
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges()
        })
        logger.info(f"Processed {material_id}: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges.")

    if graphs_info:
        build_network_manifest(graphs_info, manifest_path)
        logger.info(f"Manifest saved to {manifest_path}")
    else:
        logger.warning("No graphs were successfully constructed.")

    logger.info(f"Processing complete. Skipped {skipped_count} materials due to validation failures.")

if __name__ == "__main__":
    main()
"""
Network construction module.
Parses CIF files and constructs atomic network graphs.
"""

import os
import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import networkx as nx
from pymatgen.core import Structure
from pymatgen.analysis.structure_analyzer import bond_order
from pymatgen.analysis.local_env import CovalentBond

# Constants
COVALENT_RADIUS_TOLERANCE = 0.45  # Angstrom
FALLBACK_CUTOFFS = [3.0, 3.5, 4.0, 4.5]

# Element covalent radii (simplified lookup)
COVALENT_RADII = {
    "H": 0.37, "He": 0.32,
    "Li": 1.34, "Be": 0.90, "B": 0.82, "C": 0.77, "N": 0.75, "O": 0.73, "F": 0.71, "Ne": 0.69,
    "Na": 1.54, "Mg": 1.30, "Al": 1.18, "Si": 1.11, "P": 1.07, "S": 1.02, "Cl": 0.99, "Ar": 0.97,
    "K": 2.03, "Ca": 1.76, "Sc": 1.60, "Ti": 1.47, "V": 1.34, "Cr": 1.27, "Mn": 1.39, "Fe": 1.25, "Co": 1.26, "Ni": 1.24, "Cu": 1.32, "Zn": 1.31, "Ga": 1.26, "Ge": 1.22, "As": 1.19, "Se": 1.16, "Br": 1.14, "Kr": 1.10,
    "Rb": 2.20, "Sr": 1.95, "Y": 1.80, "Zr": 1.60, "Nb": 1.46, "Mo": 1.39, "Tc": 1.36, "Ru": 1.34, "Rh": 1.34, "Pd": 1.37, "Ag": 1.44, "Cd": 1.44, "In": 1.44, "Sn": 1.41, "Sb": 1.38, "Te": 1.35, "I": 1.33, "Xe": 1.30,
    "Cs": 2.35, "Ba": 1.98, "La": 1.87, "Ce": 1.82, "Pr": 1.82, "Nd": 1.81, "Pm": 1.83, "Sm": 1.80, "Eu": 1.99, "Gd": 1.80, "Tb": 1.77, "Dy": 1.75, "Ho": 1.75, "Er": 1.74, "Tm": 1.74, "Yb": 1.74, "Lu": 1.73,
    "Hf": 1.56, "Ta": 1.46, "W": 1.37, "Re": 1.37, "Os": 1.35, "Ir": 1.36, "Pt": 1.39, "Au": 1.44, "Hg": 1.49, "Tl": 1.48, "Pb": 1.47, "Bi": 1.46, "Po": 1.45, "At": 1.45, "Rn": 1.45
}


def setup_logger() -> logging.Logger:
    """Set up and return the logger."""
    logger = logging.getLogger("construct_network")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def get_element_covalent_radius(element: str) -> float:
    """Get covalent radius for an element."""
    return COVALENT_RADII.get(element, 1.5)  # Default fallback


def detect_bonds_covalent(structure: Structure) -> List[Tuple[int, int]]:
    """Detect bonds using covalent radii summation."""
    bonds = []
    for i, site1 in enumerate(structure.sites):
        for j, site2 in enumerate(structure.sites):
            if i >= j:
                continue
            dist = structure.get_distance(i, j)
            r1 = get_element_covalent_radius(site1.specie.symbol)
            r2 = get_element_covalent_radius(site2.specie.symbol)
            threshold = r1 + r2 + COVALENT_RADIUS_TOLERANCE
            if dist <= threshold:
                bonds.append((i, j))
    return bonds


def detect_bonds_fallback(structure: Structure) -> List[Tuple[int, int]]:
    """Detect bonds using progressive distance cutoffs."""
    for cutoff in FALLBACK_CUTOFFS:
        bonds = []
        for i, site1 in enumerate(structure.sites):
            for j, site2 in enumerate(structure.sites):
                if i >= j:
                    continue
                dist = structure.get_distance(i, j)
                if dist <= cutoff:
                    bonds.append((i, j))
        if len(bonds) > 0:
            return bonds
    return []


def construct_network_from_structure(structure: Structure) -> Optional[nx.Graph]:
    """Construct a networkx Graph from a pymatgen Structure."""
    bonds = detect_bonds_covalent(structure)
    
    # Fallback if no bonds detected
    if len(bonds) == 0:
        bonds = detect_bonds_fallback(structure)

    if len(bonds) == 0:
        return None

    G = nx.Graph()
    for i, site in enumerate(structure.sites):
        G.add_node(i, element=site.specie.symbol, coords=site.coords)
    G.add_edges_from(bonds)

    return G


def process_cif_file(cif_path: Path) -> Optional[Tuple[nx.Graph, str]]:
    """Parse a CIF file and construct a network."""
    try:
        structure = Structure.from_file(str(cif_path))
        G = construct_network_from_structure(structure)
        if G is None:
            return None
        # Basic validation
        if G.number_of_nodes() < 2 or G.number_of_edges() < 1:
            return None
        return (G, structure.formula)
    except Exception as e:
        logging.getLogger("construct_network").error(f"Failed to process {cif_path}: {e}")
        return None


def save_graph_to_pickle(graph: nx.Graph, output_path: Path) -> None:
    """Save a graph to a pickle file."""
    with open(output_path, "wb") as f:
        pickle.dump(graph, f)


def build_network_manifest(graphs_info: List[Dict[str, Any]], output_path: Path) -> None:
    """Build a manifest JSON for all constructed networks."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(graphs_info, f, indent=2)


def main() -> None:
    """Main entry point for network construction."""
    logger = setup_logger()
    logger.info("Starting network construction...")

    input_dir = Path("data/raw/cif")
    output_dir = Path("data/processed/networks")
    manifest_path = Path("data/processed/network_manifest.json")

    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    cif_files = list(input_dir.glob("*.cif"))
    logger.info(f"Found {len(cif_files)} CIF files.")

    graphs_info = []
    success_count = 0
    skip_count = 0

    for cif_file in cif_files:
        result = process_cif_file(cif_file)
        if result is None:
            logger.warning(f"Skipped {cif_file.name}: No valid network constructed.")
            skip_count += 1
            continue

        graph, formula = result
        graph_id = cif_file.stem
        output_path = output_dir / f"{graph_id}.pkl"
        
        save_graph_to_pickle(graph, output_path)
        
        info = {
            "id": graph_id,
            "formula": formula,
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
            "path": str(output_path)
        }
        graphs_info.append(info)
        success_count += 1

    build_network_manifest(graphs_info, manifest_path)
    logger.info(f"Built manifest at {manifest_path}")
    logger.info(f"Success: {success_count}, Skipped: {skip_count}")


if __name__ == "__main__":
    main()

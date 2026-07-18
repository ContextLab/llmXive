import os
import json
import logging
import pickle
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from pymatgen.core import Structure
from pymatgen.analysis.bond_valence import BVAnalyzer
from pymatgen.analysis.local_env import VoronoiNN
import networkx as nx
import numpy as np

# Import shared utilities and config
from utils import setup_logging, pin_seed, retry_with_exponential_backoff
from config import Config, get_config

# Configure logger
logger = setup_logging("network_logger", "results/network_construction.log")
config = get_config()

# Constants
COVALENT_RADII_TOLERANCE = 0.4  # Angstroms tolerance for covalent bond detection
FALLBACK_CUTOFFS = [1.0, 1.2, 1.5, 2.0]  # Progressive distance cutoffs in Angstroms

def get_element_covalent_radius(element: str) -> float:
    """
    Retrieve the covalent radius for a given element symbol.
    Uses a fallback dictionary if pymatgen's periodic table lookup fails.
    """
    try:
        from pymatgen.core.periodic_table import Element
        el = Element(element)
        return el.covalent_radius or 1.0
    except Exception:
        # Fallback dictionary for common elements
        fallback_radii = {
            'H': 0.31, 'He': 0.28, 'Li': 1.28, 'Be': 0.96, 'B': 0.84, 'C': 0.76,
            'N': 0.71, 'O': 0.66, 'F': 0.57, 'Ne': 0.58, 'Na': 1.66, 'Mg': 1.41,
            'Al': 1.21, 'Si': 1.11, 'P': 1.07, 'S': 1.05, 'Cl': 1.02, 'Ar': 1.06,
            'K': 2.03, 'Ca': 1.74, 'Sc': 1.44, 'Ti': 1.36, 'V': 1.25, 'Cr': 1.27,
            'Mn': 1.39, 'Fe': 1.25, 'Co': 1.26, 'Ni': 1.21, 'Cu': 1.38, 'Zn': 1.31,
            'Ga': 1.26, 'Ge': 1.22, 'As': 1.19, 'Se': 1.20, 'Br': 1.20, 'Kr': 1.16,
            'Rb': 2.20, 'Sr': 1.92, 'Y': 1.62, 'Zr': 1.48, 'Nb': 1.37, 'Mo': 1.45,
            'Tc': 1.56, 'Ru': 1.26, 'Rh': 1.35, 'Pd': 1.31, 'Ag': 1.53, 'Cd': 1.44,
            'In': 1.44, 'Sn': 1.41, 'Sb': 1.38, 'Te': 1.35, 'I': 1.39, 'Xe': 1.40,
            'Cs': 2.44, 'Ba': 1.98, 'La': 1.69, 'Ce': 1.85, 'Pr': 1.85, 'Nd': 1.85,
            'Pm': 1.85, 'Sm': 1.85, 'Eu': 1.85, 'Gd': 1.85, 'Tb': 1.85, 'Dy': 1.85,
            'Ho': 1.85, 'Er': 1.85, 'Tm': 1.85, 'Yb': 1.85, 'Lu': 1.85, 'Hf': 1.44,
            'Ta': 1.34, 'W': 1.30, 'Re': 1.35, 'Os': 1.28, 'Ir': 1.36, 'Pt': 1.36,
            'Au': 1.36, 'Hg': 1.32, 'Tl': 1.45, 'Pb': 1.46, 'Bi': 1.48, 'Po': 1.40,
            'At': 1.47, 'Rn': 1.45
        }
        return fallback_radii.get(element, 1.0)

def detect_bonds_covalent(structure: Structure) -> List[Tuple[int, int, float]]:
    """
    Detect bonds based on covalent radii summation with a tolerance threshold.
    Returns a list of tuples: (index_i, index_j, distance).
    """
    bonds = []
    coords = structure.frac_coords
    lattice = structure.lattice
    elements = [site.species_string for site in structure]
    n_atoms = len(structure)

    for i in range(n_atoms):
        for j in range(i + 1, n_atoms):
            dist = structure.get_distance(i, j)
            r_i = get_element_covalent_radius(elements[i])
            r_j = get_element_covalent_radius(elements[j])
            cutoff = r_i + r_j + COVALENT_RADII_TOLERANCE

            if dist <= cutoff:
                bonds.append((i, j, dist))

    return bonds

def detect_bonds_fallback(structure: Structure, max_cutoff: float) -> List[Tuple[int, int, float]]:
    """
    Fallback bond detection using a simple distance cutoff.
    Iterates through pairs and includes edges if distance <= max_cutoff.
    """
    bonds = []
    n_atoms = len(structure)

    for i in range(n_atoms):
        for j in range(i + 1, n_atoms):
            dist = structure.get_distance(i, j)
            if dist <= max_cutoff:
                bonds.append((i, j, dist))

    return bonds

def construct_network_from_structure(structure: Structure) -> Optional[nx.Graph]:
    """
    Construct a networkx Graph from a pymatgen Structure.
    Implements progressive fallback bond detection for disconnected graphs.
    Returns None if no edges can be formed even after fallbacks.
    """
    # Primary method: Covalent radii
    bonds = detect_bonds_covalent(structure)

    if not bonds:
        logger.warning(f"Covalent bond detection yielded 0 edges. Attempting fallbacks.")
        for cutoff in FALLBACK_CUTOFFS:
            bonds = detect_bonds_fallback(structure, cutoff)
            if bonds:
                logger.info(f"Fallback cutoff {cutoff} Å yielded {len(bonds)} edges.")
                break

    if not bonds:
        logger.error(f"Material {structure.formula} resulted in a disconnected graph (0 edges) after all fallbacks. Skipping.")
        return None

    G = nx.Graph()
    # Add nodes with atomic number and element symbol
    for idx, site in enumerate(structure):
        G.add_node(idx, element=site.species_string, atomic_number=site.species.elements[0].number, position=site.coords.tolist())

    # Add edges with distance
    for i, j, dist in bonds:
        G.add_edge(i, j, distance=dist)

    return G

def process_cif_file(cif_path: Path) -> Optional[Tuple[nx.Graph, str]]:
    """
    Parse a CIF file and construct the corresponding network graph.
    Returns (graph, material_id) or None if construction fails.
    """
    try:
        structure = Structure.from_file(str(cif_path))
        graph = construct_network_from_structure(structure)
        if graph is None:
            return None
        
        # Extract a simple material ID from filename or structure
        material_id = cif_path.stem
        return graph, material_id
    except Exception as e:
        logger.error(f"Failed to process CIF {cif_path}: {e}")
        return None

def save_graph_to_pickle(graph: nx.Graph, output_path: Path, material_id: str) -> str:
    """
    Save a graph to a pickle file and compute its SHA-256 checksum.
    """
    with open(output_path, 'wb') as f:
        pickle.dump(graph, f)
    
    # Compute checksum
    sha256_hash = hashlib.sha256()
    with open(output_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    checksum = sha256_hash.hexdigest()
    logger.info(f"Saved graph for {material_id} to {output_path} (Checksum: {checksum})")
    return checksum

def build_network_manifest(graphs_data: List[Dict[str, Any]], output_path: Path):
    """
    Build a manifest JSON file recording all processed graphs, their checksums,
    and derivation metadata.
    """
    manifest = {
        "derivation": "CIF -> Network via covalent radii + fallback",
        "graphs": graphs_data,
        "total_processed": len(graphs_data)
    }
    
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Network manifest saved to {output_path}")

def main():
    """
    Main entry point for constructing networks from CIF files.
    Usage: python code/construct_network.py --input data/raw/cif/ --output data/processed/networks/
    """
    import argparse

    parser = argparse.ArgumentParser(description="Construct atomic networks from CIF files.")
    parser.add_argument("--input", type=str, required=True, help="Directory containing CIF files.")
    parser.add_argument("--output", type=str, required=True, help="Directory to save network graphs.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of files to process.")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    cif_files = list(input_dir.glob("*.cif"))
    if not cif_files:
        logger.error(f"No CIF files found in {input_dir}")
        return 1

    if args.limit:
        cif_files = cif_files[:args.limit]

    logger.info(f"Processing {len(cif_files)} CIF files...")
    
    graphs_data = []
    skipped_count = 0

    for cif_path in cif_files:
        result = process_cif_file(cif_path)
        if result is None:
            skipped_count += 1
            continue

        graph, material_id = result
        output_file = output_dir / f"{material_id}.pkl"
        checksum = save_graph_to_pickle(graph, output_file, material_id)

        graphs_data.append({
            "material_id": material_id,
            "source_file": str(cif_path),
            "output_file": str(output_file),
            "checksum": checksum,
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges()
        })

    # Build manifest
    manifest_path = output_dir / "manifest.json"
    build_network_manifest(graphs_data, manifest_path)

    logger.info(f"Construction complete. Processed: {len(graphs_data)}, Skipped: {skipped_count}")
    return 0

if __name__ == "__main__":
    exit(main())
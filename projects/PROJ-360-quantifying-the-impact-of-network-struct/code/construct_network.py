"""
code/construct_network.py

Constructs atomic network graphs from CIF files using pymatgen.
Implements bond detection via covalent radii summation with fallback mechanisms.
Includes strict validation: graphs must have >= 2 nodes and >= 1 edge.
"""

import os
import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import networkx as nx
from pymatgen.core import Structure
from pymatgen.analysis.bond_valence import BVAnalyzer
from pymatgen.analysis.structure_analyzer import get_bonding_structure

from utils import setup_logging, pin_seed
from config import get_config

# Constants
COVALENT_RADIUS_TOLERANCE = 0.45  # Angstroms tolerance for bond detection
FALLBACK_CUTOFFS = [3.0, 3.5, 4.0]  # Angstroms for progressive fallback

# Setup logger
logger = setup_logging("construct_network", "data/logs/construct_network.log")

def get_element_covalent_radius(element_symbol: str) -> float:
    """
    Retrieve the covalent radius for a given element symbol.
    Uses pymatgen's Element data if available, otherwise defaults.
    """
    try:
        from pymatgen.core import Element
        elem = Element(element_symbol)
        return elem.covalent_radius
    except (ImportError, AttributeError, ValueError):
        # Fallback dictionary for common elements if pymatgen lookup fails
        fallback_radii = {
            'H': 0.31, 'He': 0.28, 'Li': 1.28, 'Be': 0.96, 'B': 0.84, 'C': 0.76,
            'N': 0.71, 'O': 0.66, 'F': 0.57, 'Ne': 0.58, 'Na': 1.66, 'Mg': 1.41,
            'Al': 1.21, 'Si': 1.11, 'P': 1.07, 'S': 1.05, 'Cl': 1.02, 'Ar': 1.06,
            'K': 2.03, 'Ca': 1.74, 'Sc': 1.44, 'Ti': 1.36, 'V': 1.34, 'Cr': 1.27,
            'Mn': 1.26, 'Fe': 1.32, 'Co': 1.26, 'Ni': 1.24, 'Cu': 1.32, 'Zn': 1.22,
            'Ga': 1.26, 'Ge': 1.22, 'As': 1.19, 'Se': 1.20, 'Br': 1.20, 'Kr': 1.16,
            'Rb': 2.20, 'Sr': 1.92, 'Y': 1.62, 'Zr': 1.48, 'Nb': 1.37, 'Mo': 1.36,
            'Tc': 1.36, 'Ru': 1.34, 'Rh': 1.34, 'Pd': 1.37, 'Ag': 1.44, 'Cd': 1.44,
            'In': 1.42, 'Sn': 1.39, 'Sb': 1.39, 'Te': 1.38, 'I': 1.39, 'Xe': 1.40,
            'Cs': 2.44, 'Ba': 1.98, 'La': 1.69, 'Ce': 1.65, 'Pr': 1.65, 'Nd': 1.64,
            'Pm': 1.63, 'Sm': 1.62, 'Eu': 1.62, 'Gd': 1.62, 'Tb': 1.61, 'Dy': 1.61,
            'Ho': 1.60, 'Er': 1.60, 'Tm': 1.60, 'Yb': 1.60, 'Lu': 1.60, 'Hf': 1.50,
            'Ta': 1.46, 'W': 1.42, 'Re': 1.41, 'Os': 1.38, 'Ir': 1.36, 'Pt': 1.36,
            'Au': 1.36, 'Hg': 1.32, 'Tl': 1.45, 'Pb': 1.46, 'Bi': 1.48, 'Po': 1.40,
            'At': 1.40, 'Rn': 1.40
        }
        return fallback_radii.get(element_symbol, 1.5)  # Default to 1.5 Angstroms

def detect_bonds_covalent(structure: Structure) -> List[Tuple[int, int]]:
    """
    Detect bonds based on the sum of covalent radii with a tolerance.
    Returns a list of (index_i, index_j) tuples.
    """
    bonds = []
    elements = structure.species
    coords = structure.frac_coords
    lattice = structure.lattice

    # Precompute covalent radii
    radii = [get_element_covalent_radius(str(species)) for species in elements]

    # Iterate over unique pairs
    for i in range(len(elements)):
        for j in range(i + 1, len(elements)):
            dist = structure.get_distance(i, j)
            cutoff = radii[i] + radii[j] + COVALENT_RADIUS_TOLERANCE
            if dist <= cutoff:
                bonds.append((i, j))
    
    return bonds

def detect_bonds_fallback(structure: Structure) -> List[Tuple[int, int]]:
    """
    Fallback bond detection using progressive distance cutoffs.
    Returns a list of (index_i, index_j) tuples.
    """
    bonds = []
    coords = structure.frac_coords
    lattice = structure.lattice
    elements = structure.species

    for cutoff in FALLBACK_CUTOFFS:
        bonds = []
        for i in range(len(elements)):
            for j in range(i + 1, len(elements)):
                dist = structure.get_distance(i, j)
                if dist <= cutoff:
                    bonds.append((i, j))
        
        # Check if we have any bonds
        if len(bonds) > 0:
            logger.info(f"Fallback bond detection succeeded with cutoff {cutoff} Angstroms.")
            return bonds
    
    logger.warning("Fallback bond detection failed for all cutoffs.")
    return []

def construct_network_from_structure(structure: Structure, use_fallback: bool = True) -> Optional[nx.Graph]:
    """
    Construct a networkx.Graph from a pymatgen Structure.
    Validates that the graph has >= 2 nodes and >= 1 edge.
    Returns None if validation fails.
    """
    G = nx.Graph()
    
    # Add nodes (atoms)
    for i, species in enumerate(structure.species):
        G.add_node(i, element=str(species), species=species, coords=structure.frac_coords[i])
    
    # Detect bonds
    bonds = detect_bonds_covalent(structure)
    
    if not bonds and use_fallback:
        bonds = detect_bonds_fallback(structure)
    
    # Add edges
    for i, j in bonds:
        G.add_edge(i, j, distance=structure.get_distance(i, j))
    
    # --- VALIDATION LOGIC FOR T012 ---
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    
    if num_nodes < 2:
        logger.warning(f"Graph construction failed: Node count ({num_nodes}) < 2. Skipping.")
        return None
    
    if num_edges < 1:
        logger.warning(f"Graph construction failed: Edge count ({num_edges}) < 1. Skipping.")
        return None
    
    logger.info(f"Validated graph: {num_nodes} nodes, {num_edges} edges.")
    return G

def process_cif_file(cif_path: Path, output_dir: Path) -> Optional[str]:
    """
    Process a single CIF file, construct the network, validate, and save.
    Returns the relative path of the saved pickle file, or None if skipped.
    """
    try:
        structure = Structure.from_file(str(cif_path))
    except Exception as e:
        logger.error(f"Failed to parse CIF file {cif_path}: {e}")
        return None
    
    graph = construct_network_from_structure(structure)
    
    if graph is None:
        # Validation failed (T012 requirement: explicitly skip with log entry)
        return None
    
    # Generate output filename
    base_name = cif_path.stem
    output_path = output_dir / f"{base_name}.pkl"
    
    save_graph_to_pickle(graph, output_path)
    return str(output_path.relative_to(output_dir))

def save_graph_to_pickle(graph: nx.Graph, path: Path) -> None:
    """
    Save a networkx graph to a pickle file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as f:
        pickle.dump(graph, f)
    logger.debug(f"Saved graph to {path}")

def build_network_manifest(manifest_path: Path, file_paths: List[str]) -> None:
    """
    Build a manifest JSON file listing all successfully processed networks.
    """
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_data = {
        "total_processed": len(file_paths),
        "files": file_paths,
        "metadata": {
            "schema_version": "1.0",
            "generated_by": "construct_network.py"
        }
    }
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)
    logger.info(f"Network manifest saved to {manifest_path}")

def main():
    """
    Main entry point for constructing networks from CIF files.
    """
    config = get_config()
    cif_dir = Path(config.data_raw_cif_dir)
    output_dir = Path(config.data_processed_networks_dir)
    manifest_path = Path(config.data_processed_networks_dir).parent / "network_manifest.json"
    
    # Ensure directories exist
    cif_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Pin seed for determinism
    pin_seed(config.random_seed)
    
    # Get list of CIF files
    cif_files = list(cif_dir.glob("*.cif"))
    if not cif_files:
        logger.warning(f"No CIF files found in {cif_dir}")
        return
    
    logger.info(f"Found {len(cif_files)} CIF files to process.")
    
    processed_files = []
    
    for cif_file in cif_files:
        logger.info(f"Processing {cif_file.name}...")
        result = process_cif_file(cif_file, output_dir)
        if result:
            processed_files.append(result)
    
    # Build manifest
    if processed_files:
        build_network_manifest(manifest_path, processed_files)
        logger.info(f"Successfully processed {len(processed_files)} files.")
    else:
        logger.warning("No files were successfully processed.")
        # Create empty manifest
        build_network_manifest(manifest_path, [])

if __name__ == "__main__":
    main()
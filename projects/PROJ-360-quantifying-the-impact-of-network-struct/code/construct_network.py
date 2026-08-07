import os
import json
import logging
import pickle
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

import numpy as np
from pymatgen.core import Structure
from pymatgen.analysis.graphs import StructureGraph
from pymatgen.analysis.local_env import CovalentBond
import networkx as nx

from config import get_config

# Constants
COVALENT_TOLERANCE = 0.45  # Angstroms
FALLBACK_CUTOFFS = [3.5, 4.0, 4.5, 5.0]  # Angstroms, progressive increase
MIN_NODES = 2
MIN_EDGES = 1

# Element covalent radii (approximate, from standard tables)
# Expanded list to cover common elements
COVALENT_RADII = {
    'H': 0.31, 'He': 0.28,
    'Li': 1.28, 'Be': 0.96, 'B': 0.84, 'C': 0.76, 'N': 0.71, 'O': 0.66, 'F': 0.57, 'Ne': 0.58,
    'Na': 1.66, 'Mg': 1.41, 'Al': 1.21, 'Si': 1.11, 'P': 1.07, 'S': 1.05, 'Cl': 1.02, 'Ar': 1.06,
    'K': 2.03, 'Ca': 1.74, 'Sc': 1.44, 'Ti': 1.36, 'V': 1.25, 'Cr': 1.27, 'Mn': 1.39, 'Fe': 1.25, 'Co': 1.26, 'Ni': 1.24, 'Cu': 1.32, 'Zn': 1.22, 'Ga': 1.22, 'Ge': 1.20, 'As': 1.19, 'Se': 1.20, 'Br': 1.20, 'Kr': 1.16,
    'Rb': 2.20, 'Sr': 1.92, 'Y': 1.62, 'Zr': 1.48, 'Nb': 1.37, 'Mo': 1.45, 'Tc': 1.56, 'Ru': 1.46, 'Rh': 1.42, 'Pd': 1.39, 'Ag': 1.45, 'Cd': 1.44, 'In': 1.42, 'Sn': 1.39, 'Sb': 1.39, 'Te': 1.38, 'I': 1.39, 'Xe': 1.40,
    'Cs': 2.44, 'Ba': 1.98, 'La': 1.69, 'Ce': 1.65, 'Pr': 1.65, 'Nd': 1.64, 'Pm': 1.63, 'Sm': 1.62, 'Eu': 1.60, 'Gd': 1.61, 'Tb': 1.59, 'Dy': 1.58, 'Ho': 1.57, 'Er': 1.56, 'Tm': 1.55, 'Yb': 1.54, 'Lu': 1.53,
    'Hf': 1.44, 'Ta': 1.34, 'W': 1.30, 'Re': 1.28, 'Os': 1.26, 'Ir': 1.27, 'Pt': 1.30, 'Au': 1.34, 'Hg': 1.32, 'Tl': 1.45, 'Pb': 1.46, 'Bi': 1.48, 'Po': 1.40, 'At': 1.50, 'Rn': 1.50
}

def setup_network_logger(name: str = "network_logger") -> logging.Logger:
    """Setup a dedicated logger for network construction tasks."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

def get_element_covalent_radius(element_symbol: str) -> float:
    """
    Retrieve covalent radius for an element.
    Falls back to a default if element not found.
    """
    return COVALENT_RADII.get(element_symbol, 1.5)  # Default fallback

def detect_bonds_covalent(structure: Structure, tolerance: float = COVALENT_TOLERANCE) -> List[Tuple[int, int]]:
    """
    Detect bonds based on covalent radii summation.
    Returns list of (site_index_1, site_index_2) tuples.
    """
    bonds = []
    sites = list(structure)
    n_sites = len(sites)

    for i in range(n_sites):
        site_i = sites[i]
        radius_i = get_element_covalent_radius(site_i.species_string)

        for j in range(i + 1, n_sites):
            site_j = sites[j]
            radius_j = get_element_covalent_radius(site_j.species_string)

            dist = structure.get_distance(i, j)
            cutoff = radius_i + radius_j + tolerance

            if dist <= cutoff:
                bonds.append((i, j))

    return bonds

def detect_bonds_fallback(structure: Structure, cutoffs: List[float] = FALLBACK_CUTOFFS) -> Tuple[List[Tuple[int, int]], float]:
    """
    Detect bonds using progressive distance cutoffs.
    Returns (bonds, cutoff_used).
    If no bonds found even with max cutoff, returns (None, None).
    """
    sites = list(structure)
    n_sites = len(sites)
    
    # Calculate max possible distance in the unit cell (diagonal)
    # This is a rough upper bound; if we need to go this far, the graph is likely just a cluster of atoms
    max_dist = structure.lattice.get_cartesian_coords([1, 1, 1])
    max_dist = np.linalg.norm(max_dist)

    for cutoff in cutoffs:
        bonds = []
        for i in range(n_sites):
            for j in range(i + 1, n_sites):
                dist = structure.get_distance(i, j)
                if dist <= cutoff:
                    bonds.append((i, j))
        
        if bonds:
            return bonds, cutoff

    # If we reach here, no bonds found even with the largest cutoffs
    return [], None

def construct_network_from_structure(structure: Structure, logger: Optional[logging.Logger] = None) -> Tuple[Optional[nx.Graph], str, str]:
    """
    Construct a networkx graph from a pymatgen Structure.
    Tries covalent detection first, then fallbacks.
    Returns (graph, status, details).
    """
    if logger is None:
        logger = setup_network_logger()

    # 1. Try Covalent Radii Method
    bonds = detect_bonds_covalent(structure)
    if bonds:
        logger.debug(f"Covalent method found {len(bonds)} bonds.")
        status = "covalent"
        details = f"Covalent radii method succeeded with {len(bonds)} bonds."
    else:
        logger.debug("Covalent method found no bonds. Attempting fallbacks...")
        bonds, cutoff_used = detect_bonds_fallback(structure)
        
        if bonds:
            status = "fallback"
            details = f"Fallback method succeeded with cutoff {cutoff_used:.2f}Å, found {len(bonds)} bonds."
            logger.info(f"Fallback successful for {structure.composition}: {details}")
        else:
            # No bonds found even with fallbacks
            status = "failed"
            details = "No bonds found after all fallback attempts. Graph has no edges."
            logger.warning(f"Failed to construct network for {structure.composition}: {details}")
            return None, status, details

    # Build NetworkX Graph
    G = nx.Graph()
    for idx, site in enumerate(structure):
        G.add_node(idx, species=site.species_string, coords=site.coords.tolist())
    
    G.add_edges_from(bonds)

    return G, status, details

def process_cif_file(cif_path: Path, output_dir: Path, logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
    """
    Process a single CIF file: parse, construct network, save if valid.
    Returns a record of the processing result.
    """
    if logger is None:
        logger = setup_network_logger()

    result = {
        "source_file": str(cif_path),
        "material_id": None,
        "status": "unknown",
        "details": "",
        "nodes": 0,
        "edges": 0,
        "checksum": None
    }

    try:
        structure = Structure.from_file(str(cif_path))
        # Extract material_id from filename or structure properties if available
        # Assuming filename format like "mp-123.cif" or similar
        stem = cif_path.stem
        if stem.startswith("mp-") or stem.startswith("material-"):
            result["material_id"] = stem
        else:
            # Fallback: generate a hash-based ID if no standard prefix
            result["material_id"] = f"unknown_{hashlib.sha256(str(cif_path).encode()).hexdigest()[:8]}"

        # Construct Network
        G, status, details = construct_network_from_structure(structure, logger)
        
        result["status"] = status
        result["details"] = details

        if G is None:
            # No edges found, skip saving
            logger.warning(f"Skipping {cif_path.name}: {details}")
            return result

        # Validate Graph
        if G.number_of_nodes() < MIN_NODES or G.number_of_edges() < MIN_EDGES:
            logger.warning(f"Skipping {cif_path.name}: Graph has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges (min: {MIN_NODES}/{MIN_EDGES}).")
            result["status"] = "skipped_validation"
            result["details"] = f"Failed validation: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges."
            return result

        # Save Graph
        output_path = output_dir / f"{result['material_id']}.pkl"
        with open(output_path, 'wb') as f:
            pickle.dump(G, f)

        # Compute checksum of the saved graph file
        with open(output_path, 'rb') as f:
            result["checksum"] = hashlib.sha256(f.read()).hexdigest()

        result["nodes"] = G.number_of_nodes()
        result["edges"] = G.number_of_edges()
        logger.info(f"Saved network for {result['material_id']}: {result['nodes']} nodes, {result['edges']} edges. Status: {status}")

    except Exception as e:
        logger.error(f"Error processing {cif_path}: {str(e)}")
        result["status"] = "error"
        result["details"] = str(e)

    return result

def save_graph_to_pickle(graph: nx.Graph, path: Path) -> str:
    """Save a graph to a pickle file and return its SHA-256 checksum."""
    with open(path, 'wb') as f:
        pickle.dump(graph, f)
    
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def build_network_manifest(results: List[Dict[str, Any]], output_path: Path):
    """
    Build a manifest JSON file recording the results of network construction.
    """
    manifest = {
        "total_processed": len(results),
        "successful": sum(1 for r in results if r["status"] in ["covalent", "fallback"]),
        "skipped": sum(1 for r in results if r["status"] in ["failed", "skipped_validation"]),
        "errors": sum(1 for r in results if r["status"] == "error"),
        "entries": results
    }
    
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)

def main():
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(description="Construct atomic networks from CIF files.")
    parser.add_argument("--input", type=str, required=True, help="Input directory containing CIF files.")
    parser.add_argument("--output", type=str, required=True, help="Output directory for network pickle files.")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger = setup_network_logger()
    logger.info(f"Processing CIF files from {input_dir} to {output_dir}")

    cif_files = list(input_dir.glob("*.cif"))
    if not cif_files:
        logger.error(f"No CIF files found in {input_dir}")
        return

    logger.info(f"Found {len(cif_files)} CIF files.")

    results = []
    for cif_file in cif_files:
        result = process_cif_file(cif_file, output_dir, logger)
        results.append(result)

    # Save manifest
    manifest_path = output_dir / "network_manifest.json"
    build_network_manifest(results, manifest_path)
    logger.info(f"Manifest saved to {manifest_path}")

    # Summary
    successful = [r for r in results if r["status"] in ["covalent", "fallback"]]
    skipped = [r for r in results if r["status"] in ["failed", "skipped_validation"]]
    
    logger.info(f"Processing complete. Successful: {len(successful)}, Skipped/Failed: {len(skipped)}")
    if skipped:
        logger.warning("The following materials were skipped due to lack of edges or validation failure:")
        for r in skipped:
            logger.warning(f"  - {r['source_file']}: {r['details']}")

if __name__ == "__main__":
    main()
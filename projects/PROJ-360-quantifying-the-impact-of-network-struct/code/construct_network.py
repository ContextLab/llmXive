import os
import json
import logging
import pickle
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from utils/config if available, otherwise define minimal fallbacks
try:
    from utils import setup_logging
except ImportError:
    def setup_logging(name: str) -> logging.Logger:
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

try:
    from config import Config
except ImportError:
    class Config:
        def __init__(self):
            self._data = {}
        def get(self, key, default=None):
            return self._data.get(key, default)

# Covalent radii (in Angstroms) - simplified set from Pyykko & Atsumi (2009)
COVALENT_RADII = {
    'H': 0.31, 'He': 0.28,
    'Li': 1.28, 'Be': 0.96, 'B': 0.84, 'C': 0.76, 'N': 0.71, 'O': 0.66, 'F': 0.57, 'Ne': 0.58,
    'Na': 1.66, 'Mg': 1.41, 'Al': 1.21, 'Si': 1.11, 'P': 1.07, 'S': 1.05, 'Cl': 1.02, 'Ar': 1.06,
    'K': 2.03, 'Ca': 1.76, 'Sc': 1.70, 'Ti': 1.60, 'V': 1.53, 'Cr': 1.39, 'Mn': 1.39, 'Fe': 1.32, 'Co': 1.26, 'Ni': 1.24, 'Cu': 1.32, 'Zn': 1.31, 'Ga': 1.26, 'Ge': 1.22, 'As': 1.19, 'Se': 1.20, 'Br': 1.20, 'Kr': 1.16,
    'Rb': 2.20, 'Sr': 1.95, 'Y': 1.90, 'Zr': 1.75, 'Nb': 1.64, 'Mo': 1.54, 'Tc': 1.47, 'Ru': 1.46, 'Rh': 1.42, 'Pd': 1.39, 'Ag': 1.45, 'Cd': 1.44, 'In': 1.42, 'Sn': 1.39, 'Sb': 1.39, 'Te': 1.38, 'I': 1.39, 'Xe': 1.40,
    'Cs': 2.44, 'Ba': 2.15, 'La': 2.07, 'Ce': 2.04, 'Pr': 2.03, 'Nd': 2.01, 'Pm': 1.99, 'Sm': 1.98, 'Eu': 1.98, 'Gd': 1.96, 'Tb': 1.94, 'Dy': 1.92, 'Ho': 1.92, 'Er': 1.89, 'Tm': 1.90, 'Yb': 1.87, 'Lu': 1.87,
    'Hf': 1.75, 'Ta': 1.70, 'W': 1.62, 'Re': 1.51, 'Os': 1.44, 'Ir': 1.41, 'Pt': 1.36, 'Au': 1.36, 'Hg': 1.32, 'Tl': 1.45, 'Pb': 1.46, 'Bi': 1.48, 'Po': 1.40, 'At': 1.50, 'Rn': 1.50
}

def get_element_covalent_radius(element: str) -> float:
    """Get covalent radius for an element symbol."""
    return COVALENT_RADII.get(element, 1.0)

def detect_bonds_covalent(structure: Any, tolerance: float = 0.4) -> List[Tuple[int, int, float]]:
    """
    Detect bonds based on covalent radii summation.
    Returns list of (atom_index_i, atom_index_j, distance).
    """
    bonds = []
    atoms = structure.sites
    num_atoms = len(atoms)

    for i in range(num_atoms):
        for j in range(i + 1, num_atoms):
            atom_i = atoms[i]
            atom_j = atoms[j]

            dist = atom_i.distance_to(atom_j)
            r_i = get_element_covalent_radius(atom_i.species_string)
            r_j = get_element_covalent_radius(atom_j.species_string)

            threshold = r_i + r_j + tolerance

            if dist <= threshold:
                bonds.append((i, j, dist))

    return bonds

def detect_bonds_fallback(structure: Any, max_distance: float = 3.5, step: float = 0.2) -> List[Tuple[int, int, float]]:
    """
    Fallback bond detection using progressive distance cutoffs.
    Starts from a conservative cutoff and increases until at least one bond is found
    or max_distance is reached.
    """
    atoms = structure.sites
    num_atoms = len(atoms)
    
    # Start with a very small cutoff to see if ANY bonds exist at all
    current_cutoff = 1.5 
    
    while current_cutoff <= max_distance:
        bonds = []
        for i in range(num_atoms):
            for j in range(i + 1, num_atoms):
                atom_i = atoms[i]
                atom_j = atoms[j]
                dist = atom_i.distance_to(atom_j)
                if dist <= current_cutoff:
                    bonds.append((i, j, dist))
        
        if len(bonds) > 0:
            logging.getLogger("construct_network").info(f"Fallback detected {len(bonds)} bonds at cutoff {current_cutoff:.2f} Å.")
            return bonds
        
        current_cutoff += step

    logging.getLogger("construct_network").warning(f"No bonds found even at max cutoff {max_distance} Å.")
    return []

def construct_network_from_structure(structure: Any) -> Optional[Any]:
    """
    Construct a networkx graph from a pymatgen Structure.
    Returns None if the graph has no edges after all fallback attempts.
    """
    try:
        import networkx as nx
    except ImportError:
        logging.error("networkx is required but not installed.")
        return None

    G = nx.Graph()
    atoms = structure.sites
    num_atoms = len(atoms)

    # Add nodes
    for i, atom in enumerate(atoms):
        G.add_node(i, element=atom.species_string, coords=atom.coords)

    # Try primary covalent detection
    bonds = detect_bonds_covalent(structure)
    
    # If no bonds, try fallback
    if not bonds:
        logging.getLogger("construct_network").warning(f"No bonds found via covalent radii for {structure.formula}. Attempting fallback...")
        bonds = detect_bonds_fallback(structure)

    if not bonds:
        logging.getLogger("construct_network").error(f"Failed to detect any bonds for {structure.formula} after fallback. Skipping.")
        return None

    # Add edges
    for i, j, dist in bonds:
        G.add_edge(i, j, distance=dist)

    return G

def process_cif_file(cif_path: str) -> Optional[Any]:
    """
    Parse a CIF file and construct a network graph.
    Returns the graph or None if processing fails or no bonds are found.
    """
    try:
        from pymatgen.io.cif import CifParser
    except ImportError:
        logging.error("pymatgen is required but not installed.")
        return None

    logger = logging.getLogger("construct_network")
    logger.info(f"Processing CIF: {cif_path}")

    try:
        parser = CifParser(cif_path)
        # Take the first structure found (usually the one we want)
        structures = parser.get_structures()
        if not structures:
            logger.error(f"No structures found in {cif_path}")
            return None
        
        structure = structures[0]
    except Exception as e:
        logger.error(f"Error parsing CIF {cif_path}: {e}")
        return None

    G = construct_network_from_structure(structure)
    return G

def save_graph_to_pickle(graph: Any, output_path: str):
    """Save a networkx graph to a pickle file."""
    with open(output_path, 'wb') as f:
        pickle.dump(graph, f)
    logger = logging.getLogger("construct_network")
    logger.info(f"Saved graph to {output_path}")

def build_network_manifest(material_id: str, cif_path: str, graph_path: str):
    """
    Build a manifest entry for a processed material.
    Returns a dictionary.
    """
    cif_checksum = hashlib.sha256(open(cif_path, 'rb').read()).hexdigest()
    graph_checksum = hashlib.sha256(open(graph_path, 'rb').read()).hexdigest()
    
    return {
        "material_id": material_id,
        "cif_path": str(cif_path),
        "cif_checksum": cif_checksum,
        "graph_path": str(graph_path),
        "graph_checksum": graph_checksum,
        "derivation": "CIF -> Network via covalent radii + fallback"
    }

def main():
    """
    Main entry point for constructing networks from CIF files.
    Usage: python code/construct_network.py --input <input_dir> --output <output_dir>
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Construct atomic networks from CIF files.")
    parser.add_argument("--input", type=str, required=True, help="Input directory containing CIF files.")
    parser.add_argument("--output", type=str, required=True, help="Output directory for graph pickle files.")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level.")
    args = parser.parse_args()

    # Setup logging
    logger = setup_logging("construct_network")
    logger.setLevel(getattr(logging, args.log_level.upper()))
    
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_dir.exists():
        logger.error(f"Input directory {input_dir} does not exist.")
        sys.exit(1)

    cif_files = list(input_dir.glob("*.cif"))
    if not cif_files:
        logger.error(f"No CIF files found in {input_dir}.")
        sys.exit(1)

    logger.info(f"Found {len(cif_files)} CIF files.")
    
    manifest = {"materials": []}
    processed_count = 0
    skipped_count = 0

    for cif_file in cif_files:
        # Extract material_id from filename (e.g., mp-123.cif -> mp-123)
        material_id = cif_file.stem
        
        graph = process_cif_file(str(cif_file))
        
        if graph is None:
            skipped_count += 1
            continue

        if graph.number_of_edges() == 0:
            logger.warning(f"Graph for {material_id} has no edges after fallback. Skipping.")
            skipped_count += 1
            continue

        output_path = output_dir / f"{material_id}.pkl"
        save_graph_to_pickle(graph, str(output_path))
        
        manifest_entry = build_network_manifest(material_id, str(cif_file), str(output_path))
        manifest["materials"].append(manifest_entry)
        processed_count += 1

    # Save manifest
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Processing complete. Success: {processed_count}, Skipped: {skipped_count}.")
    logger.info(f"Manifest saved to {manifest_path}")

if __name__ == "__main__":
    main()
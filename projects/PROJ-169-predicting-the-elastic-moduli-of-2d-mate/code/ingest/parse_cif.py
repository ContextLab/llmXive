"""
CIF Parser for 2D Material Elastic Moduli Prediction.

Converts CIF files from raw data sources into MaterialGraph objects using pymatgen.
Extracts node and edge features suitable for GNN training.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from pymatgen.core import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

# Import from project API surface
from data_models.material_graph import MaterialGraph
from utils.config import get_config
from utils.logger import log_operation, get_logger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants for featurization
ATOMIC_NUMBER_MAP = {
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

# Electronegativity (Pauling scale) - simplified mapping
ELECTRONEGATIVITY_MAP = {
    "H": 2.20, "He": 0.00, "Li": 0.98, "Be": 1.57, "B": 2.04, "C": 2.55,
    "N": 3.04, "O": 3.44, "F": 3.98, "Ne": 0.00, "Na": 0.93, "Mg": 1.31,
    "Al": 1.61, "Si": 1.90, "P": 2.19, "S": 2.58, "Cl": 3.16, "Ar": 0.00,
    "K": 0.82, "Ca": 1.00, "Sc": 1.36, "Ti": 1.54, "V": 1.63, "Cr": 1.66,
    "Mn": 1.55, "Fe": 1.83, "Co": 1.88, "Ni": 1.91, "Cu": 1.90, "Zn": 1.65,
    "Ga": 1.81, "Ge": 2.01, "As": 2.18, "Se": 2.55, "Br": 2.96, "Kr": 3.00,
    "Rb": 0.82, "Sr": 0.95, "Y": 1.22, "Zr": 1.33, "Nb": 1.60, "Mo": 2.16,
    "Tc": 1.90, "Ru": 2.20, "Rh": 2.28, "Pd": 2.20, "Ag": 1.93, "Cd": 1.69,
    "In": 1.78, "Sn": 1.96, "Sb": 2.05, "Te": 2.10, "I": 2.66, "Xe": 2.60,
    "Cs": 0.79, "Ba": 0.89, "La": 1.10, "Ce": 1.12, "Pr": 1.13, "Nd": 1.14,
    "Pm": 1.13, "Sm": 1.17, "Eu": 1.20, "Gd": 1.20, "Tb": 1.20, "Dy": 1.22,
    "Ho": 1.23, "Er": 1.24, "Tm": 1.25, "Yb": 1.10, "Lu": 1.27, "Hf": 1.30,
    "Ta": 1.50, "W": 2.36, "Re": 1.90, "Os": 2.20, "Ir": 2.20, "Pt": 2.28,
    "Au": 2.54, "Hg": 2.00, "Tl": 1.62, "Pb": 1.87, "Bi": 2.02, "Po": 2.00,
    "At": 2.20, "Rn": 2.20, "Fr": 0.70, "Ra": 0.90, "Ac": 1.10, "Th": 1.30,
    "Pa": 1.50, "U": 1.38, "Np": 1.36, "Pu": 1.28, "Am": 1.30, "Cm": 1.30,
    "Bk": 1.30, "Cf": 1.30, "Es": 1.30, "Fm": 1.30, "Md": 1.30, "No": 1.30,
    "Lr": 1.30, "Rf": 1.30, "Db": 1.30, "Sg": 1.30, "Bh": 1.30, "Hs": 1.30,
    "Mt": 1.30, "Ds": 1.30, "Rg": 1.30, "Cn": 1.30, "Nh": 1.30, "Fl": 1.30,
    "Mc": 1.30, "Lv": 1.30, "Ts": 1.30, "Og": 1.30
}

# Atomic radii (pm) - simplified mapping
ATOMIC_RADIUS_MAP = {
    "H": 37, "He": 32, "Li": 134, "Be": 90, "B": 82, "C": 77, "N": 75, "O": 73,
    "F": 72, "Ne": 71, "Na": 154, "Mg": 130, "Al": 118, "Si": 111, "P": 106,
    "S": 102, "Cl": 99, "Ar": 97, "K": 196, "Ca": 174, "Sc": 144, "Ti": 136,
    "V": 125, "Cr": 127, "Mn": 139, "Fe": 125, "Co": 126, "Ni": 121, "Cu": 138,
    "Zn": 131, "Ga": 126, "Ge": 122, "As": 119, "Se": 116, "Br": 114, "Kr": 110,
    "Rb": 211, "Sr": 192, "Y": 162, "Zr": 148, "Nb": 137, "Mo": 145, "Tc": 156,
    "Ru": 126, "Rh": 134, "Pd": 137, "Ag": 144, "Cd": 151, "In": 144, "Sn": 141,
    "Sb": 138, "Te": 135, "I": 133, "Xe": 130, "Cs": 225, "Ba": 198, "La": 169,
    "Ce": 183, "Pr": 182, "Nd": 181, "Pm": 183, "Sm": 180, "Eu": 180, "Gd": 180,
    "Tb": 177, "Dy": 178, "Ho": 176, "Er": 176, "Tm": 175, "Yb": 174, "Lu": 174,
    "Hf": 159, "Ta": 146, "W": 139, "Re": 137, "Os": 135, "Ir": 136, "Pt": 139,
    "Au": 144, "Hg": 149, "Tl": 148, "Pb": 147, "Bi": 146, "Po": 146, "At": 145,
    "Rn": 145, "Fr": 144, "Ra": 143, "Ac": 142, "Th": 141, "Pa": 140, "U": 139,
    "Np": 138, "Pu": 137, "Am": 136, "Cm": 135, "Bk": 134, "Cf": 133, "Es": 132,
    "Fm": 131, "Md": 130, "No": 129, "Lr": 128, "Rf": 127, "Db": 126, "Sg": 125,
    "Bh": 124, "Hs": 123, "Mt": 122, "Ds": 121, "Rg": 120, "Cn": 119, "Nh": 118,
    "Fl": 117, "Mc": 116, "Lv": 115, "Ts": 114, "Og": 113
}

def get_atomic_properties(symbol: str) -> Tuple[float, float, float]:
    """
    Get atomic properties for a given element symbol.

    Args:
        symbol: Element symbol (e.g., "C", "Fe")

    Returns:
        Tuple of (atomic_number, electronegativity, atomic_radius)
    """
    atomic_number = ATOMIC_NUMBER_MAP.get(symbol, 0)
    electronegativity = ELECTRONEGATIVITY_MAP.get(symbol, 0.0)
    atomic_radius = ATOMIC_RADIUS_MAP.get(symbol, 0.0)

    return atomic_number, electronegativity, atomic_radius

def featurize_atoms(structure: Structure) -> np.ndarray:
    """
    Create node features for each atom in the structure.

    Features per atom:
    - Atomic number (normalized)
    - Electronegativity
    - Atomic radius (normalized)
    - Valence electron count (approximated by group number)

    Args:
        structure: pymatgen Structure object

    Returns:
        np.ndarray of shape (n_atoms, n_features)
    """
    n_atoms = len(structure)
    n_features = 4  # atomic_number, electronegativity, radius, valence

    features = np.zeros((n_atoms, n_features), dtype=np.float32)

    for i, site in enumerate(structure):
        symbol = site.species_string
        atomic_number, electronegativity, atomic_radius = get_atomic_properties(symbol)

        # Normalize atomic number (max ~118)
        features[i, 0] = atomic_number / 118.0
        features[i, 1] = electronegativity / 4.0  # Max Pauling ~4.0
        features[i, 2] = atomic_radius / 250.0  # Max radius ~250 pm
        # Valence electrons (simplified: group number mod 18, with adjustments)
        # For transition metals, use a heuristic based on atomic number
        if atomic_number <= 2:  # H, He
            features[i, 3] = atomic_number
        elif atomic_number <= 10:  # Li-Ne
            features[i, 3] = (atomic_number - 2) % 8 + 1
        elif atomic_number <= 18:  # Na-Ar
            features[i, 3] = (atomic_number - 10) % 8 + 1
        else:
            # Transition metals and beyond: use a simplified heuristic
            # This is an approximation; real valence depends on oxidation state
            features[i, 3] = min(8, (atomic_number % 18) + 1)

    return features

def featurize_bonds(structure: Structure, cutoff: float = 3.5) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create edge features and adjacency matrix for bonds in the structure.

    Uses a distance-based cutoff to determine bonds.

    Args:
        structure: pymatgen Structure object
        cutoff: Bond distance cutoff in Angstroms

    Returns:
        Tuple of (adjacency_matrix, edge_features)
        - adjacency_matrix: np.ndarray of shape (n_atoms, n_atoms), binary
        - edge_features: np.ndarray of shape (n_bonds, n_edge_features)
    """
    n_atoms = len(structure)
    adjacency = np.zeros((n_atoms, n_atoms), dtype=np.float32)
    edge_features_list = []

    # Calculate all pairwise distances
    for i in range(n_atoms):
        for j in range(i + 1, n_atoms):
            dist = structure.get_distance(i, j)
            if dist < cutoff:
                adjacency[i, j] = 1.0
                adjacency[j, i] = 1.0

                # Edge features: normalized distance, direction (simplified)
                # For now, just use normalized distance
                edge_feat = np.array([dist / cutoff], dtype=np.float32)
                edge_features_list.append(edge_feat)

    if len(edge_features_list) == 0:
        return adjacency, np.zeros((0, 1), dtype=np.float32)

    edge_features = np.vstack(edge_features_list)
    return adjacency, edge_features

def parse_cif_file(cif_path: Path) -> Optional[MaterialGraph]:
    """
    Parse a single CIF file and convert it to a MaterialGraph.

    Args:
        cif_path: Path to the CIF file

    Returns:
        MaterialGraph object or None if parsing fails
    """
    try:
        structure = Structure.from_file(cif_path)

        # Check if structure is valid
        if len(structure) == 0:
            logger.warning(f"Empty structure in {cif_path}")
            return None

        # Extract node features
        node_features = featurize_atoms(structure)

        # Extract edge features and adjacency
        adjacency, edge_features = featurize_bonds(structure)

        # Extract target values (elastic moduli)
        # These should come from the data source metadata, not the CIF itself
        # For now, we'll use placeholder values that should be overwritten by the pipeline
        target_moduli = {
            "youngs_modulus": 0.0,  # Will be filled by pipeline
            "shear_modulus": 0.0,    # Will be filled by pipeline
            "poisson_ratio": 0.0     # Will be filled by pipeline
        }

        # Extract metadata
        metadata = {
            "source_file": str(cif_path.name),
            "n_atoms": len(structure),
            "space_group": structure.get_space_group_info()[0] if structure.lattice is not None else "unknown",
            "lattice_parameters": [
                structure.lattice.a if structure.lattice else 0.0,
                structure.lattice.b if structure.lattice else 0.0,
                structure.lattice.c if structure.lattice else 0.0,
                structure.lattice.alpha if structure.lattice else 0.0,
                structure.lattice.beta if structure.lattice else 0.0,
                structure.lattice.gamma if structure.lattice else 0.0,
            ] if structure.lattice else [0.0] * 6
        }

        # Create MaterialGraph
        graph = MaterialGraph(
            node_features=node_features.tolist(),
            edge_features=edge_features.tolist(),
            adjacency=adjacency.tolist(),
            target_moduli=target_moduli,
            metadata=metadata
        )

        return graph

    except Exception as e:
        logger.error(f"Failed to parse CIF file {cif_path}: {e}")
        return None

def parse_cif_directory(input_dir: Path, output_dir: Optional[Path] = None) -> Tuple[int, int]:
    """
    Parse all CIF files in a directory and optionally save results.

    Args:
        input_dir: Directory containing CIF files
        output_dir: Optional directory to save parsed graphs as JSON

    Returns:
        Tuple of (parsed_count, excluded_count)
    """
    cif_files = list(input_dir.glob("*.cif")) + list(input_dir.glob("*.CIF"))

    if not cif_files:
        logger.warning(f"No CIF files found in {input_dir}")
        return 0, 0

    parsed_graphs = []
    excluded_count = 0

    for cif_file in cif_files:
        graph = parse_cif_file(cif_file)
        if graph is not None:
            parsed_graphs.append(graph)
        else:
            excluded_count += 1

    # Save results if output_dir is specified
    if output_dir and parsed_graphs:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "parsed_graphs.json"

        # Convert graphs to serializable format
        serializable_graphs = []
        for i, graph in enumerate(parsed_graphs):
            serializable_graphs.append({
                "index": i,
                "node_features": graph.node_features,
                "edge_features": graph.edge_features,
                "adjacency": graph.adjacency,
                "target_moduli": graph.target_moduli,
                "metadata": graph.metadata
            })

        with open(output_path, "w") as f:
            json.dump(serializable_graphs, f, indent=2)

        logger.info(f"Saved {len(parsed_graphs)} parsed graphs to {output_path}")

    return len(parsed_graphs), excluded_count

@log_operation("parse_cif_main")
def main():
    """
    Main entry point for CIF parsing.

    Usage:
        python code/ingest/parse_cif.py --input <input_dir> --output <output_dir>

    Args:
        input_dir: Directory containing CIF files
        output_dir: Directory to save parsed graphs (optional)
    """
    parser = argparse.ArgumentParser(description="Parse CIF files into MaterialGraph objects")
    parser.add_argument("--input", type=str, required=True, help="Input directory containing CIF files")
    parser.add_argument("--output", type=str, required=False, help="Output directory for parsed graphs (optional)")

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else None

    if not input_path.exists():
        logger.error(f"Input directory does not exist: {input_path}")
        sys.exit(1)

    parsed_count, excluded_count = parse_cif_directory(input_path, output_path)

    logger.info(f"Parsed {parsed_count} graphs, excluded {excluded_count}")

    # Write summary to stdout for pipeline integration
    summary = {
        "parsed_count": parsed_count,
        "excluded_count": excluded_count,
        "input_dir": str(input_path),
        "output_dir": str(output_path) if output_path else None
    }

    print(json.dumps(summary))

if __name__ == "__main__":
    main()
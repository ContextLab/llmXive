"""
CIF Parser for 2D Material Elastic Moduli Prediction.

Converts CIF files to MaterialGraph objects using pymatgen.
Extracts node and edge features for GNN training.
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
from pymatgen.io.cif import CifParser
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

# Import local modules
from data_models.material_graph import MaterialGraph
from utils.config import get_config
from utils.logger import log_operation

# Constants for featurization
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
    "Og": 118,
}

# Electronegativity (Pauling scale) - approximate values for common elements
ELECTRONEGATIVITY = {
    "H": 2.20, "Li": 0.98, "Be": 1.57, "B": 2.04, "C": 2.55, "N": 3.04,
    "O": 3.44, "F": 3.98, "Na": 0.93, "Mg": 1.31, "Al": 1.61, "Si": 1.90,
    "P": 2.19, "S": 2.58, "Cl": 3.16, "K": 0.82, "Ca": 1.00, "Sc": 1.36,
    "Ti": 1.54, "V": 1.63, "Cr": 1.66, "Mn": 1.55, "Fe": 1.83, "Co": 1.88,
    "Ni": 1.91, "Cu": 1.90, "Zn": 1.65, "Ga": 1.81, "Ge": 2.01, "As": 2.18,
    "Se": 2.55, "Br": 2.96, "Rb": 0.82, "Sr": 0.95, "Y": 1.22, "Zr": 1.33,
    "Nb": 1.6, "Mo": 2.16, "Tc": 1.9, "Ru": 2.2, "Rh": 2.28, "Pd": 2.20,
    "Ag": 1.93, "Cd": 1.69, "In": 1.78, "Sn": 1.96, "Sb": 2.05, "Te": 2.1,
    "I": 2.66, "Cs": 0.79, "Ba": 0.89, "La": 1.1, "Ce": 1.12, "Pr": 1.13,
    "Nd": 1.14, "Pm": 1.13, "Sm": 1.17, "Eu": 1.2, "Gd": 1.2, "Tb": 1.2,
    "Dy": 1.22, "Ho": 1.23, "Er": 1.24, "Tm": 1.25, "Yb": 1.1, "Lu": 1.27,
    "Hf": 1.3, "Ta": 1.5, "W": 2.36, "Re": 1.9, "Os": 2.2, "Ir": 2.20,
    "Pt": 2.28, "Au": 2.54, "Hg": 2.00, "Tl": 1.62, "Pb": 2.33, "Bi": 2.02,
    "Po": 2.0, "At": 2.2, "Rn": 2.2,
}

# Atomic radii (pm) - approximate
ATOMIC_RADII = {
    "H": 53, "Li": 167, "Be": 112, "B": 87, "C": 67, "N": 56, "O": 48,
    "F": 42, "Na": 190, "Mg": 145, "Al": 118, "Si": 111, "P": 98, "S": 88,
    "Cl": 79, "K": 243, "Ca": 194, "Sc": 184, "Ti": 176, "V": 171,
    "Cr": 166, "Mn": 161, "Fe": 156, "Co": 152, "Ni": 149, "Cu": 145,
    "Zn": 142, "Ga": 136, "Ge": 125, "As": 114, "Se": 103, "Br": 94,
    "Rb": 265, "Sr": 219, "Y": 212, "Zr": 206, "Nb": 198, "Mo": 190,
    "Tc": 183, "Ru": 178, "Rh": 173, "Pd": 169, "Ag": 165, "Cd": 161,
    "In": 156, "Sn": 145, "Sb": 133, "Te": 123, "I": 115, "Cs": 298,
    "Ba": 253, "La": 226, "Ce": 210, "Pr": 207, "Nd": 205, "Pm": 205,
    "Sm": 204, "Eu": 204, "Gd": 203, "Tb": 202, "Dy": 201, "Ho": 200,
    "Er": 199, "Tm": 198, "Yb": 194, "Lu": 193, "Hf": 191, "Ta": 188,
    "W": 186, "Re": 185, "Os": 184, "Ir": 182, "Pt": 182, "Au": 180,
    "Hg": 178, "Tl": 175, "Pb": 175, "Bi": 170, "Po": 168, "At": 166,
    "Rn": 164,
}

logger = logging.getLogger(__name__)

@log_operation("get_atomic_properties")
def get_atomic_properties(symbol: str) -> Dict[str, float]:
    """
    Get basic atomic properties for featurization.

    Args:
        symbol: Chemical symbol of the element.

    Returns:
        Dictionary with atomic number, electronegativity, and radius.
    """
    atomic_num = ATOMIC_NUMBERS.get(symbol, 0)
    electronegativity = ELECTRONEGATIVITY.get(symbol, 0.0)
    radius = ATOMIC_RADII.get(symbol, 0.0)

    return {
        "atomic_number": float(atomic_num),
        "electronegativity": electronegativity,
        "atomic_radius": radius,
    }

@log_operation("featurize_atoms")
def featurize_atoms(atoms: List[Dict[str, Any]]) -> List[List[float]]:
    """
    Convert list of atoms to feature vectors.

    Args:
        atoms: List of dictionaries with 'symbol' and 'properties'.

    Returns:
        List of feature vectors (one per atom).
    """
    features = []
    for atom in atoms:
        props = get_atomic_properties(atom["symbol"])
        # Normalize features (simple min-max for now, can be improved)
        feat = [
            props["atomic_number"] / 118.0,  # Normalize atomic number
            props["electronegativity"] / 4.0,  # Normalize electronegativity
            props["atomic_radius"] / 300.0,  # Normalize radius
        ]
        features.append(feat)
    return features

@log_operation("featurize_bonds")
def featurize_bonds(
    bonds: List[Tuple[int, int, float]],
    max_dist: float = 3.0,
) -> List[List[float]]:
    """
    Convert list of bonds to feature vectors.

    Args:
        bonds: List of (atom_idx_i, atom_idx_j, distance).
        max_dist: Maximum distance for bonding consideration.

    Returns:
        List of edge feature vectors.
    """
    features = []
    for i, j, dist in bonds:
        # Normalize distance
        norm_dist = min(dist / max_dist, 1.0)
        # Edge features: normalized distance
        edge_feat = [norm_dist]
        features.append(edge_feat)
    return features

@log_operation("parse_cif_file")
def parse_cif_file(
    cif_path: str,
    elastic_tensor: Optional[np.ndarray] = None,
    target_moduli: Optional[Dict[str, float]] = None,
    structure_pickle: Optional[bytes] = None,
    cif_raw: Optional[str] = None,
) -> Optional[MaterialGraph]:
    """
    Parse a single CIF file and convert to MaterialGraph.

    Args:
        cif_path: Path to the CIF file.
        elastic_tensor: Optional 6x6 elastic tensor (Voigt notation).
        target_moduli: Optional dictionary with Young's, Shear, Poisson moduli.
        structure_pickle: Optional pre-computed pickle of pymatgen Structure.
        cif_raw: Optional raw CIF string.

    Returns:
        MaterialGraph object or None if parsing fails.
    """
    try:
        # Parse CIF
        parser = CifParser(cif_path)
        structures = parser.get_structures()

        if not structures:
            logger.warning(f"No structures found in {cif_path}")
            return None

        # Use the first structure (typically the most symmetric one)
        structure = structures[0]

        # If structure_pickle is provided, use it (to ensure consistency)
        if structure_pickle is not None:
            import pickle
            structure = pickle.loads(structure_pickle)

        # Extract atomic properties
        atoms = []
        for site in structure.sites:
            atoms.append({
                "symbol": site.species_string,
                "properties": get_atomic_properties(site.species_string),
            })

        # Featurize atoms
        node_features = featurize_atoms(atoms)

        # Build adjacency (based on distance)
        bonds = []
        for i in range(len(atoms)):
            for j in range(i + 1, len(atoms)):
                dist = structure[i].distance_to(structure[j])
                if dist < 3.0:  # Bonding threshold
                    bonds.append((i, j, dist))

        # Featurize bonds
        edge_features = featurize_bonds(bonds)

        # Build edge index (PyG format: [2, num_edges])
        edge_index = []
        for i, j, _ in bonds:
            edge_index.append([i, j])
            edge_index.append([j, i])  # Undirected

        if not edge_index:
            edge_index = [[], []]
        else:
            edge_index = list(zip(*edge_index))

        # Create MaterialGraph
        graph = MaterialGraph(
            node_features=node_features,
            edge_features=edge_features,
            edge_index=edge_index,
            target_moduli=target_moduli or {},
            family_id=structure.formula,  # Use formula as family_id placeholder
            structure_pickle=structure_pickle,
            cif_raw=cif_raw,
        )

        return graph

    except Exception as e:
        logger.error(f"Failed to parse {cif_path}: {e}")
        return None

@log_operation("parse_cif_directory")
def parse_cif_directory(
    input_dir: str,
    output_dir: str,
    elastic_tensors: Optional[Dict[str, np.ndarray]] = None,
    target_moduli_list: Optional[List[Dict[str, float]]] = None,
) -> List[MaterialGraph]:
    """
    Parse all CIF files in a directory.

    Args:
        input_dir: Directory containing CIF files.
        output_dir: Directory to save parsed graphs (JSON/Parquet).
        elastic_tensors: Optional dict mapping filename to elastic tensor.
        target_moduli_list: Optional list of target moduli dicts.

    Returns:
        List of MaterialGraph objects.
    """
    input_path = Path(input_dir)
    cif_files = list(input_path.glob("*.cif"))

    if not cif_files:
        logger.warning(f"No CIF files found in {input_dir}")
        return []

    graphs = []
    for idx, cif_file in enumerate(cif_files):
        elastic_tensor = None
        target_moduli = None
        structure_pickle = None
        cif_raw = None

        # Load elastic tensor if available
        if elastic_tensors and cif_file.name in elastic_tensors:
            elastic_tensor = elastic_tensors[cif_file.name]

        # Load target moduli if available
        if target_moduli_list and idx < len(target_moduli_list):
            target_moduli = target_moduli_list[idx]

        # Read raw CIF for storage
        try:
            with open(cif_file, "r") as f:
                cif_raw = f.read()
        except Exception as e:
            logger.warning(f"Could not read raw CIF {cif_file}: {e}")
            continue

        # Parse CIF
        graph = parse_cif_file(
            str(cif_file),
            elastic_tensor=elastic_tensor,
            target_moduli=target_moduli,
            structure_pickle=structure_pickle,
            cif_raw=cif_raw,
        )

        if graph is not None:
            graphs.append(graph)

    logger.info(f"Parsed {len(graphs)} valid structures from {len(cif_files)} files")
    return graphs

@log_operation("main")
def main():
    """CLI entry point for CIF parsing."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Parse CIF files into MaterialGraph objects."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Input directory containing CIF files.",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output directory for parsed graphs.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level.",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create output directory
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)

    # Parse CIFs
    graphs = parse_cif_directory(args.input, args.output)

    # Save results (placeholder - actual saving done by pipeline)
    logger.info(f"Successfully parsed {len(graphs)} graphs")
    logger.info(f"Output directory: {args.output}")

    if not graphs:
        logger.warning("No graphs were parsed. Check input files.")
        sys.exit(1)

    return graphs

if __name__ == "__main__":
    main()
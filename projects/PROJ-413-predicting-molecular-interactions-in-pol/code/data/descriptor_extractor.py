"""
Descriptor Extractor for Molecular Interface Pairs.

This script extracts hand-crafted topological descriptors (degree, density,
clustering coefficient) from the curated dataset of molecular graphs and
saves them to a CSV file for downstream analysis.

Input: data/curated/curated_dataset.csv
Output: data/processed/descriptors.csv
"""

import os
import sys
import logging
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import csv
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.seed_utils import set_seed
from utils.exceptions import DataError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
CURATED_DATA_PATH = project_root / "data" / "curated" / "curated_dataset.csv"
OUTPUT_PATH = project_root / "data" / "processed" / "descriptors.csv"
SEED_VALUE = 42

def parse_smiles_to_adjacency(smiles: str) -> Tuple[np.ndarray, int]:
    """
    Parse a SMILES string into an adjacency matrix and atom count.
    Uses RDKit for robust parsing.

    Args:
        smiles: SMILES string representing the molecule.

    Returns:
        Tuple of (adjacency_matrix, num_atoms)
    """
    try:
        from rdkit import Chem
        from rdkit.Chem import rdmolops
    except ImportError:
        raise DataError("RDKit is required for SMILES parsing but not installed.")

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        logger.warning(f"Failed to parse SMILES: {smiles}")
        return np.zeros((0, 0)), 0

    # Get adjacency matrix from RDKit
    adj = rdmolops.GetAdjacencyMatrix(mol)
    return adj, mol.GetNumAtoms()

def calculate_degree(adj: np.ndarray) -> List[float]:
    """
    Calculate the degree (number of connections) for each node.

    Args:
        adj: Adjacency matrix (N x N)

    Returns:
        List of degrees for each node
    """
    if adj.size == 0:
        return []
    return np.sum(adj, axis=1).tolist()

def calculate_graph_density(adj: np.ndarray) -> float:
    """
    Calculate the density of the graph (actual edges / possible edges).

    Args:
        adj: Adjacency matrix (N x N)

    Returns:
        Graph density (0.0 to 1.0)
    """
    n = adj.shape[0]
    if n <= 1:
        return 0.0
    actual_edges = np.sum(adj) / 2  # Undirected graph
    possible_edges = n * (n - 1) / 2
    if possible_edges == 0:
        return 0.0
    return actual_edges / possible_edges

def calculate_clustering_coefficient(adj: np.ndarray) -> List[float]:
    """
    Calculate the local clustering coefficient for each node.
    CC_i = (2 * triangles_i) / (k_i * (k_i - 1))

    Args:
        adj: Adjacency matrix (N x N)

    Returns:
        List of clustering coefficients for each node
    """
    n = adj.shape[0]
    if n == 0:
        return []

    degrees = np.sum(adj, axis=1)
    coefficients = []

    for i in range(n):
        k = degrees[i]
        if k < 2:
            coefficients.append(0.0)
            continue

        # Get neighbors
        neighbors = np.where(adj[i] > 0)[0]
        # Count edges between neighbors
        subgraph = adj[np.ix_(neighbors, neighbors)]
        triangles = np.sum(subgraph) / 2
        possible_triangles = k * (k - 1) / 2

        if possible_triangles == 0:
            coefficients.append(0.0)
        else:
            coefficients.append(triangles / possible_triangles)

    return coefficients

def extract_descriptors(smiles_polymer: str, smiles_filler: str) -> Dict[str, float]:
    """
    Extract topological descriptors for a pair of molecules.

    Args:
        smiles_polymer: SMILES string for the polymer
        smiles_filler: SMILES string for the filler

    Returns:
        Dictionary of descriptors
    """
    descriptors = {}

    # Process polymer
    adj_poly, n_poly = parse_smiles_to_adjacency(smiles_polymer)
    if n_poly == 0:
        raise DataError(f"Invalid polymer SMILES: {smiles_polymer}")

    deg_poly = calculate_degree(adj_poly)
    descriptors['polymer_avg_degree'] = float(np.mean(deg_poly)) if deg_poly else 0.0
    descriptors['polymer_max_degree'] = float(np.max(deg_poly)) if deg_poly else 0.0
    descriptors['polymer_density'] = calculate_graph_density(adj_poly)
    descriptors['polymer_clustering'] = float(np.mean(calculate_clustering_coefficient(adj_poly)))

    # Process filler
    adj_fill, n_fill = parse_smiles_to_adjacency(smiles_filler)
    if n_fill == 0:
        raise DataError(f"Invalid filler SMILES: {smiles_filler}")

    deg_fill = calculate_degree(adj_fill)
    descriptors['filler_avg_degree'] = float(np.mean(deg_fill)) if deg_fill else 0.0
    descriptors['filler_max_degree'] = float(np.max(deg_fill)) if deg_fill else 0.0
    descriptors['filler_density'] = calculate_graph_density(adj_fill)
    descriptors['filler_clustering'] = float(np.mean(calculate_clustering_coefficient(adj_fill)))

    # Combined descriptors
    descriptors['total_atoms'] = n_poly + n_fill
    descriptors['combined_density'] = (descriptors['polymer_density'] + descriptors['filler_density']) / 2.0

    return descriptors

def main():
    """
    Main function to extract descriptors from the curated dataset.
    """
    logger.info("Starting descriptor extraction...")
    set_seed(SEED_VALUE)

    if not CURATED_DATA_PATH.exists():
        raise FileNotFoundError(f"Curated dataset not found at {CURATED_DATA_PATH}")

    output_path = OUTPUT_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)

    descriptors_list = []
    row_count = 0

    try:
        with open(CURATED_DATA_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames

            if 'polymer_smiles' not in fieldnames or 'filler_smiles' not in fieldnames:
                raise DataError("Curated dataset missing 'polymer_smiles' or 'filler_smiles' columns")

            for row in reader:
                try:
                    desc = extract_descriptors(row['polymer_smiles'], row['filler_smiles'])
                    # Preserve original identifiers
                    desc['id'] = row.get('id', f"row_{row_count}")
                    desc['polymer_smiles'] = row['polymer_smiles']
                    desc['filler_smiles'] = row['filler_smiles']

                    # Include adhesion energy if present
                    if 'adhesion_energy' in row and row['adhesion_energy']:
                        try:
                            desc['adhesion_energy'] = float(row['adhesion_energy'])
                        except ValueError:
                            desc['adhesion_energy'] = None

                    descriptors_list.append(desc)
                    row_count += 1

                    if row_count % 100 == 0:
                        logger.info(f"Processed {row_count} rows...")

                except Exception as e:
                    logger.warning(f"Skipping row {row_count}: {e}")
                    continue

        if row_count == 0:
            raise DataError("No valid rows processed from curated dataset")

        # Write output
        if descriptors_list:
            output_fieldnames = list(descriptors_list[0].keys())
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=output_fieldnames)
                writer.writeheader()
                writer.writerows(descriptors_list)

            logger.info(f"Successfully extracted descriptors for {row_count} rows to {output_path}")
        else:
            raise DataError("No descriptors were extracted")

    except Exception as e:
        logger.error(f"Descriptor extraction failed: {e}")
        raise

if __name__ == "__main__":
    main()
"""
Descriptor Extractor for Molecular Graphs.

This module extracts hand-crafted topological descriptors from the curated
molecular dataset. It reads SMILES strings from the curated dataset, constructs
molecular graphs using RDKit, and calculates:
- Degree (average node degree)
- Graph Density
- Clustering Coefficient (average)

Output is saved to data/processed/descriptors.csv.
"""
import os
import sys
import logging
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import networkx as nx
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
INPUT_PATH = PROJECT_ROOT / "data" / "curated" / "curated_dataset.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "descriptors.csv"

# Exit codes
E_INPUT_MISSING = 101
E_NO_DATA = 102
E_WRITE_FAILED = 103


def parse_smiles_to_adjacency(smiles: str) -> Optional[nx.Graph]:
    """
    Convert a SMILES string to a NetworkX graph representing the molecular structure.

    Args:
        smiles: SMILES string of the molecule.

    Returns:
        NetworkX graph where nodes are atoms and edges are bonds.
        Returns None if the SMILES is invalid.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning(f"Could not parse SMILES: {smiles}")
            return None

        G = nx.Graph()
        # Add atoms as nodes
        for atom in mol.GetAtoms():
            G.add_node(atom.GetIdx(), symbol=atom.GetSymbol(), atomic_num=atom.GetAtomicNum())

        # Add bonds as edges
        for bond in mol.GetBonds():
            G.add_edge(
                bond.GetBeginAtomIdx(),
                bond.GetEndAtomIdx(),
                bond_type=bond.GetBondType()
            )
        return G
    except Exception as e:
        logger.error(f"Error parsing SMILES '{smiles}': {e}")
        return None


def calculate_degree(G: nx.Graph) -> float:
    """
    Calculate the average degree of the graph.

    Args:
        G: NetworkX graph.

    Returns:
        Average degree of the graph.
    """
    if G.number_of_nodes() == 0:
        return 0.0
    return sum(dict(G.degree()).values()) / G.number_of_nodes()


def calculate_graph_density(G: nx.Graph) -> float:
    """
    Calculate the density of the graph.

    Density is the ratio of actual edges to possible edges.

    Args:
        G: NetworkX graph.

    Returns:
        Graph density (0.0 to 1.0).
    """
    if G.number_of_nodes() <= 1:
        return 0.0
    return nx.density(G)


def calculate_clustering_coefficient(G: nx.Graph) -> float:
    """
    Calculate the average clustering coefficient of the graph.

    Args:
        G: NetworkX graph.

    Returns:
        Average clustering coefficient.
    """
    if G.number_of_nodes() == 0:
        return 0.0
    return nx.average_clustering(G)


def load_curated_data(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load the curated dataset from CSV.

    Args:
        input_path: Path to the curated dataset CSV.

    Returns:
        List of dictionaries representing rows.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    import csv

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    rows = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if 'polymer_smiles' not in reader.fieldnames or 'filler_smiles' not in reader.fieldnames:
            raise ValueError("Input CSV must contain 'polymer_smiles' and 'filler_smiles' columns.")
        for row in reader:
            rows.append(row)

    if len(rows) == 0:
        raise ValueError("Input CSV is empty.")

    return rows


def extract_descriptors(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract topological descriptors for each row in the dataset.

    For each row, we construct graphs for both polymer and filler molecules
    and calculate descriptors for each, plus combined statistics.

    Args:
        rows: List of dictionaries from the curated dataset.

    Returns:
        List of dictionaries containing original data plus descriptors.
    """
    results = []
    total_processed = 0
    total_skipped = 0

    for idx, row in enumerate(rows):
        polymer_smiles = row.get('polymer_smiles', '').strip()
        filler_smiles = row.get('filler_smiles', '').strip()

        if not polymer_smiles or not filler_smiles:
            logger.warning(f"Row {idx}: Missing SMILES. Skipping.")
            total_skipped += 1
            continue

        # Process Polymer
        poly_G = parse_smiles_to_adjacency(polymer_smiles)
        if poly_G is None:
            logger.warning(f"Row {idx}: Invalid polymer SMILES. Skipping.")
            total_skipped += 1
            continue

        # Process Filler
        fill_G = parse_smiles_to_adjacency(filler_smiles)
        if fill_G is None:
            logger.warning(f"Row {idx}: Invalid filler SMILES. Skipping.")
            total_skipped += 1
            continue

        # Calculate Descriptors
        poly_degree = calculate_degree(poly_G)
        poly_density = calculate_graph_density(poly_G)
        poly_clustering = calculate_clustering_coefficient(poly_G)

        fill_degree = calculate_degree(fill_G)
        fill_density = calculate_graph_density(fill_G)
        fill_clustering = calculate_clustering_coefficient(fill_G)

        # Combined/Interaction descriptors (simple aggregation for now)
        total_nodes = poly_G.number_of_nodes() + fill_G.number_of_nodes()
        total_edges = poly_G.number_of_edges() + fill_G.number_of_edges()

        combined_degree = (poly_degree + fill_degree) / 2.0
        combined_density = (poly_density + fill_density) / 2.0
        combined_clustering = (poly_clustering + fill_clustering) / 2.0

        result_row = {
            'row_id': idx,
            'polymer_smiles': polymer_smiles,
            'filler_smiles': filler_smiles,
            'polymer_degree': poly_degree,
            'polymer_density': poly_density,
            'polymer_clustering': poly_clustering,
            'filler_degree': fill_degree,
            'filler_density': fill_density,
            'filler_clustering': fill_clustering,
            'combined_degree': combined_degree,
            'combined_density': combined_density,
            'combined_clustering': combined_clustering,
            'total_nodes': total_nodes,
            'total_edges': total_edges
        }

        # Preserve original adhesion energy if present
        if 'adhesion_energy' in row:
            result_row['adhesion_energy'] = row['adhesion_energy']

        results.append(result_row)
        total_processed += 1

        if (total_processed + total_skipped) % 100 == 0:
            logger.info(f"Processed {total_processed + total_skipped} rows...")

    logger.info(f"Extraction complete. Processed: {total_processed}, Skipped: {total_skipped}")
    return results


def save_descriptors(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the extracted descriptors to a CSV file.

    Args:
        results: List of dictionaries with descriptor data.
        output_path: Path to the output CSV file.
    """
    if not results:
        logger.error("No results to save.")
        raise ValueError("Cannot save empty results.")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(results[0].keys())

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Saved {len(results)} rows to {output_path}")


def main() -> int:
    """
    Main entry point for the descriptor extraction pipeline.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    logger.info(f"Starting descriptor extraction. Input: {INPUT_PATH}")

    try:
        # 1. Load data
        if not INPUT_PATH.exists():
            logger.error(f"Input file does not exist: {INPUT_PATH}")
            logger.error("Please ensure T016 (curated dataset generation) has completed successfully.")
            return E_INPUT_MISSING

        rows = load_curated_data(INPUT_PATH)
        logger.info(f"Loaded {len(rows)} rows from curated dataset.")

        # 2. Extract descriptors
        descriptors = extract_descriptors(rows)

        if not descriptors:
            logger.error("No valid descriptors could be extracted.")
            return E_NO_DATA

        # 3. Save results
        save_descriptors(descriptors, OUTPUT_PATH)

        logger.info("Descriptor extraction completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return E_INPUT_MISSING
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return E_NO_DATA
    except Exception as e:
        logger.exception(f"Unexpected error during extraction: {e}")
        return E_WRITE_FAILED


if __name__ == "__main__":
    sys.exit(main())
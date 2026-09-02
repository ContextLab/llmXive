"""
Extract hand-crafted graph descriptors (degree, density, clustering coefficient)
from SMILES strings in the curated dataset using RDKit.

Output: data/processed/descriptors.csv
Schema: polymer_smiles, filler_smiles, polymer_degree, polymer_density,
        polymer_clustering, filler_degree, filler_density, filler_clustering
"""
import os
import sys
import logging
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import rdmolops
import networkx as nx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CURATED_DATA_PATH = PROJECT_ROOT / "data" / "curated" / "curated_dataset.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "descriptors.csv"

def parse_smiles_to_adjacency(smiles: str) -> Optional[np.ndarray]:
    """
    Convert a SMILES string to an adjacency matrix using RDKit.

    Args:
        smiles: SMILES string representation of a molecule.

    Returns:
        numpy array adjacency matrix, or None if parsing fails.
    """
    if not smiles or not isinstance(smiles, str):
        return None

    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning(f"Failed to parse SMILES: {smiles}")
            return None

        # Get the adjacency matrix from RDKit
        adj = rdmolops.GetAdjacencyMatrix(mol)
        return adj.astype(float)
    except Exception as e:
        logger.warning(f"Error parsing SMILES '{smiles}': {e}")
        return None

def calculate_degree(adj_matrix: np.ndarray) -> float:
    """
    Calculate the average node degree of the graph.

    Args:
        adj_matrix: NxN adjacency matrix.

    Returns:
        Average degree (float).
    """
    if adj_matrix is None or adj_matrix.size == 0:
        return 0.0

    # Sum of each row gives the degree of that node
    degrees = np.sum(adj_matrix, axis=1)
    if len(degrees) == 0:
        return 0.0
    return float(np.mean(degrees))

def calculate_graph_density(adj_matrix: np.ndarray) -> float:
    """
    Calculate the graph density (ratio of existing edges to possible edges).

    Args:
        adj_matrix: NxN adjacency matrix.

    Returns:
        Density value between 0 and 1.
    """
    if adj_matrix is None or adj_matrix.size == 0:
        return 0.0

    n = adj_matrix.shape[0]
    if n <= 1:
        return 0.0

    # Number of edges (undirected, so divide by 2)
    num_edges = np.sum(adj_matrix) / 2
    # Possible edges in undirected graph: n*(n-1)/2
    max_edges = n * (n - 1) / 2

    if max_edges == 0:
        return 0.0

    return float(num_edges / max_edges)

def calculate_clustering_coefficient(adj_matrix: np.ndarray) -> float:
    """
    Calculate the average clustering coefficient of the graph.

    Args:
        adj_matrix: NxN adjacency matrix.

    Returns:
        Average clustering coefficient.
    """
    if adj_matrix is None or adj_matrix.size == 0:
        return 0.0

    try:
        G = nx.from_numpy_array(adj_matrix)
        # nx.clustering returns a dict of local clustering coefficients
        local_clustering = nx.clustering(G)
        if not local_clustering:
            return 0.0
        return float(np.mean(list(local_clustering.values())))
    except Exception as e:
        logger.warning(f"Error calculating clustering coefficient: {e}")
        return 0.0

def load_curated_data(path: Path) -> pd.DataFrame:
    """
    Load the curated dataset from CSV.

    Args:
        path: Path to the curated dataset CSV.

    Returns:
        DataFrame with columns polymer_smiles, filler_smiles, adhesion_energy.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    if not path.exists():
        raise FileNotFoundError(f"Curated dataset not found at {path}")

    df = pd.read_csv(path)

    required_cols = ['polymer_smiles', 'filler_smiles', 'adhesion_energy']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    logger.info(f"Loaded curated dataset with {len(df)} rows from {path}")
    return df

def extract_descriptors(smiles: str) -> Tuple[float, float, float]:
    """
    Extract degree, density, and clustering coefficient from a single SMILES string.

    Args:
        smiles: SMILES string.

    Returns:
        Tuple of (degree, density, clustering).
    """
    adj = parse_smiles_to_adjacency(smiles)
    if adj is None:
        return 0.0, 0.0, 0.0

    degree = calculate_degree(adj)
    density = calculate_graph_density(adj)
    clustering = calculate_clustering_coefficient(adj)

    return degree, density, clustering

def save_descriptors(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the extracted descriptors to a CSV file.

    Args:
        df: DataFrame with descriptor columns.
        output_path: Path to save the CSV.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved descriptors to {output_path}")

def main():
    """Main entry point for descriptor extraction."""
    logger.info("Starting descriptor extraction from curated dataset...")

    try:
        # Load curated data
        df = load_curated_data(CURATED_DATA_PATH)

        # Initialize lists to store results
        results = []

        for idx, row in df.iterrows():
            polymer_smiles = row['polymer_smiles']
            filler_smiles = row['filler_smiles']

            # Extract descriptors for polymer
            p_degree, p_density, p_clustering = extract_descriptors(polymer_smiles)

            # Extract descriptors for filler
            f_degree, f_density, f_clustering = extract_descriptors(filler_smiles)

            results.append({
                'polymer_smiles': polymer_smiles,
                'filler_smiles': filler_smiles,
                'polymer_degree': p_degree,
                'polymer_density': p_density,
                'polymer_clustering': p_clustering,
                'filler_degree': f_degree,
                'filler_density': f_density,
                'filler_clustering': f_clustering
            })

            if (idx + 1) % 100 == 0:
                logger.info(f"Processed {idx + 1} rows...")

        # Create output DataFrame
        output_df = pd.DataFrame(results)

        # Verify schema
        expected_cols = [
            'polymer_smiles', 'filler_smiles',
            'polymer_degree', 'polymer_density', 'polymer_clustering',
            'filler_degree', 'filler_density', 'filler_clustering'
        ]
        if not all(col in output_df.columns for col in expected_cols):
            raise ValueError("Output DataFrame missing expected columns")

        # Save to disk
        save_descriptors(output_df, OUTPUT_PATH)

        logger.info(f"Descriptor extraction complete. Output: {OUTPUT_PATH}")
        print(f"SUCCESS: Descriptors saved to {OUTPUT_PATH}")

    except FileNotFoundError as e:
        logger.error(f"Data file error: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during descriptor extraction: {e}")
        raise

if __name__ == "__main__":
    main()

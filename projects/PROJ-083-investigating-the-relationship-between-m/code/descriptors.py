import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from pathlib import Path
import numpy as np
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
import networkx as nx
import csv
import hashlib

from code.utils.logger import setup_logger
from code.config import get_config

# Initialize logger
logger = setup_logger(__name__)

def is_connected(mol: Chem.Mol) -> bool:
    """
    Check if the molecular graph is connected.
    Returns True if the graph has exactly one connected component.
    """
    if mol is None:
        return False
    # Get the number of connected components using RDKit
    # GetSubstructMatches with a dummy pattern or use GetMolFrags
    frags = Chem.GetMolFrags(mol, asMols=False)
    return len(frags) == 1

def calculate_wiener_index(mol: Chem.Mol) -> float:
    """
    Calculate the Wiener index (sum of all shortest path distances in the graph).
    """
    if not is_connected(mol):
        raise ValueError("Molecule is not connected; Wiener index undefined.")
    
    # Convert RDKit mol to NetworkX graph
    G = nx.Graph()
    for atom in mol.GetAtoms():
        G.add_node(atom.GetIdx())
    for bond in mol.GetBonds():
        G.add_edge(bond.GetBeginAtomIdx(), bond.GetEndAtomIdx())
    
    # Calculate all pairs shortest paths
    lengths = dict(nx.all_pairs_shortest_path_length(G))
    total_distance = 0
    for source in lengths:
        for target, dist in lengths[source].items():
            if source < target: # Sum each pair once
                total_distance += dist
    
    return float(total_distance)

def calculate_balaban_index(mol: Chem.Mol) -> float:
    """
    Calculate the Balaban J index.
    J = (M / (M - N + 1)) * sum(1 / sqrt(d_i * d_j)) for all edges (i, j)
    where M is number of edges, N is number of vertices, d_i is degree of vertex i.
    """
    if not is_connected(mol):
        raise ValueError("Molecule is not connected; Balaban index undefined.")

    G = nx.Graph()
    for atom in mol.GetAtoms():
        G.add_node(atom.GetIdx())
    for bond in mol.GetBonds():
        G.add_edge(bond.GetBeginAtomIdx(), bond.GetEndAtomIdx())
    
    N = G.number_of_nodes()
    M = G.number_of_edges()
    
    if M - N + 1 == 0:
        return 0.0 # Avoid division by zero for trees/cycles where M = N-1

    sum_term = 0.0
    for u, v in G.edges():
        deg_u = G.degree[u]
        deg_v = G.degree[v]
        if deg_u == 0 or deg_v == 0:
            continue
        sum_term += 1.0 / np.sqrt(deg_u * deg_v)
    
    return float((M / (M - N + 1)) * sum_term)

def calculate_zagreb_index(mol: Chem.Mol) -> float:
    """
    Calculate the first Zagreb index (sum of squared degrees).
    M1 = sum(deg(v)^2) for all vertices v.
    """
    if not is_connected(mol):
        raise ValueError("Molecule is not connected; Zagreb index undefined.")

    G = nx.Graph()
    for atom in mol.GetAtoms():
        G.add_node(atom.GetIdx())
    for bond in mol.GetBonds():
        G.add_edge(bond.GetBeginAtomIdx(), bond.GetEndAtomIdx())
    
    total = 0
    for node in G.nodes():
        deg = G.degree[node]
        total += deg * deg
    
    return float(total)

class TopologicalDescriptorCalculator:
    """
    Class to calculate topological descriptors for a given RDKit molecule.
    Handles connectivity checks and delegates to specific calculators.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def calculate(self, mol: Chem.Mol) -> Dict[str, float]:
        """
        Calculate Wiener, Balaban, and Zagreb indices.
        Raises ValueError if molecule is disconnected.
        """
        if not is_connected(mol):
            raise ValueError("Disconnected graph detected.")
        
        return {
            "wiener": calculate_wiener_index(mol),
            "balaban": calculate_balaban_index(mol),
            "zagreb": calculate_zagreb_index(mol)
        }

def calculate_descriptors_for_smiles(smiles: str, reaction_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Parse SMILES, check connectivity, and calculate descriptors.
    Returns a dict with descriptors if valid, or None if disconnected (to be handled by caller).
    Raises ValueError if SMILES is invalid.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")
    
    if not is_connected(mol):
        return None
    
    try:
        descriptors = TopologicalDescriptorCalculator().calculate(mol)
        return {
            "smiles": smiles,
            "reaction_id": reaction_id,
            **descriptors
        }
    except Exception as e:
        logger.error(f"Error calculating descriptors for {smiles}: {e}")
        return None

def log_disconnected_graphs(disconnected_records: List[Dict[str, str]], output_path: str):
    """
    Log disconnected graphs to a CSV file with a checksum.
    Output Schema: smiles, reaction_id, error_type
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ["smiles", "reaction_id", "error_type"]
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in disconnected_records:
            writer.writerow(record)
    
    # Calculate checksum
    checksum = hashlib.md5(output_file.read_bytes()).hexdigest()
    logger.info(f"Disconnected graphs logged to {output_path} (Checksum: {checksum})")
    return checksum

def main():
    """
    Entry point for testing or running descriptor calculations.
    """
    logger.info("Running descriptor calculations main entry point.")
    # Example usage logic can be added here if needed for CLI
    pass

if __name__ == "__main__":
    main()

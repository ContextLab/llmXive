import logging
from typing import List, Tuple, Optional, Dict, Any
import os
import logging.handlers
from pathlib import Path
import rdkit
from rdkit import Chem
from rdkit.Chem import rdmolops
import networkx as nx

def setup_invalid_smiles_logger(log_file: str = "data/logs/invalid_smiles.log") -> logging.Logger:
    logger = logging.getLogger("invalid_smiles")
    logger.setLevel(logging.DEBUG)
    
    # Ensure directory exists
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    return logger

def log_invalid_smiles(logger: logging.Logger, smiles: str, reason: str) -> None:
    logger.error(f"Invalid SMILES: {smiles} | Reason: {reason}")

def is_valid_molecule(smiles: str) -> bool:
    """Checks if a SMILES string represents a valid molecule."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        return mol is not None
    except Exception:
        return False

def build_molecular_graph(smiles: str) -> Optional[nx.Graph]:
    """
    Builds a NetworkX graph from an RDKit molecule.
    Nodes: Atoms
    Edges: Bonds
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    
    G = nx.Graph()
    
    # Add atoms
    for atom in mol.GetAtoms():
        G.add_node(atom.GetIdx(), symbol=atom.GetSymbol(), atomic_num=atom.GetAtomicNum())
    
    # Add bonds
    for bond in mol.GetBonds():
        G.add_edge(bond.GetBeginAtomIdx(), bond.GetEndAtomIdx(), order=bond.GetBondType())
    
    return G

def get_molecular_weight(mol: Chem.Mol) -> float:
    """Calculates molecular weight."""
    return sum(atom.GetAtomicWeight() for atom in mol.GetAtoms())

def build_graphs_from_smiles_list(smiles_list: List[str]) -> List[Tuple[str, Optional[nx.Graph]]]:
    """
    Builds graphs for a list of SMILES.
    Returns list of (smiles, graph_or_None).
    """
    results = []
    for smiles in smiles_list:
        g = build_molecular_graph(smiles)
        results.append((smiles, g))
    return results

def validate_graph_structure(G: nx.Graph) -> bool:
    """Validates that the graph is non-empty and connected (or has components)."""
    if G.number_of_nodes() == 0:
        return False
    # Graphs can be disconnected, so we don't strictly require connectivity here
    # But we require at least one node
    return True

def main():
    """Main entry point for testing graph builder."""
    logger = setup_invalid_smiles_logger()
    test_smiles = ["CCO", "invalid_smiles", "c1ccccc1"]
    for smi in test_smiles:
        if is_valid_molecule(smi):
            g = build_molecular_graph(smi)
            print(f"{smi}: Valid, Nodes={g.number_of_nodes()}, Edges={g.number_of_edges()}")
        else:
            log_invalid_smiles(logger, smi, "RDKit parsing failed")
            print(f"{smi}: Invalid")

if __name__ == "__main__":
    main()

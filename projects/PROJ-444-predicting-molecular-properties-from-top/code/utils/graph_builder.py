import logging
from typing import List, Tuple, Optional, Dict, Any
import os
import logging.handlers
from pathlib import Path
import rdkit
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors
import networkx as nx

def setup_invalid_smiles_logger(log_path: str) -> logging.Logger:
    """Setup a logger specifically for invalid SMILES."""
    logger = logging.getLogger('invalid_smiles')
    logger.setLevel(logging.WARNING)
    
    # Avoid adding handlers multiple times
    if not logger.handlers:
        log_dir = Path(log_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        handler = logging.FileHandler(log_path)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def log_invalid_smiles(logger: logging.Logger, smiles: str, reason: str):
    """Log an invalid SMILES string."""
    logger.warning(f"Invalid SMILES: {smiles} | Reason: {reason}")

def is_valid_molecule(smiles: str) -> Optional[Chem.Mol]:
    """Check if SMILES is valid and return RDKit Mol object."""
    if not smiles or not isinstance(smiles, str):
        return None
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        # Basic sanity check
        if mol.GetNumAtoms() == 0:
            return None
        return mol
    except Exception:
        return None

def build_molecular_graph(mol: Chem.Mol) -> nx.Graph:
    """
    Convert an RDKit molecule to a NetworkX graph.
    Nodes are atoms, edges are bonds.
    Attributes include atomic number, formal charge, etc.
    """
    G = nx.Graph()
    
    for atom in mol.GetAtoms():
        G.add_node(
            atom.GetIdx(),
            atomic_num=atom.GetAtomicNum(),
            formal_charge=atom.GetFormalCharge(),
            num_hs=atom.GetNumExplicitHs() + atom.GetNumImplicitHs(),
            aromatic=atom.GetIsAromatic(),
            hybridization=str(atom.GetHybridization())
        )
    
    for bond in mol.GetBonds():
        G.add_edge(
            bond.GetBeginAtomIdx(),
            bond.GetEndAtomIdx(),
            bond_type=bond.GetBondType(),
            conjugated=bond.GetIsConjugated()
        )
    
    return G

def get_molecular_weight(mol: Chem.Mol) -> float:
    """Get molecular weight."""
    return Descriptors.MolWt(mol)

def build_graphs_from_smiles_list(smiles_list: List[str]) -> List[Tuple[str, Optional[nx.Graph], Optional[str]]]:
    """
    Build graphs for a list of SMILES.
    Returns list of (smiles, graph, error_msg).
    """
    results = []
    logger = setup_invalid_smiles_logger("data/logs/invalid_smiles.log")
    
    for smiles in smiles_list:
        mol = is_valid_molecule(smiles)
        if mol is None:
            log_invalid_smiles(logger, smiles, "RDKit parsing failed")
            results.append((smiles, None, "Invalid SMILES"))
            continue
        
        try:
            graph = build_molecular_graph(mol)
            results.append((smiles, graph, None))
        except Exception as e:
            log_invalid_smiles(logger, smiles, str(e))
            results.append((smiles, None, str(e)))
    
    return results

def validate_graph_structure(G: nx.Graph) -> bool:
    """Validate that the graph has nodes and edges."""
    if G.number_of_nodes() == 0:
        return False
    return True

def main():
    # Example usage
    smiles = "CCO"
    mol = is_valid_molecule(smiles)
    if mol:
        G = build_molecular_graph(mol)
        print(f"Molecule: {smiles}, Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
    else:
        print(f"Invalid SMILES: {smiles}")

if __name__ == "__main__":
    main()

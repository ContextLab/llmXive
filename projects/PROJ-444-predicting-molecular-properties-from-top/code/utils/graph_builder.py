import logging
from typing import List, Tuple, Optional, Dict, Any
import os
import logging.handlers
from pathlib import Path
import rdkit
from rdkit import Chem
from rdkit.Chem import Descriptors

# --- Logging Setup for Invalid SMILES (T015) ---

_invalid_smiles_logger = None

def setup_invalid_smiles_logger(log_path: str = "data/logs/invalid_smiles.log") -> logging.Logger:
    """
    Sets up a dedicated logger for invalid SMILES strings.
    Creates the directory if it doesn't exist.
    """
    global _invalid_smiles_logger
    
    if _invalid_smiles_logger is not None:
        return _invalid_smiles_logger

    log_file_path = Path(log_path)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("invalid_smiles")
    logger.setLevel(logging.WARNING)

    # Avoid adding duplicate handlers if called multiple times
    if not logger.handlers:
        handler = logging.FileHandler(log_file_path, mode='a')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    _invalid_smiles_logger = logger
    return logger

def log_invalid_smiles(smiles: str, reason: str = "Parsing failed") -> None:
    """
    Logs an invalid SMILES string to the dedicated log file.
    """
    logger = setup_invalid_smiles_logger()
    logger.warning(f"Invalid SMILES '{smiles}': {reason}")

# --- Molecule Validation & Graph Construction ---

def is_valid_molecule(smiles: str) -> bool:
    """
    Checks if a SMILES string can be parsed into a valid RDKit molecule.
    Logs invalid molecules if the logger is set up.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            log_invalid_smiles(smiles, "RDKit returned None")
            return False
        # Basic validity check: ensure it has at least one atom
        if mol.GetNumAtoms() == 0:
            log_invalid_smiles(smiles, "Molecule has no atoms")
            return False
        return True
    except Exception as e:
        log_invalid_smiles(smiles, f"Exception during parsing: {str(e)}")
        return False

def build_molecular_graph(mol: Chem.Mol) -> Any:
    """
    Converts an RDKit Mol object to a NetworkX graph.
    Nodes represent atoms, edges represent bonds.
    Attributes include atomic number and bond order.
    """
    import networkx as nx
    
    G = nx.Graph()
    
    # Add atoms as nodes
    for atom in mol.GetAtoms():
        G.add_node(atom.GetIdx(), atomic_num=atom.GetAtomicNum(), symbol=atom.GetSymbol())
    
    # Add bonds as edges
    for bond in mol.GetBonds():
        G.add_edge(
            bond.GetBeginAtomIdx(),
            bond.GetEndAtomIdx(),
            bond_order=bond.GetBondTypeAsDouble()
        )
    
    return G

def get_molecular_weight(mol: Chem.Mol) -> float:
    """
    Calculates the molecular weight of an RDKit Mol object.
    """
    return Descriptors.MolWt(mol)

def build_graphs_from_smiles_list(smiles_list: List[str], valid_only: bool = True) -> List[Tuple[str, Any]]:
    """
    Builds a list of (smiles, graph) tuples from a list of SMILES strings.
    
    Args:
        smiles_list: List of SMILES strings.
        valid_only: If True, skips invalid SMILES (logs them). If False, raises on invalid.
    
    Returns:
        List of tuples (smiles, networkx_graph).
    """
    graphs = []
    for smiles in smiles_list:
        if not is_valid_molecule(smiles):
            if valid_only:
                continue
            else:
                raise ValueError(f"Invalid SMILES encountered: {smiles}")
        
        mol = Chem.MolFromSmiles(smiles)
        graph = build_molecular_graph(mol)
        graphs.append((smiles, graph))
    
    return graphs

def validate_graph_structure(G: Any) -> bool:
    """
    Validates that a graph has at least one node and is not trivial.
    """
    return G.number_of_nodes() > 0 and G.number_of_edges() >= 0

def main():
    """
    CLI entry point for testing graph builder utilities.
    """
    import sys
    test_smiles = [
        "CCO",       # Valid: Ethanol
        "INVALID",   # Invalid
        "c1ccccc1",  # Valid: Benzene
        "C1CCCCC1",  # Valid: Cyclohexane
        "CC(C)C1=CC=CC=C1", # Valid: Isopropylbenzene
    ]
    
    print("Testing Graph Builder...")
    for s in test_smiles:
        if is_valid_molecule(s):
            g = build_molecular_graph(Chem.MolFromSmiles(s))
            print(f"SMILES: {s} -> Nodes: {g.number_of_nodes()}, Edges: {g.number_of_edges()}")
        else:
            print(f"SMILES: {s} -> INVALID (Logged)")
    
    print(f"\nCheck data/logs/invalid_smiles.log for logged errors.")

if __name__ == "__main__":
    main()

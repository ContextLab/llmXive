import logging
from typing import List, Tuple, Optional, Dict, Any
import os
import logging.handlers
from pathlib import Path
import rdkit
from rdkit import Chem
from rdkit.Chem import Descriptors

def setup_invalid_smiles_logger(log_file: str) -> logging.Logger:
    """
    Setup a dedicated logger for invalid SMILES.
    
    Args:
        log_file: Path to the log file.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("invalid_smiles")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        # Ensure directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def log_invalid_smiles(smiles: str, reason: str, logger: Optional[logging.Logger] = None):
    """
    Log an invalid SMILES string.
    
    Args:
        smiles: The invalid SMILES string.
        reason: Reason for invalidity.
        logger: Logger instance (uses default if None).
    """
    if logger is None:
        logger = logging.getLogger("invalid_smiles")
    
    if not logger.handlers:
        # Setup default logger if none exists
        setup_invalid_smiles_logger("data/logs/invalid_smiles.log")
        logger = logging.getLogger("invalid_smiles")
    
    logger.info(f"Invalid SMILES: {smiles} - Reason: {reason}")

def is_valid_molecule(smiles: str) -> bool:
    """
    Check if a SMILES string represents a valid molecule.
    
    Args:
        smiles: SMILES string to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    if not smiles or not isinstance(smiles, str):
        return False
    
    try:
        mol = Chem.MolFromSmiles(smiles)
        return mol is not None
    except Exception:
        return False

def build_molecular_graph(mol: Chem.Mol) -> Optional[Any]:
    """
    Build a NetworkX graph from an RDKit molecule.
    
    Args:
        mol: RDKit molecule object.
        
    Returns:
        NetworkX graph or None if invalid.
    """
    if mol is None:
        return None
    
    import networkx as nx
    
    graph = nx.Graph()
    
    # Add atoms as nodes
    for atom in mol.GetAtoms():
        graph.add_node(
            atom.GetIdx(),
            symbol=atom.GetSymbol(),
            atomic_num=atom.GetAtomicNum(),
            degree=atom.GetDegree(),
            formal_charge=atom.GetFormalCharge()
        )
    
    # Add bonds as edges with weight (inverse of bond order)
    for bond in mol.GetBonds():
        start_idx = bond.GetBeginAtomIdx()
        end_idx = bond.GetEndAtomIdx()
        bond_order = bond.GetBondTypeAsDouble()
        
        # Weight is inverse of bond order (higher order = shorter distance)
        weight = 1.0 / bond_order if bond_order > 0 else 1.0
        
        graph.add_edge(start_idx, end_idx, weight=weight, bond_type=bond.GetBondType())
    
    return graph

def get_molecular_weight(mol: Chem.Mol) -> Optional[float]:
    """
    Calculate molecular weight of an RDKit molecule.
    
    Args:
        mol: RDKit molecule object.
        
    Returns:
        Molecular weight or None if invalid.
    """
    if mol is None:
        return None
    
    try:
        return Descriptors.MolWt(mol)
    except Exception:
        return None

def build_graphs_from_smiles_list(
    smiles_list: List[str],
    logger: Optional[logging.Logger] = None
) -> List[Tuple[str, Optional[Any], Optional[float]]]:
    """
    Build graphs from a list of SMILES strings.
    
    Args:
        smiles_list: List of SMILES strings.
        logger: Logger instance for invalid SMILES.
        
    Returns:
        List of (smiles, graph, molecular_weight) tuples.
    """
    results = []
    
    if logger is None:
        logger = logging.getLogger("graph_builder")
    
    for smiles in smiles_list:
        if not is_valid_molecule(smiles):
            log_invalid_smiles(smiles, "Failed SMILES validation", logger)
            results.append((smiles, None, None))
            continue
        
        mol = Chem.MolFromSmiles(smiles)
        graph = build_molecular_graph(mol)
        mw = get_molecular_weight(mol)
        
        results.append((smiles, graph, mw))
    
    return results

def validate_graph_structure(graph: Any) -> bool:
    """
    Validate the structure of a molecular graph.
    
    Args:
        graph: NetworkX graph to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    if graph is None:
        return False
    
    try:
        # Check for nodes
        if graph.number_of_nodes() == 0:
            return False
        
        # Check for self-loops (should not exist in valid molecular graphs)
        if graph.number_of_selfloops() > 0:
            return False
        
        # Check edge weights exist
        for u, v, data in graph.edges(data=True):
            if 'weight' not in data:
                return False
        
        return True
    except Exception:
        return False

def main():
    """Main entry point for graph builder utilities."""
    print("Graph builder utilities module loaded successfully.")

if __name__ == "__main__":
    main()

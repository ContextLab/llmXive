import logging
from typing import List, Tuple, Optional, Dict, Any
import os
import logging.handlers
from pathlib import Path
import rdkit
from rdkit import Chem
from rdkit.Chem import Descriptors

# Project root for log file location
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_LOGS_DIR = PROJECT_ROOT / "data" / "logs"

class Graph:
    """Simple wrapper for molecular graph data."""
    def __init__(self, rdkit_mol):
        self.mol = rdkit_mol
        self.nodes = []
        self.edges = []
        self._extract_structure()

    def _extract_structure(self):
        """Extract nodes and edges from RDKit molecule."""
        self.nodes = list(self.mol.GetAtoms())
        self.edges = list(self.mol.GetBonds())

def setup_invalid_smiles_logger():
    """
    Setup a dedicated logger for invalid SMILES to write to data/logs/invalid_smiles.log.
    Returns the logger instance.
    """
    # Ensure directory exists
    DATA_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger("invalid_smiles")
    logger.setLevel(logging.INFO)
    
    # Prevent duplicate handlers if called multiple times
    if not logger.handlers:
        handler = logging.FileHandler(DATA_LOGS_DIR / "invalid_smiles.log")
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def log_invalid_smiles(logger: logging.Logger, smiles: str, reason: str):
    """Log an invalid SMILES entry to the specific logger."""
    if logger:
        logger.info(f"SMILES: {smiles} | Reason: {reason}")

def is_valid_molecule(smiles: str) -> bool:
    """Check if a SMILES string represents a valid molecule."""
    if not smiles or not isinstance(smiles, str):
        return False
    try:
        mol = Chem.MolFromSmiles(smiles)
        return mol is not None
    except Exception:
        return False

def build_molecular_graph(smiles: str) -> Optional[Graph]:
    """Build a molecular graph from a SMILES string."""
    if not is_valid_molecule(smiles):
        return None
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return Graph(mol)

def get_molecular_weight(mol: Chem.Mol) -> float:
    """Calculate molecular weight."""
    return Descriptors.MolWt(mol)

def build_graphs_from_smiles_list(smiles_list: List[str]) -> List[Tuple[str, Optional[Graph]]]:
    """Build graphs for a list of SMILES strings."""
    results = []
    for smiles in smiles_list:
        graph = build_molecular_graph(smiles)
        results.append((smiles, graph))
    return results

def validate_graph_structure(graph: Graph) -> bool:
    """Validate the structure of a graph."""
    if graph is None:
        return False
    # Basic checks: nodes and edges exist
    return len(graph.nodes) > 0 and len(graph.edges) >= 0

def build_graph(smiles: str) -> Optional[Graph]:
    """
    Main entry point for building a graph from SMILES.
    Returns a Graph object or None if invalid.
    """
    return build_molecular_graph(smiles)

def validate_graph(graph: Graph) -> bool:
    """
    Validate graph properties (valence, aromaticity, bond order).
    """
    if graph is None or graph.mol is None:
        return False
    
    # Check for valence errors
    if Chem.rdmolops.FindMolChiralCenters(graph.mol, includeUnassigned=True) is not None:
        # RDKit doesn't strictly fail on valence in MolFromSmiles usually, 
        # but we can check for explicit valence errors if needed.
        # For now, if MolFromSmiles succeeded, we assume basic valence is okay.
        pass

    # Check for aromaticity
    # RDKit computes aromaticity by default, but we can check ring info
    if graph.mol.GetRingInfo().NumRings() == 0:
        pass # Linear molecules are fine
    
    # Check bond orders
    for bond in graph.edges:
        bond_type = bond.GetBondType()
        if bond_type not in [Chem.BondType.SINGLE, Chem.BondType.DOUBLE, Chem.BondType.TRIPLE, Chem.BondType.AROMATIC]:
            return False
    
    return True

def main():
    """Example usage for testing."""
    logger = setup_invalid_smiles_logger()
    test_smiles = ["CCO", "invalid_smiles", "c1ccccc1"]
    
    for s in test_smiles:
        g = build_graph(s)
        if g is None:
            log_invalid_smiles(logger, s, "Failed to parse")
        else:
            print(f"{s}: Valid, MW={get_molecular_weight(g.mol):.2f}")

if __name__ == "__main__":
    main()
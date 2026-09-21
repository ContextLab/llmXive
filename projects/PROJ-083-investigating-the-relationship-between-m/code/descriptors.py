import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import numpy as np
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors
from rdkit.Chem.rdmolops import GetAdjacencyMatrix
import networkx as nx

from code.utils.logger import setup_logger
from code.config import get_config

logger = setup_logger(__name__)

class TopologicalDescriptorCalculator:
    """
    Calculator for topological descriptors (Wiener, Balaban, Zagreb indices).
    Includes validation for graph connectivity (FR-002).
    """

    def __init__(self):
        self.config = get_config()
        self.logger = logger

    def _is_connected(self, mol: Chem.Mol) -> bool:
        """
        Check if the molecular graph is connected.
        Returns False if the graph is disconnected or invalid.
        """
        if mol is None:
            return False
        try:
            # RDKit GetNumAtoms returns 0 for empty/invalid mols
            if mol.GetNumAtoms() == 0:
                return False
            
            # Get the number of connected components
            # RDKit's GetMolFrags returns a tuple of atom indices for each fragment
            frags = Chem.GetMolFrags(mol, asMols=False, sanitizeFrags=False)
            return len(frags) == 1
        except Exception as e:
            self.logger.warning(f"Failed to check connectivity for molecule: {e}")
            return False

    def calculate_wiener_index(self, mol: Chem.Mol) -> Optional[float]:
        """Calculate Wiener index (sum of all shortest path distances)."""
        if not self._is_connected(mol):
            return None
        try:
            # RDKit implementation
            return rdMolDescriptors.CalcWienerIndex(mol)
        except Exception as e:
            self.logger.warning(f"Wiener index calculation failed: {e}")
            return None

    def calculate_balaban_index(self, mol: Chem.Mol) -> Optional[float]:
        """Calculate Balaban J index."""
        if not self._is_connected(mol):
            return None
        try:
            # RDKit implementation
            return rdMolDescriptors.CalcBalabanJ(mol)
        except Exception as e:
            self.logger.warning(f"Balaban index calculation failed: {e}")
            return None

    def calculate_zagreb_index(self, mol: Chem.Mol) -> Optional[float]:
        """Calculate First Zagreb index (sum of squared degrees)."""
        if not self._is_connected(mol):
            return None
        try:
            # RDKit implementation
            return rdMolDescriptors.CalcZagrebIndex(mol)
        except Exception as e:
            self.logger.warning(f"Zagreb index calculation failed: {e}")
            return None

    def calculate_descriptors(self, mol: Chem.Mol) -> Dict[str, Any]:
        """
        Calculate all descriptors for a single molecule.
        Returns a dictionary with values or None if invalid/disconnected.
        """
        if not self._is_connected(mol):
            return {
                "wiener": None,
                "balaban": None,
                "zagreb": None,
                "is_valid_topology": False,
                "reason": "Disconnected graph or invalid molecule"
            }
        
        wiener = self.calculate_wiener_index(mol)
        balaban = self.calculate_balaban_index(mol)
        zagreb = self.calculate_zagreb_index(mol)

        return {
            "wiener": wiener,
            "balaban": balaban,
            "zagreb": zagreb,
            "is_valid_topology": True,
            "reason": None
        }

def calculate_descriptors_for_smiles(smiles: str) -> Dict[str, Any]:
    """
    Wrapper function to calculate descriptors from a SMILES string.
    Flags invalid topology for disconnected graphs.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return {
                "wiener": None,
                "balaban": None,
                "zagreb": None,
                "is_valid_topology": False,
                "reason": "Failed to parse SMILES"
            }
        
        calculator = TopologicalDescriptorCalculator()
        return calculator.calculate_descriptors(mol)
    except Exception as e:
        logger.error(f"Error calculating descriptors for SMILES '{smiles}': {e}")
        return {
            "wiener": None,
            "balaban": None,
            "zagreb": None,
            "is_valid_topology": False,
            "reason": f"Calculation error: {str(e)}"
        }

def main():
    """
    Main entry point for descriptor calculation.
    Reads from data/processed/eas_reactions.csv, calculates descriptors,
    and writes to data/processed/descriptors.csv, excluding invalid topologies.
    """
    config = get_config()
    input_path = Path(config.DATA_PROCESSED) / "eas_reactions.csv"
    output_path = Path(config.DATA_PROCESSED) / "descriptors.csv"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return

    logger.info(f"Reading reactions from {input_path}")
    
    import pandas as pd
    df = pd.read_csv(input_path)
    
    calculator = TopologicalDescriptorCalculator()
    results = []
    invalid_count = 0
    total_count = len(df)

    logger.info(f"Processing {total_count} reactions...")

    for idx, row in df.iterrows():
        smiles = row.get('reactant_smiles')
        if not smiles:
            invalid_count += 1
            continue
        
        desc = calculator.calculate_descriptors_for_smiles(smiles)
        
        if not desc['is_valid_topology']:
            invalid_count += 1
            # Log the exclusion reason for audit
            logger.debug(f"Excluded row {idx}: {desc['reason']}")
            continue

        results.append({
            'row_id': idx,
            'reactant_smiles': smiles,
            'wiener': desc['wiener'],
            'balaban': desc['balaban'],
            'zagreb': desc['zagreb'],
            'is_valid_topology': True
        })

    # Create output DataFrame
    if not results:
        logger.warning("No valid topologies found. Output file will be empty.")
        pd.DataFrame(columns=['row_id', 'reactant_smiles', 'wiener', 'balaban', 'zagreb', 'is_valid_topology']).to_csv(output_path, index=False)
    else:
        out_df = pd.DataFrame(results)
        out_df.to_csv(output_path, index=False)

    logger.info(f"Descriptor calculation complete.")
    logger.info(f"Total processed: {total_count}")
    logger.info(f"Valid topologies: {len(results)}")
    logger.info(f"Invalid topologies (excluded): {invalid_count}")
    logger.info(f"Output written to: {output_path}")

if __name__ == "__main__":
    main()

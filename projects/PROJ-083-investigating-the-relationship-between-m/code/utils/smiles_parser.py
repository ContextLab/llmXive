"""
SMILES Parser and Base Data Loader Utilities.

This module provides core functionality for parsing SMILES strings into molecular
graph representations using RDKit, validating chemical structures, and handling
malformed data gracefully.

It serves as the foundational data loader for the molecular topology pipeline.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple

from rdkit import Chem
from rdkit.Chem import AllChem

# Configure module logger
logger = logging.getLogger(__name__)


class SMILESParser:
    """
    Utility class for parsing SMILES strings into RDKit Mol objects.

    This class handles:
    - Parsing SMILES strings
    - Sanitization and validation
    - Error reporting for malformed inputs
    """

    def __init__(self, sanitize: bool = True):
        """
        Initialize the parser.

        Args:
            sanitize: If True, perform RDKit sanitization (valence checks,
                      aromaticity perception, etc.) on parsed molecules.
        """
        self.sanitize = sanitize

    def parse(self, smiles: str) -> Optional[Chem.Mol]:
        """
        Parse a single SMILES string into an RDKit Mol object.

        Args:
            smiles: The SMILES string to parse.

        Returns:
            An RDKit Mol object if parsing is successful, None otherwise.
        """
        if not smiles or not isinstance(smiles, str):
            logger.warning(f"Invalid input type or empty string: {type(smiles)}")
            return None

        try:
            mol = Chem.MolFromSmiles(smiles, sanitize=self.sanitize)
            if mol is None:
                logger.warning(f"Failed to parse SMILES: {smiles}")
                return None

            # Additional validation: ensure the molecule has at least one atom
            if mol.GetNumAtoms() == 0:
                logger.warning(f"Parsed molecule has no atoms: {smiles}")
                return None

            return mol

        except Exception as e:
            logger.error(f"Exception occurred while parsing SMILES '{smiles}': {e}")
            return None

    def parse_batch(self, smiles_list: List[str]) -> List[Tuple[str, Optional[Chem.Mol]]]:
        """
        Parse a list of SMILES strings.

        Args:
            smiles_list: List of SMILES strings.

        Returns:
            A list of tuples (original_smiles, mol_object).
            Mol object is None if parsing failed.
        """
        results = []
        for smiles in smiles_list:
            mol = self.parse(smiles)
            results.append((smiles, mol))
        return results

    def get_molecular_formula(self, mol: Chem.Mol) -> str:
        """
        Get the molecular formula of a molecule.

        Args:
            mol: RDKit Mol object.

        Returns:
            Molecular formula string (e.g., "C6H6").
        """
        if mol is None:
            return ""
        return Chem.rdMolDescriptors.CalcMolFormula(mol)

    def get_molecular_weight(self, mol: Chem.Mol) -> float:
        """
        Get the molecular weight of a molecule.

        Args:
            mol: RDKit Mol object.

        Returns:
            Molecular weight in g/mol.
        """
        if mol is None:
            return 0.0
        return Chem.rdMolDescriptors.CalcExactMolWt(mol)

    def is_valid_aromatic_ring(self, mol: Chem.Mol) -> bool:
        """
        Check if the molecule contains at least one aromatic ring.

        Args:
            mol: RDKit Mol object.

        Returns:
            True if at least one aromatic ring is present, False otherwise.
        """
        if mol is None:
            return False
        # Check for aromatic bonds
        for bond in mol.GetBonds():
            if bond.GetIsAromatic():
                return True
        return False


class BaseDataLoader:
    """
    Base class for loading chemical data from various sources.

    This class provides common functionality for:
    - Loading SMILES from files (CSV, TXT)
    - Validating data integrity
    - Filtering based on chemical properties
    """

    def __init__(self, parser: Optional[SMILESParser] = None):
        """
        Initialize the data loader.

        Args:
            parser: SMILESParser instance to use. If None, a default is created.
        """
        self.parser = parser or SMILESParser()
        self.logger = logging.getLogger(self.__class__.__name__)

    def load_from_file(self, file_path: str, smiles_column: str = "smiles") -> List[Dict[str, Any]]:
        """
        Load SMILES data from a CSV file.

        Args:
            file_path: Path to the CSV file.
            smiles_column: Name of the column containing SMILES strings.

        Returns:
            List of dictionaries containing parsed data.
        """
        import pandas as pd

        try:
            df = pd.read_csv(file_path)
            if smiles_column not in df.columns:
                raise ValueError(f"Column '{smiles_column}' not found in {file_path}")

            records = []
            for idx, row in df.iterrows():
                smiles = str(row[smiles_column])
                mol = self.parser.parse(smiles)

                record = {
                    "id": idx,
                    "smiles": smiles,
                    "mol": mol,
                    "valid": mol is not None
                }

                if mol:
                    record["formula"] = self.parser.get_molecular_formula(mol)
                    record["molecular_weight"] = self.parser.get_molecular_weight(mol)
                    record["has_aromatic_ring"] = self.parser.is_valid_aromatic_ring(mol)

                records.append(record)

            return records

        except FileNotFoundError:
            self.logger.error(f"File not found: {file_path}")
            raise
        except Exception as e:
            self.logger.error(f"Error loading file {file_path}: {e}")
            raise

    def filter_valid(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter records to keep only valid molecules.

        Args:
            records: List of record dictionaries.

        Returns:
            Filtered list of valid records.
        """
        return [r for r in records if r.get("valid", False)]

    def get_statistics(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate basic statistics for a list of records.

        Args:
            records: List of record dictionaries.

        Returns:
            Dictionary with statistics.
        """
        total = len(records)
        valid = sum(1 for r in records if r.get("valid", False))
        aromatic = sum(1 for r in records if r.get("has_aromatic_ring", False))

        weights = [r["molecular_weight"] for r in records if r.get("valid", False)]

        return {
            "total_records": total,
            "valid_molecules": valid,
            "invalid_molecules": total - valid,
            "molecules_with_aromatic_rings": aromatic,
            "valid_percentage": (valid / total * 100) if total > 0 else 0,
            "avg_molecular_weight": sum(weights) / len(weights) if weights else 0,
            "min_molecular_weight": min(weights) if weights else 0,
            "max_molecular_weight": max(weights) if weights else 0
        }


def load_smiles_file(file_path: str, smiles_column: str = "smiles") -> List[Dict[str, Any]]:
    """
    Convenience function to load SMILES from a CSV file.

    Args:
        file_path: Path to the CSV file.
        smiles_column: Name of the column containing SMILES strings.

    Returns:
        List of dictionaries containing parsed data.
    """
    loader = BaseDataLoader()
    return loader.load_from_file(file_path, smiles_column)


def parse_smiles(smiles: str) -> Optional[Chem.Mol]:
    """
    Convenience function to parse a single SMILES string.

    Args:
        smiles: The SMILES string to parse.

    Returns:
        RDKit Mol object or None if parsing fails.
    """
    parser = SMILESParser()
    return parser.parse(smiles)

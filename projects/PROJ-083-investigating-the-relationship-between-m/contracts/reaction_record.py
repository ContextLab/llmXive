"""
Schema definitions for ReactionRecord.

This module defines the data structure for storing parsed reaction data,
including reactants, products, and metadata required for topological analysis.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from rdkit import Chem


@dataclass
class ReactionRecord:
    """
    Represents a single reaction record from the USPTO-50k dataset.

    Attributes:
        reaction_id: Unique identifier for the reaction (e.g., from USPTO).
        smiles_reactants: List of SMILES strings for reactant molecules.
        smiles_products: List of SMILES strings for product molecules.
        reaction_smiles: The full reaction SMILES string (reactants >> products).
        metadata: Additional metadata from the source (e.g., conditions, citations).
        reactant_mols: Parsed RDKit Mol objects for reactants (computed on demand).
        product_mols: Parsed RDKit Mol objects for products (computed on demand).
        is_eas: Boolean flag indicating if this reaction is classified as Electrophilic Aromatic Substitution.
        error_message: Optional error message if parsing or validation failed.
    """
    reaction_id: str
    smiles_reactants: List[str]
    smiles_products: List[str]
    reaction_smiles: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    reactant_mols: List[Chem.Mol] = field(default_factory=list)
    product_mols: List[Chem.Mol] = field(default_factory=list)
    is_eas: bool = False
    error_message: Optional[str] = None

    def validate(self) -> bool:
        """
        Validates the record by attempting to parse SMILES into RDKit Mol objects.
        
        Returns:
            bool: True if all SMILES parse successfully, False otherwise.
        """
        if not self.smiles_reactants or not self.smiles_products:
            self.error_message = "Missing reactant or product SMILES"
            return False

        self.reactant_mols = []
        self.product_mols = []

        for smi in self.smiles_reactants:
            mol = Chem.MolFromSmiles(smi)
            if mol is None:
                self.error_message = f"Failed to parse reactant SMILES: {smi}"
                return False
            self.reactant_mols.append(mol)

        for smi in self.smiles_products:
            mol = Chem.MolFromSmiles(smi)
            if mol is None:
                self.error_message = f"Failed to parse product SMILES: {smi}"
                return False
            self.product_mols.append(mol)

        return True

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the record to a dictionary for serialization.
        
        Returns:
            dict: Dictionary representation of the record.
        """
        return {
            "reaction_id": self.reaction_id,
            "smiles_reactants": self.smiles_reactants,
            "smiles_products": self.smiles_products,
            "reaction_smiles": self.reaction_smiles,
            "metadata": self.metadata,
            "is_eas": self.is_eas,
            "error_message": self.error_message
        }

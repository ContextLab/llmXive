"""
Data model for a single molecule.

This module defines the Molecule dataclass which encapsulates a molecule's
SMILES string, RDKit Mol object, and derived features (MW, atom count,
node/edge features).
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import json
import numpy as np
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

# Feature definitions as per task specification
NODE_FEATURE_KEYS = ['atom_type', 'hybridization', 'formal_charge']
EDGE_FEATURE_KEYS = ['bond_type', 'conjugated', 'aromatic']


@dataclass
class Molecule:
    """
    Represents a molecule with its graph features.
    
    Attributes:
        smiles (str): The SMILES string representation.
        mol (rdkit.Chem.Mol): The RDKit Mol object.
        molecular_weight (float): Calculated molecular weight.
        atom_count (int): Number of atoms in the molecule.
        node_features (np.ndarray): Array of shape (N_atoms, 3) containing
            [atom_type, hybridization, formal_charge].
        edge_features (np.ndarray): Array of shape (N_edges, 3) containing
            [bond_type, conjugated, aromatic].
    """
    smiles: str
    mol: Chem.Mol
    molecular_weight: float = 0.0
    atom_count: int = 0
    node_features: np.ndarray = field(default_factory=lambda: np.array([]))
    edge_features: np.ndarray = field(default_factory=lambda: np.array([]))

    def __post_init__(self):
        """Initialize derived features if not provided."""
        if self.mol is not None:
            if self.molecular_weight == 0.0:
                self.molecular_weight = rdMolDescriptors.CalcExactMolWt(self.mol)
            if self.atom_count == 0:
                self.atom_count = self.mol.GetNumAtoms()
            
            # Generate features if empty
            if self.node_features.size == 0 or self.edge_features.size == 0:
                self._extract_features()

    def _extract_features(self):
        """Extract node and edge feature from the RDKit Mol object."""
        atoms = self.mol.GetAtoms()
        bonds = self.mol.GetBonds()
        
        # Node features: [atom_type, hybridization, formal_charge]
        node_data = []
        for atom in atoms:
            # Atom type: atomic number
            atom_type = atom.GetAtomicNum()
            # Hybridization: map to integer
            hybridization = int(atom.GetHybridization())
            # Formal charge
            formal_charge = atom.GetFormalCharge()
            node_data.append([atom_type, hybridization, formal_charge])
        
        if node_data:
            self.node_features = np.array(node_data, dtype=np.float32)
        else:
            self.node_features = np.zeros((0, 3), dtype=np.float32)

        # Edge features: [bond_type, conjugated, aromatic]
        edge_data = []
        for bond in bonds:
            # Bond type: map to integer
            bond_type = int(bond.GetBondType())
            # Conjugated
            conjugated = 1 if bond.GetIsConjugated() else 0
            # Aromatic
            aromatic = 1 if bond.GetIsAromatic() else 0
            edge_data.append([bond_type, conjugated, aromatic])
        
        if edge_data:
            self.edge_features = np.array(edge_data, dtype=np.float32)
        else:
            self.edge_features = np.zeros((0, 3), dtype=np.float32)

    def validate(self) -> bool:
        """
        Validate the molecule object.
        
        Checks:
            - SMILES is a non-empty string
            - Mol object is not None and valid
            - Node features shape matches atom count
            - Edge features shape matches bond count
        
        Returns:
            bool: True if valid, False otherwise.
        """
        if not self.smiles or not isinstance(self.smiles, str):
            return False
        
        if self.mol is None:
            return False
        
        if not isinstance(self.mol, Chem.Mol):
            return False
        
        # Check if molecule is valid (has atoms)
        if self.mol.GetNumAtoms() == 0:
            return False
        
        # Validate node features
        expected_node_shape = (self.atom_count, 3)
        if self.node_features.shape != expected_node_shape:
            return False
        
        # Validate edge features
        expected_edge_shape = (self.mol.GetNumBonds(), 3)
        if self.edge_features.shape != expected_edge_shape:
            return False
        
        return True

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the molecule to a dictionary representation.
        
        Returns:
            dict: Dictionary containing all attributes. Arrays are converted
                to lists for JSON serialization.
        """
        return {
            'smiles': self.smiles,
            'molecular_weight': self.molecular_weight,
            'atom_count': self.atom_count,
            'node_features': self.node_features.tolist(),
            'edge_features': self.edge_features.tolist(),
            # Mol object cannot be serialized to JSON directly, so we exclude it
            # or convert to SMILES if needed
            'mol_smiles': self.smiles
        }

    @classmethod
    def from_smiles(cls, smiles: str) -> Optional['Molecule']:
        """
        Create a Molecule instance from a SMILES string.
        
        Args:
            smiles (str): The SMILES string.
        
        Returns:
            Molecule or None: A Molecule instance if parsing succeeds, None otherwise.
        """
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        return cls(smiles=smiles, mol=mol)
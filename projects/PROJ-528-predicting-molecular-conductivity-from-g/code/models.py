"""
Pydantic models for molecular data representation.

Defines data structures for molecules and their associated descriptors
used throughout the conductivity prediction pipeline.
"""
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from rdkit import Chem


class Descriptor(BaseModel):
    """
    Represents a single molecular descriptor.

    Attributes:
        name: Name of the descriptor (e.g., 'degree_mean', 'aromaticity_index')
        value: Numeric value of the descriptor
    """
    name: str = Field(..., description="Name of the descriptor")
    value: float = Field(..., description="Numeric value of the descriptor")

    @field_validator('value')
    @classmethod
    def validate_value(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError('Descriptor value must be numeric')
        return float(v)


class Molecule(BaseModel):
    """
    Represents a molecule with its SMILES string, descriptors, and target value.

    Attributes:
        smiles: SMILES string representation of the molecule
        descriptors: List of Descriptor objects containing computed features
        target: Optional target variable (e.g., conductivity or HOMO-LUMO gap)
    """
    smiles: str = Field(..., description="SMILES string of the molecule")
    descriptors: List[Descriptor] = Field(default_factory=list, description="List of molecular descriptors")
    target: Optional[float] = Field(None, description="Target variable value (conductivity or HOMO-LUMO gap)")

    @field_validator('smiles')
    @classmethod
    def validate_smiles_format(cls, v):
        """Validate that the SMILES string is chemically valid using RDKit."""
        if not v or not isinstance(v, str):
            raise ValueError('SMILES must be a non-empty string')
        
        mol = Chem.MolFromSmiles(v)
        if mol is None:
            raise ValueError(f'Invalid SMILES string: {v}')
        
        return v

    @property
    def descriptor_dict(self) -> dict:
        """Return descriptors as a dictionary mapping name to value."""
        return {desc.name: desc.value for desc in self.descriptors}

    @property
    def descriptor_names(self) -> List[str]:
        """Return list of descriptor names."""
        return [desc.name for desc in self.descriptors]

    @property
    def descriptor_values(self) -> List[float]:
        """Return list of descriptor values."""
        return [desc.value for desc in self.descriptors]
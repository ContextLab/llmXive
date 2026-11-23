"""
Pydantic models for molecular data.
"""
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from rdkit import Chem


class Molecule(BaseModel):
    """
    Pydantic model for a molecule.

    Attributes:
        smi: SMILES string representation of the molecule.
        lambda_max: Maximum excitation wavelength in nanometers.
        scaffold_id: Identifier for the Bemis-Murcko scaffold.
    """
    smi: str
    lambda_max: float
    scaffold_id: Optional[str] = None

    @field_validator('smi')
    @classmethod
    def validate_smi(cls, v: str) -> str:
        """
        Validate SMILES string using RDKit.

        Args:
            v: SMILES string.

        Returns:
            Canonicalized SMILES string.

        Raises:
            ValueError: If the SMILES string is invalid.
        """
        mol = Chem.MolFromSmiles(v)
        if mol is None:
            raise ValueError(f"Invalid SMILES: {v}")
        return Chem.MolToSmiles(mol)


class Scaffold(BaseModel):
    """
    Pydantic model for a scaffold.

    Attributes:
        scaffold_id: Unique identifier for the scaffold.
        molecule_count: Number of molecules belonging to this scaffold.
        molecules: List of molecules associated with this scaffold.
    """
    scaffold_id: str
    molecule_count: int = 0
    molecules: List[Molecule] = Field(default_factory=list)

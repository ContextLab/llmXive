"""
Pydantic data models for molecular excitation wavelength prediction.

This module defines the core data structures used throughout the pipeline:
- Molecule: Represents a single molecule with its SMILES, experimental lambda_max, and scaffold ID.
- Scaffold: Represents a Bemis-Murcko scaffold structure.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from rdkit import Chem


class Molecule(BaseModel):
    """
    Data model for a single molecule entry.
    
    Attributes:
        smi (str): Canonical SMILES string of the molecule.
        lambda_max (float): Experimental maximum absorption wavelength in nanometers.
        scaffold_id (str): Unique identifier for the Bemis-Murcko scaffold.
    """
    smi: str = Field(..., description="Canonical SMILES string")
    lambda_max: float = Field(..., description="Experimental lambda_max in nm")
    scaffold_id: str = Field(..., description="Bemis-Murcko scaffold identifier")

    @field_validator('smi')
    @classmethod
    def validate_smi(cls, v: str) -> str:
        """Validate that the SMILES string corresponds to a valid RDKit molecule."""
        if not v or not isinstance(v, str):
            raise ValueError("SMILES string must be a non-empty string")
        
        mol = Chem.MolFromSmiles(v)
        if mol is None:
            raise ValueError(f"Invalid SMILES string: {v}")
        return v

    @field_validator('lambda_max')
    @classmethod
    def validate_lambda_max(cls, v: float) -> float:
        """Validate that lambda_max is a positive number."""
        if v <= 0:
            raise ValueError(f"lambda_max must be positive, got {v}")
        return v

    @field_validator('scaffold_id')
    @classmethod
    def validate_scaffold_id(cls, v: str) -> str:
        """Validate that scaffold_id is a non-empty string."""
        if not v or not isinstance(v, str):
            raise ValueError("scaffold_id must be a non-empty string")
        return v


class Scaffold(BaseModel):
    """
    Data model for a Bemis-Murcko scaffold.
    
    Attributes:
        scaffold_id (str): Unique identifier for the scaffold.
        smi (str): Canonical SMILES string of the scaffold.
        molecule_count (int): Number of molecules in the dataset sharing this scaffold.
    """
    scaffold_id: str = Field(..., description="Unique scaffold identifier")
    smi: str = Field(..., description="Canonical SMILES of the scaffold")
    molecule_count: int = Field(default=0, ge=0, description="Count of molecules with this scaffold")

    @field_validator('scaffold_id')
    @classmethod
    def validate_scaffold_id(cls, v: str) -> str:
        """Validate scaffold_id format."""
        if not v or not isinstance(v, str):
            raise ValueError("scaffold_id must be a non-empty string")
        return v

    @field_validator('smi')
    @classmethod
    def validate_smi(cls, v: str) -> str:
        """Validate that the scaffold SMILES is valid."""
        if not v or not isinstance(v, str):
            raise ValueError("SMILES string must be a non-empty string")
        
        mol = Chem.MolFromSmiles(v)
        if mol is None:
            raise ValueError(f"Invalid scaffold SMILES string: {v}")
        return v
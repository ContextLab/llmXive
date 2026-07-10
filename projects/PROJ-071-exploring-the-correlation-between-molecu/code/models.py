from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
import math


class Molecule(BaseModel):
    """
    Data model representing a pharmaceutical molecule.
    Stores SMILES, calculated descriptors, and metadata.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    smiles: str = Field(..., description="Canonical SMILES string")
    name: Optional[str] = Field(None, description="Common drug name")
    molecular_weight: float = Field(..., description="Molecular weight in g/mol")
    tpsa: float = Field(..., description="Topological Polar Surface Area")
    rotatable_bonds: int = Field(..., description="Count of rotatable bonds")
    aromatic_rings: int = Field(..., description="Count of aromatic rings")
    wiener_index: float = Field(..., description="Wiener index (topological distance sum)")
    zagreb_index: float = Field(..., description="Zagreb index (connectivity index)")
    rdkit_mol: Optional[Chem.Mol] = Field(None, exclude=True, description="RDKit molecule object (not serialized)")

    @field_validator('smiles')
    @classmethod
    def validate_smiles_format(cls, v: str) -> str:
        """Validate that the SMILES string corresponds to a valid chemical structure."""
        mol = Chem.MolFromSmiles(v)
        if mol is None:
            raise ValueError(f"Invalid SMILES string: {v}")
        return v

    @field_validator('molecular_weight', 'tpsa', 'wiener_index', 'zagreb_index')
    @classmethod
    def check_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError(f"Value {v} cannot be negative")
        return v

    @classmethod
    def from_smiles(cls, smiles: str, name: Optional[str] = None) -> 'Molecule':
        """
        Factory method to create a Molecule instance from a SMILES string.
        Calculates all descriptors using RDKit.
        """
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise ValueError(f"Invalid SMILES: {smiles}")

        # Calculate descriptors
        mw = Descriptors.MolWt(mol)
        tpsa = Descriptors.TPSA(mol)
        rot_bonds = rdMolDescriptors.CalcNumRotatableBonds(mol)
        aromatic_rings = rdMolDescriptors.CalcNumAromaticRings(mol)
        
        # Wiener index calculation
        # Note: RDKit does not have a direct 'Wiener Index' function in standard Descriptors
        # We calculate it manually using the distance matrix on the hydrogen-suppressed graph
        try:
            # Get the distance matrix (hydrogen suppressed)
            dist_mat = rdMolDescriptors.CalcDistanceMatrix(mol)
            # Sum of upper triangle elements
            wiener = float(sum(sum(row[i+1:]) for i, row in enumerate(dist_mat)))
        except Exception:
            wiener = 0.0

        # Zagreb index calculation
        # First Zagreb Index: Sum of (degree^2) for all vertices
        try:
            # Get adjacency matrix or degrees
            # rdMolDescriptors.CalcNumAtoms gives number of atoms
            # We need degrees. We can compute from adjacency matrix or use specific descriptor
            # RDKit has 'CalcMolDescriptors' but Zagreb is not directly exposed as a single function
            # We compute manually from the adjacency matrix
            adj_mat = rdMolDescriptors.CalcAdjacencyMatrix(mol)
            degrees = [sum(row) for row in adj_mat]
            zagreb = float(sum(d * d for d in degrees))
        except Exception:
            zagreb = 0.0

        return cls(
            smiles=smiles,
            name=name,
            molecular_weight=mw,
            tpsa=tpsa,
            rotatable_bonds=rot_bonds,
            aromatic_rings=aromatic_rings,
            wiener_index=wiener,
            zagreb_index=zagreb,
            rdkit_mol=mol
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding the RDKit object."""
        return self.model_dump(exclude={'rdkit_mol'})


class DegradationRecord(BaseModel):
    """
    Data model representing a degradation measurement for a molecule.
    Includes half-life, conditions, and metadata.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    smiles: str = Field(..., description="SMILES of the molecule")
    half_life: float = Field(..., description="Half-life in hours")
    temperature: float = Field(..., description="Temperature in Kelvin")
    ph: float = Field(..., description="pH value")
    rate_constant: Optional[float] = Field(None, description="Rate constant (k) in 1/h")
    activation_energy: Optional[float] = Field(None, description="Activation energy (Ea) in kJ/mol")
    condition_notes: Optional[str] = Field(None, description="Notes on experimental conditions")
    source_id: Optional[str] = Field(None, description="Source identifier (e.g., FDA ID)")
    normalized: bool = Field(False, description="Whether this record has been normalized to standard conditions")

    @field_validator('half_life', 'temperature', 'ph')
    @classmethod
    def check_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"Value {v} must be positive")
        return v

    @field_validator('rate_constant', 'activation_energy')
    @classmethod
    def check_non_negative_optional(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError(f"Value {v} cannot be negative")
        return v

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DegradationRecord':
        """
        Create a DegradationRecord from a dictionary (e.g., from CSV row).
        Handles conversion of units if necessary (assumes input is already in standard units or marked).
        """
        # Ensure required fields are present
        required = ['smiles', 'half_life', 'temperature', 'ph']
        for field in required:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        return cls(
            smiles=data['smiles'],
            half_life=float(data['half_life']),
            temperature=float(data['temperature']),
            ph=float(data['ph']),
            rate_constant=float(data['rate_constant']) if data.get('rate_constant') is not None else None,
            activation_energy=float(data['activation_energy']) if data.get('activation_energy') is not None else None,
            condition_notes=data.get('condition_notes'),
            source_id=data.get('source_id'),
            normalized=data.get('normalized', False)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization (e.g., to CSV)."""
        return self.model_dump()

    def is_standard_condition(self) -> bool:
        """
        Check if the record is at standard conditions (25°C, pH 7.4).
        25°C = 298.15 K
        """
        is_temp = abs(self.temperature - 298.15) < 0.1
        is_ph = abs(self.ph - 7.4) < 0.1
        return is_temp and is_ph
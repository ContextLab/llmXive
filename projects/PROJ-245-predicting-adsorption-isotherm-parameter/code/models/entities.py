"""
Base data classes/entities for the adsorption isotherm prediction pipeline.

These classes provide a structured representation of the core domain entities:
Adsorbate, Adsorbent, and IsothermParameter. They are designed to be
compatible with the data schema defined in contracts/dataset.schema.yaml.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class AdsorbateState(Enum):
    """Enumeration for the physical state of the adsorbate."""
    GAS = "gas"
    LIQUID = "liquid"
    SUPERCRITICAL = "supercritical"


@dataclass
class Adsorbate:
    """
    Represents the adsorbate molecule.

    Attributes:
        material_id: Unique identifier for the material (e.g., 'Kr', 'CH4').
        name: Common chemical name.
        formula: Chemical formula (e.g., 'Kr', 'CH4').
        molecular_weight: Molecular weight in g/mol.
        kinetic_diameter: Kinetic diameter in Angstroms (Å).
        polarizability: Polarizability in Å³.
        quadrupole_moment: Quadrupole moment in Debye (D).
        h_bond_donors: Number of hydrogen bond donors.
        h_bond_acceptors: Number of hydrogen bond acceptors.
        van_der_waals_volume: Van der Waals volume in Å³.
        state: Physical state at STP.
        rdkit_smiles: RDKit SMILES string if available.
        metadata: Additional arbitrary properties.
    """
    material_id: str
    name: Optional[str] = None
    formula: Optional[str] = None
    molecular_weight: Optional[float] = None
    kinetic_diameter: Optional[float] = None
    polarizability: Optional[float] = None
    quadrupole_moment: Optional[float] = None
    h_bond_donors: int = 0
    h_bond_acceptors: int = 0
    van_der_waals_volume: Optional[float] = None
    state: AdsorbateState = AdsorbateState.GAS
    rdkit_smiles: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the instance to a dictionary compatible with the dataset schema."""
        return {
            "material_id": self.material_id,
            "name": self.name,
            "formula": self.formula,
            "molecular_weight": self.molecular_weight,
            "kinetic_diameter": self.kinetic_diameter,
            "polarizability": self.polarizability,
            "quadrupole_moment": self.quadrupole_moment,
            "h_bond_donors": self.h_bond_donors,
            "h_bond_acceptors": self.h_bond_acceptors,
            "van_der_waals_volume": self.van_der_waals_volume,
            "state": self.state.value,
            "rdkit_smiles": self.rdkit_smiles,
            **self.metadata
        }


@dataclass
class Adsorbent:
    """
    Represents the adsorbent material (e.g., MOF, CNT, Zeolite).

    Attributes:
        material_id: Unique identifier for the adsorbent (e.g., 'MOF-5', 'CNT-1').
        name: Common name.
        type: Type of material (e.g., 'MOF', 'CNT', 'Zeolite').
        surface_area: BET surface area in m²/g.
        pore_volume: Total pore volume in cm³/g.
        pore_size: Average pore size in Å.
        functional_groups: List of functional groups present.
        metadata: Additional arbitrary properties.
    """
    material_id: str
    name: Optional[str] = None
    type: Optional[str] = None
    surface_area: Optional[float] = None
    pore_volume: Optional[float] = None
    pore_size: Optional[float] = None
    functional_groups: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the instance to a dictionary compatible with the dataset schema."""
        return {
            "material_id": self.material_id,
            "name": self.name,
            "type": self.type,
            "surface_area": self.surface_area,
            "pore_volume": self.pore_volume,
            "pore_size": self.pore_size,
            "functional_groups": self.functional_groups,
            **self.metadata
        }


@dataclass
class IsothermParameter:
    """
    Represents the target isotherm parameters for a specific Adsorbate-Adsorbent pair.

    Attributes:
        adsorbate_id: Reference to the adsorbate material_id.
        adsorbent_id: Reference to the adsorbent material_id.
        langmuir_capacity: Langmuir saturation capacity (mol/kg or mmol/g).
        henry_constant: Henry's law constant (mmol/kg/bar or similar).
        isotherm_type: Type of isotherm (e.g., 'Type I', 'Type II').
        temperature: Temperature at which measurement was taken (K).
        pressure_range: Tuple of (min_pressure, max_pressure) in bar.
        metadata: Additional measurement metadata.
    """
    adsorbate_id: str
    adsorbent_id: str
    langmuir_capacity: Optional[float] = None
    henry_constant: Optional[float] = None
    isotherm_type: Optional[str] = None
    temperature: Optional[float] = None
    pressure_range: Optional[tuple] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the instance to a dictionary compatible with the dataset schema."""
        return {
            "adsorbate_id": self.adsorbate_id,
            "adsorbent_id": self.adsorbent_id,
            "langmuir_capacity": self.langmuir_capacity,
            "henry_constant": self.henry_constant,
            "isotherm_type": self.isotherm_type,
            "temperature": self.temperature,
            "pressure_range": self.pressure_range,
            **self.metadata
        }
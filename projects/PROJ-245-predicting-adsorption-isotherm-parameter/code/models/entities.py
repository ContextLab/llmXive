"""
Core data entities for the adsorption isotherm prediction pipeline.

This module defines the fundamental data classes representing adsorbates,
adsorbents, and the target isotherm parameters used throughout the project.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
import json


class AdsorbateState(Enum):
    """Enumeration of possible physical states for an adsorbate."""
    GAS = "gas"
    LIQUID = "liquid"
    SUPERCRITICAL = "supercritical"
    SOLID = "solid"


@dataclass
class Adsorbate:
    """
    Represents a chemical adsorbate molecule.
    
    Attributes:
        material_id: Unique identifier for the material instance.
        smi: SMILES string representation of the molecule.
        iupac_name: Official IUPAC name.
        common_name: Common or trade name.
        molecular_weight: Molecular weight in g/mol.
        state: Physical state at standard conditions.
        kinetic_diameter: Kinetic diameter in Angstroms (Å).
        polarizability: Molecular polarizability in Å³.
        dipole_moment: Dipole moment in Debye.
        quadrupole_moment: Quadrupole moment (tensor or scalar representation).
        h_bond_donors: Number of hydrogen bond donors.
        h_bond_acceptors: Number of hydrogen bond acceptors.
        van_der_waals_volume: van der Waals volume in Å³.
        surface_area: Molecular surface area in Å².
        logp: Partition coefficient (octanol-water).
        metadata: Additional arbitrary properties.
    """
    material_id: str
    smi: str
    iupac_name: Optional[str] = None
    common_name: Optional[str] = None
    molecular_weight: Optional[float] = None
    state: Optional[AdsorbateState] = None
    kinetic_diameter: Optional[float] = None  # Å
    polarizability: Optional[float] = None  # Å³
    dipole_moment: Optional[float] = None  # Debye
    quadrupole_moment: Optional[float] = None  # Debye·Å (or appropriate unit)
    h_bond_donors: Optional[int] = None
    h_bond_acceptors: Optional[int] = None
    van_der_waals_volume: Optional[float] = None  # Å³
    surface_area: Optional[float] = None  # Å²
    logp: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the instance to a dictionary, serializing enums."""
        data = self.__dict__.copy()
        if self.state is not None:
            data['state'] = self.state.value
        return data

    def to_json(self) -> str:
        """Serialize the instance to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class Adsorbent:
    """
    Represents a porous material (adsorbent) used for adsorption.
    
    Attributes:
        material_id: Unique identifier for the material.
        name: Common name or identifier (e.g., "MOF-5", "CNT").
        type: Material class (e.g., "MOF", "CNT", "Zeolite", "Activated Carbon").
        surface_area: BET surface area in m²/g.
        pore_volume: Total pore volume in cm³/g.
        pore_size_distribution: List of pore sizes in nm (optional).
        functional_groups: List of surface functional groups.
        synthesis_method: Brief description of synthesis.
        metadata: Additional properties.
    """
    material_id: str
    name: str
    type: Optional[str] = None
    surface_area: Optional[float] = None  # m²/g
    pore_volume: Optional[float] = None  # cm³/g
    pore_size_distribution: Optional[List[float]] = None  # nm
    functional_groups: Optional[List[str]] = None
    synthesis_method: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the instance to a dictionary."""
        return self.__dict__.copy()

    def to_json(self) -> str:
        """Serialize the instance to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class IsothermParameter:
    """
    Represents the target isotherm parameters derived from experimental or simulated data.
    
    This class holds the regression targets for the machine learning models.
    
    Attributes:
        record_id: Unique identifier for the specific adsorption measurement record.
        adsorbate_id: Reference to the Adsorbate material_id.
        adsorbent_id: Reference to the Adsorbent material_id.
        temperature: Temperature in Kelvin.
        pressure_unit: Unit of pressure (e.g., 'bar', 'Pa', 'atm').
        langmuir_capacity: Langmuir maximum capacity (q_max) in mol/kg or mmol/g.
        langmuir_k: Langmuir affinity constant (K_L) in 1/pressure_unit.
        henry_constant: Henry's law constant (K_H) in mol/kg/bar (or similar).
        isotherm_type: Type of isotherm (e.g., "Type I", "Type II").
        source: Origin of the data (e.g., "NIST", "Synthetic", "Literature").
        metadata: Additional experimental conditions or notes.
    """
    record_id: str
    adsorbate_id: str
    adsorbent_id: str
    temperature: float  # Kelvin
    pressure_unit: str = "bar"
    langmuir_capacity: Optional[float] = None  # mol/kg
    langmuir_k: Optional[float] = None  # 1/bar
    henry_constant: Optional[float] = None  # mol/kg/bar
    isotherm_type: Optional[str] = None
    source: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the instance to a dictionary."""
        return self.__dict__.copy()

    def to_json(self) -> str:
        """Serialize the instance to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)
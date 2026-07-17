"""
Base data classes and entities for the adsorption isotherm prediction pipeline.

This module defines the core domain entities: Adsorbate, Adsorbent, and IsothermParameter.
These classes serve as the structured representation of molecular and material data
used throughout the pipeline.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
import json
import hashlib


class AdsorbateState(Enum):
    """Enumeration of possible physical states for an adsorbate."""
    GAS = "gas"
    LIQUID = "liquid"
    SUPERCRITICAL = "supercritical"
    UNKNOWN = "unknown"


@dataclass
class Adsorbate:
    """
    Represents an adsorbate molecule.
    
    Attributes:
        mol_id: Unique identifier for the molecule (e.g., SMILES string or InChIKey)
        name: Common name of the molecule
        molecular_weight: Molecular weight in g/mol
        polarizability: Polarizability in Å³
        kinetic_diameter: Kinetic diameter in Å
        polar_surface_area: Polar surface area in Å²
        h_bond_donors: Number of hydrogen bond donors
        h_bond_acceptors: Number of hydrogen bond acceptors
        vdw_volume: Van der Waals volume in Å³
        quadrupole_moment: Quadrupole moment (optional)
        lj_energy_param: Lennard-Jones energy parameter (optional)
        state: Physical state of the adsorbate
        descriptors: Dictionary of additional calculated descriptors
    """
    mol_id: str
    name: Optional[str] = None
    molecular_weight: Optional[float] = None
    polarizability: Optional[float] = None
    kinetic_diameter: Optional[float] = None
    polar_surface_area: Optional[float] = None
    h_bond_donors: Optional[int] = None
    h_bond_acceptors: Optional[int] = None
    vdw_volume: Optional[float] = None
    quadrupole_moment: Optional[float] = None
    lj_energy_param: Optional[float] = None
    state: AdsorbateState = AdsorbateState.UNKNOWN
    descriptors: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the Adsorbate instance to a dictionary."""
        return {
            "mol_id": self.mol_id,
            "name": self.name,
            "molecular_weight": self.molecular_weight,
            "polarizability": self.polarizability,
            "kinetic_diameter": self.kinetic_diameter,
            "polar_surface_area": self.polar_surface_area,
            "h_bond_donors": self.h_bond_donors,
            "h_bond_acceptors": self.h_bond_acceptors,
            "vdw_volume": self.vdw_volume,
            "quadrupole_moment": self.quadrupole_moment,
            "lj_energy_param": self.lj_energy_param,
            "state": self.state.value,
            "descriptors": self.descriptors
        }
    
    def descriptor_hash(self) -> str:
        """
        Generate a hash based on the descriptor values.
        Used for identifying identical adsorbates with potentially conflicting targets.
        """
        hashable_values = [
            self.molecular_weight,
            self.polarizability,
            self.kinetic_diameter,
            self.polar_surface_area,
            self.h_bond_donors,
            self.h_bond_acceptors,
            self.vdw_volume,
            self.quadrupole_moment,
            self.lj_energy_param
        ]
        # Convert to string representation for hashing
        str_repr = str(tuple(hashable_values))
        return hashlib.md5(str_repr.encode()).hexdigest()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Adsorbate":
        """Create an Adsorbate instance from a dictionary."""
        state = data.get("state", "unknown")
        if isinstance(state, str):
            try:
                state = AdsorbateState(state)
            except ValueError:
                state = AdsorbateState.UNKNOWN
        
        return cls(
            mol_id=data["mol_id"],
            name=data.get("name"),
            molecular_weight=data.get("molecular_weight"),
            polarizability=data.get("polarizability"),
            kinetic_diameter=data.get("kinetic_diameter"),
            polar_surface_area=data.get("polar_surface_area"),
            h_bond_donors=data.get("h_bond_donors"),
            h_bond_acceptors=data.get("h_bond_acceptors"),
            vdw_volume=data.get("vdw_volume"),
            quadrupole_moment=data.get("quadrupole_moment"),
            lj_energy_param=data.get("lj_energy_param"),
            state=state,
            descriptors=data.get("descriptors", {})
        )
    
    def to_json(self) -> str:
        """Serialize the Adsorbate to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "Adsorbate":
        """Create an Adsorbate instance from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class Adsorbent:
    """
    Represents an adsorbent material (e.g., MOF, CNT, zeolite).
    
    Attributes:
        material_id: Unique identifier for the material
        name: Name of the material
        type: Material type (e.g., "MOF", "CNT", "Zeolite")
        surface_area: BET surface area in m²/g
        pore_volume: Total pore volume in cm³/g
        pore_size: Average pore size in Å
        isotherm_type: Type of isotherm observed (e.g., "Type I", "Type II")
        synthesis_method: Method used for synthesis (optional)
        properties: Dictionary of additional material properties
    """
    material_id: str
    name: Optional[str] = None
    type: Optional[str] = None
    surface_area: Optional[float] = None
    pore_volume: Optional[float] = None
    pore_size: Optional[float] = None
    isotherm_type: Optional[str] = None
    synthesis_method: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the Adsorbent instance to a dictionary."""
        return {
            "material_id": self.material_id,
            "name": self.name,
            "type": self.type,
            "surface_area": self.surface_area,
            "pore_volume": self.pore_volume,
            "pore_size": self.pore_size,
            "isotherm_type": self.isotherm_type,
            "synthesis_method": self.synthesis_method,
            "properties": self.properties
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Adsorbent":
        """Create an Adsorbent instance from a dictionary."""
        return cls(
            material_id=data["material_id"],
            name=data.get("name"),
            type=data.get("type"),
            surface_area=data.get("surface_area"),
            pore_volume=data.get("pore_volume"),
            pore_size=data.get("pore_size"),
            isotherm_type=data.get("isotherm_type"),
            synthesis_method=data.get("synthesis_method"),
            properties=data.get("properties", {})
        )
    
    def to_json(self) -> str:
        """Serialize the Adsorbent to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "Adsorbent":
        """Create an Adsorbent instance from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class IsothermParameter:
    """
    Represents an isotherm parameter measurement.
    
    Attributes:
        param_id: Unique identifier for the parameter measurement
        material_id: Reference to the adsorbent material
        mol_id: Reference to the adsorbate molecule
        parameter_type: Type of parameter (e.g., "Langmuir_capacity", "Henry_constant")
        value: Numerical value of the parameter
        unit: Unit of measurement
        temperature: Temperature at which measurement was taken (K)
        pressure: Pressure at which measurement was taken (bar)
        source: Source of the data (e.g., "synthetic", "NIST", "literature")
        confidence: Confidence score or uncertainty estimate (optional)
        metadata: Additional metadata about the measurement
    """
    param_id: str
    material_id: str
    mol_id: str
    parameter_type: str
    value: float
    unit: str
    temperature: Optional[float] = None
    pressure: Optional[float] = None
    source: str = "unknown"
    confidence: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the IsothermParameter instance to a dictionary."""
        return {
            "param_id": self.param_id,
            "material_id": self.material_id,
            "mol_id": self.mol_id,
            "parameter_type": self.parameter_type,
            "value": self.value,
            "unit": self.unit,
            "temperature": self.temperature,
            "pressure": self.pressure,
            "source": self.source,
            "confidence": self.confidence,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IsothermParameter":
        """Create an IsothermParameter instance from a dictionary."""
        return cls(
            param_id=data["param_id"],
            material_id=data["material_id"],
            mol_id=data["mol_id"],
            parameter_type=data["parameter_type"],
            value=data["value"],
            unit=data["unit"],
            temperature=data.get("temperature"),
            pressure=data.get("pressure"),
            source=data.get("source", "unknown"),
            confidence=data.get("confidence"),
            metadata=data.get("metadata", {})
        )
    
    def to_json(self) -> str:
        """Serialize the IsothermParameter to a JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> "IsothermParameter":
        """Create an IsothermParameter instance from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
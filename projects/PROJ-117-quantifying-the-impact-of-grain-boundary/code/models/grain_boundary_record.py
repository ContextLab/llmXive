"""
Data model for Grain Boundary Record.

Defines the `GrainBoundaryRecord` dataclass used to store parsed
grain boundary simulation data, including geometric descriptors
and physical properties.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any
import json


@dataclass
class GrainBoundaryRecord:
    """
    Represents a single grain boundary simulation record.

    Attributes:
        material_id: Unique identifier for the material (e.g., from Materials Project).
        structure_file: Path to the raw structure file (POSCAR/CIF).
        misorientation_angle: Misorientation angle in degrees.
        rotation_axis: Rotation axis vector [x, y, z].
        boundary_plane_normal: Boundary plane normal vector [h, k, l] or Miller indices.
        sigma_value: Sigma value (Σ) from Coincidence Site Lattice (CSL) theory.
        boundary_width: Width of the grain boundary region in Angstroms.
        excess_volume: Excess volume per unit area in Angstroms^2.
        temperature: Simulation temperature in Kelvin.
        composition: Chemical composition string or dict.
        diffusivity: Measured atomic diffusivity value.
        simulation_method: Method used (e.g., 'DFT', 'MD', 'KMC').
        potential_id: Identifier for the interatomic potential used.
        source: Source of the data (e.g., 'Materials Project', 'OpenKIM', 'NIST').
        raw_metadata: Dictionary storing any additional raw metadata from the source.
    """

    material_id: str
    structure_file: str
    misorientation_angle: float
    rotation_axis: List[float]
    boundary_plane_normal: List[float]
    sigma_value: float
    boundary_width: float
    excess_volume: float
    temperature: float
    composition: str
    diffusivity: float
    simulation_method: str
    potential_id: str
    source: str
    raw_metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert the record to a dictionary."""
        return {
            "material_id": self.material_id,
            "structure_file": self.structure_file,
            "misorientation_angle": self.misorientation_angle,
            "rotation_axis": self.rotation_axis,
            "boundary_plane_normal": self.boundary_plane_normal,
            "sigma_value": self.sigma_value,
            "boundary_width": self.boundary_width,
            "excess_volume": self.excess_volume,
            "temperature": self.temperature,
            "composition": self.composition,
            "diffusivity": self.diffusivity,
            "simulation_method": self.simulation_method,
            "potential_id": self.potential_id,
            "source": self.source,
            "raw_metadata": self.raw_metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GrainBoundaryRecord":
        """Create a GrainBoundaryRecord from a dictionary."""
        return cls(
            material_id=data["material_id"],
            structure_file=data["structure_file"],
            misorientation_angle=data["misorientation_angle"],
            rotation_axis=data["rotation_axis"],
            boundary_plane_normal=data["boundary_plane_normal"],
            sigma_value=data["sigma_value"],
            boundary_width=data["boundary_width"],
            excess_volume=data["excess_volume"],
            temperature=data["temperature"],
            composition=data["composition"],
            diffusivity=data["diffusivity"],
            simulation_method=data["simulation_method"],
            potential_id=data["potential_id"],
            source=data["source"],
            raw_metadata=data.get("raw_metadata", {}),
        )

    def to_json(self) -> str:
        """Serialize the record to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "GrainBoundaryRecord":
        """Deserialize a record from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

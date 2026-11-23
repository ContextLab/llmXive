"""
Data models for alloy system definitions.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class CrystalStructure(Enum):
    """Supported crystal structures for bulk phases."""
    BCC = "bcc"
    FCC = "fcc"
    HCP = "hcp"
    AMORPHOUS = "amorphous"


@dataclass
class AlloySystem:
    """
    Represents a specific alloy system (e.g., Fe-Cr-Mo).

    Attributes:
        name: Unique identifier for the system (e.g., "Fe-Cr-Mo").
        solvent: The primary solvent element (e.g., "Fe").
        solutes: List of solute elements (e.g., ["Cr", "Mo"]).
        structure: The bulk crystal structure of the solvent.
        bulk_composition: Dictionary of bulk atomic fractions {element: fraction}.
        temperature: Temperature in Kelvin.
        metadata: Optional additional metadata.
    """
    name: str
    solvent: str
    solutes: List[str]
    structure: CrystalStructure = CrystalStructure.BCC
    bulk_composition: Dict[str, float] = field(default_factory=dict)
    temperature: float = 0.0
    metadata: Dict[str, any] = field(default_factory=dict)

    def __post_init__(self):
        if self.temperature < 0:
            raise ValueError("Temperature must be non-negative.")
        
        # Ensure solvent is in composition if provided
        if self.bulk_composition and self.solvent not in self.bulk_composition:
            raise ValueError(f"Solvent '{self.solvent}' must be in bulk_composition.")
        
        # Validate solutes are in composition
        for solute in self.solutes:
            if self.bulk_composition and solute not in self.bulk_composition:
                raise ValueError(f"Solute '{solute}' must be in bulk_composition.")

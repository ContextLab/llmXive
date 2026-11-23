"""
Schema definition for TopologicalDescriptor.

This class represents the calculated topological indices for a specific molecule
within a reaction context.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class TopologicalDescriptor:
    """
    Data contract for topological descriptors of a molecule.

    Attributes:
        reaction_id: Reference to the parent ReactionRecord.
        smiles: The canonical SMILES string of the molecule analyzed.
        molecule_role: Role of the molecule in the reaction (e.g., 'reactant', 'product').
        wiener_index: The Wiener index (sum of all shortest path distances).
        balaban_index: The Balaban index (connectivity index).
        zagreb_index: The Zagreb index (sum of squared degrees).
        is_connected: Boolean indicating if the molecular graph is connected.
        atom_count: Number of atoms in the molecule.
        bond_count: Number of bonds in the molecule.
        calculation_status: Status of the calculation (e.g., 'SUCCESS', 'FAILED').
        error_message: Optional error message if calculation failed.
    """
    reaction_id: str
    smiles: str
    molecule_role: str
    wiener_index: Optional[float] = None
    balaban_index: Optional[float] = None
    zagreb_index: Optional[float] = None
    is_connected: bool = True
    atom_count: int = 0
    bond_count: int = 0
    calculation_status: str = "SUCCESS"
    error_message: Optional[str] = None

    def __post_init__(self):
        """Validate basic constraints."""
        if not self.reaction_id:
            raise ValueError("reaction_id cannot be empty")
        if not self.smiles:
            raise ValueError("smiles cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the record to a dictionary for serialization."""
        return {
            "reaction_id": self.reaction_id,
            "smiles": self.smiles,
            "molecule_role": self.molecule_role,
            "wiener_index": self.wiener_index,
            "balaban_index": self.balaban_index,
            "zagreb_index": self.zagreb_index,
            "is_connected": self.is_connected,
            "atom_count": self.atom_count,
            "bond_count": self.bond_count,
            "calculation_status": self.calculation_status,
            "error_message": self.error_message
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TopologicalDescriptor":
        """Create a TopologicalDescriptor from a dictionary."""
        return cls(
            reaction_id=data.get("reaction_id", ""),
            smiles=data.get("smiles", ""),
            molecule_role=data.get("molecule_role", ""),
            wiener_index=data.get("wiener_index"),
            balaban_index=data.get("balaban_index"),
            zagreb_index=data.get("zagreb_index"),
            is_connected=data.get("is_connected", True),
            atom_count=data.get("atom_count", 0),
            bond_count=data.get("bond_count", 0),
            calculation_status=data.get("calculation_status", "SUCCESS"),
            error_message=data.get("error_message")
        )

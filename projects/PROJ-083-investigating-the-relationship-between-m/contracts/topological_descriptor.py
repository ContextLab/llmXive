"""
Schema definitions for TopologicalDescriptor.

This module defines the data structure for storing calculated topological
indices (Wiener, Balaban, Zagreb) associated with molecular graphs.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum


class DescriptorType(Enum):
    """Enumeration of supported topological descriptor types."""
    WIENER = "wiener"
    BALABAN = "balaban"
    ZAGREB = "zagreb"


@dataclass
class TopologicalDescriptor:
    """
    Represents a calculated topological descriptor for a specific molecule.

    Attributes:
        record_id: The ID of the ReactionRecord this descriptor belongs to.
        molecule_smiles: The canonical SMILES of the molecule being described.
        molecule_role: Role of the molecule in the reaction (e.g., 'reactant', 'product', 'aromatic_core').
        descriptor_type: The type of descriptor calculated (Wiener, Balaban, Zagreb).
        value: The calculated numerical value of the descriptor.
        is_valid: Boolean flag indicating if the calculation was valid (e.g., graph was connected).
        metadata: Additional metadata (e.g., calculation timestamp, graph properties).
        error_message: Optional error message if calculation failed.
    """
    record_id: str
    molecule_smiles: str
    molecule_role: str
    descriptor_type: DescriptorType
    value: float
    is_valid: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the descriptor to a dictionary for serialization.
        
        Returns:
            dict: Dictionary representation of the descriptor.
        """
        return {
            "record_id": self.record_id,
            "molecule_smiles": self.molecule_smiles,
            "molecule_role": self.molecule_role,
            "descriptor_type": self.descriptor_type.value,
            "value": self.value,
            "is_valid": self.is_valid,
            "metadata": self.metadata,
            "error_message": self.error_message
        }

    @classmethod
    def create_invalid(
        cls,
        record_id: str,
        molecule_smiles: str,
        molecule_role: str,
        descriptor_type: DescriptorType,
        reason: str
    ) -> "TopologicalDescriptor":
        """
        Factory method to create an invalid descriptor record.
        
        Args:
            record_id: The ID of the associated reaction record.
            molecule_smiles: The SMILES of the molecule.
            molecule_role: The role of the molecule.
            descriptor_type: The type of descriptor.
            reason: The reason for invalidity (e.g., disconnected graph).
        
        Returns:
            TopologicalDescriptor: An instance marked as invalid.
        """
        return cls(
            record_id=record_id,
            molecule_smiles=molecule_smiles,
            molecule_role=molecule_role,
            descriptor_type=descriptor_type,
            value=0.0,
            is_valid=False,
            error_message=reason
        )

"""
Schema definition for ReactionRecord.

This class represents a single reaction instance from the USPTO-50k dataset,
filtered for Electrophilic Aromatic Substitution (EAS) reactions.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

class ReactionType(Enum):
    """Enumeration of supported reaction types."""
    EAS = "EAS"
    OTHER = "OTHER"

@dataclass
class ReactionRecord:
    """
    Data contract for a single reaction record.

    Attributes:
        reaction_id: Unique identifier for the reaction (e.g., from USPTO dataset).
        smiles_reactants: SMILES string of the reactant molecules.
        smiles_products: SMILES string of the product molecules.
        smiles_reagent: SMILES string of the reagent (if applicable).
        reaction_type: The classified type of reaction (e.g., EAS).
        metadata: Dictionary for additional raw data (e.g., yield, conditions).
        is_valid: Boolean flag indicating if the SMILES parsing was successful.
        error_message: Optional string describing parsing/validation errors.
    """
    reaction_id: str
    smiles_reactants: str
    smiles_products: str
    smiles_reagent: Optional[str] = None
    reaction_type: ReactionType = ReactionType.OTHER
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_valid: bool = True
    error_message: Optional[str] = None

    def __post_init__(self):
        """Validate basic constraints upon initialization."""
        if not self.reaction_id:
            raise ValueError("reaction_id cannot be empty")
        if not self.smiles_reactants:
            self.is_valid = False
            self.error_message = "Missing reactant SMILES"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the record to a dictionary for serialization."""
        return {
            "reaction_id": self.reaction_id,
            "smiles_reactants": self.smiles_reactants,
            "smiles_products": self.smiles_products,
            "smiles_reagent": self.smiles_reagent,
            "reaction_type": self.reaction_type.value,
            "metadata": self.metadata,
            "is_valid": self.is_valid,
            "error_message": self.error_message
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReactionRecord":
        """Create a ReactionRecord from a dictionary."""
        reaction_type_str = data.get("reaction_type", "OTHER")
        try:
            reaction_type = ReactionType(reaction_type_str)
        except ValueError:
            reaction_type = ReactionType.OTHER

        return cls(
            reaction_id=data.get("reaction_id", ""),
            smiles_reactants=data.get("smiles_reactants", ""),
            smiles_products=data.get("smiles_products", ""),
            smiles_reagent=data.get("smiles_reagent"),
            reaction_type=reaction_type,
            metadata=data.get("metadata", {}),
            is_valid=data.get("is_valid", True),
            error_message=data.get("error_message")
        )

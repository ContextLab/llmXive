"""
Base schema definitions for ReactionRecord and TopologicalDescriptor.

These classes serve as the strict data contract between pipeline stages:
1. Ingestion (T011-T015) produces ReactionRecord instances.
2. Descriptor Calculation (T020-T027) consumes ReactionRecord and produces TopologicalDescriptor.
3. Modeling (T032-T040) consumes TopologicalDescriptor.

Attributes are typed and validated to prevent silent data corruption.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass(frozen=True)
class ReactionRecord:
    """
    Immutable record representing a single chemical reaction from the USPTO dataset.

    Attributes:
        reaction_id: Unique identifier for the reaction (e.g., USPTO ID or hash).
        smiles_reactants: SMILES string of the reactant mixture.
        smiles_products: SMILES string of the product mixture.
        smiles_reagent: SMILES string of the reagent(s).
        reaction_type: Classification of the reaction (e.g., "EAS" for Electrophilic Aromatic Substitution).
        yield_pct: Reported yield percentage (0-100). May be None if not reported.
        temperature_c: Reaction temperature in Celsius. May be None.
        timestamp: Ingestion timestamp for auditability.
        raw_record: Optional dictionary holding the original raw data for debugging.
    """
    reaction_id: str
    smiles_reactants: str
    smiles_products: str
    smiles_reagent: str
    reaction_type: str
    yield_pct: Optional[float] = None
    temperature_c: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    raw_record: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate required fields and basic constraints."""
        if not self.reaction_id:
            raise ValueError("reaction_id cannot be empty")
        if not self.smiles_reactants:
            raise ValueError("smiles_reactants cannot be empty")
        if not self.smiles_products:
            raise ValueError("smiles_products cannot be empty")
        if self.yield_pct is not None and not (0.0 <= self.yield_pct <= 100.0):
            raise ValueError(f"yield_pct must be between 0 and 100, got {self.yield_pct}")

    @property
    def is_eas(self) -> bool:
        """Check if this reaction is classified as Electrophilic Aromatic Substitution."""
        return self.reaction_type.upper() == "EAS"

@dataclass(frozen=True)
class TopologicalDescriptor:
    """
    Immutable record representing calculated topological indices for a specific molecule.

    This record is generated from a Reactant within a ReactionRecord.
    It serves as the feature vector for the modeling stage.

    Attributes:
        reaction_id: Reference to the parent ReactionRecord.
        smiles: The SMILES string of the specific reactant molecule analyzed.
        wiener_index: The Wiener index (sum of shortest path distances).
        balaban_index: The Balaban J index (connectivity index).
        zagreb_index: The Zagreb index (sum of squared degrees).
        atom_count: Total number of atoms in the molecule.
        bond_count: Total number of bonds in the molecule.
        is_valid_topology: Boolean flag indicating if the graph was connected and valid.
        symmetry_class: Optional integer representing the symmetry class of the aromatic ring.
        calculation_timestamp: Timestamp of the calculation.
    """
    reaction_id: str
    smiles: str
    wiener_index: float
    balaban_index: float
    zagreb_index: float
    atom_count: int
    bond_count: int
    is_valid_topology: bool
    symmetry_class: Optional[int] = None
    calculation_timestamp: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate calculated values."""
        if self.atom_count <= 0:
            raise ValueError("atom_count must be positive")
        if self.bond_count < 0:
            raise ValueError("bond_count cannot be negative")
        if not self.is_valid_topology:
            # If invalid, indices might be 0 or NaN, but we flag it explicitly
            pass
        
        # Basic sanity checks for indices (they must be non-negative for valid graphs)
        if self.is_valid_topology:
            if self.wiener_index < 0 or self.balaban_index < 0 or self.zagreb_index < 0:
                raise ValueError("Topological indices must be non-negative for valid topologies")

    @property
    def feature_vector(self) -> List[float]:
        """Return the primary numerical features as a list."""
        return [self.wiener_index, self.balaban_index, self.zagreb_index]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for CSV/JSON serialization."""
        return {
            "reaction_id": self.reaction_id,
            "smiles": self.smiles,
            "wiener_index": self.wiener_index,
            "balaban_index": self.balaban_index,
            "zagreb_index": self.zagreb_index,
            "atom_count": self.atom_count,
            "bond_count": self.bond_count,
            "is_valid_topology": self.is_valid_topology,
            "symmetry_class": self.symmetry_class,
            "calculation_timestamp": self.calculation_timestamp.isoformat()
        }

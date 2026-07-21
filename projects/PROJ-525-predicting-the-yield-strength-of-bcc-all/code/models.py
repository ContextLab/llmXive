"""
Data models for the BCC Yield Strength prediction pipeline.

Defines the core data structures for alloy records and compositional descriptors.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from typing_extensions import Literal


@dataclass
class AlloyRecord:
    """
    Represents a single alloy entry from the raw or processed dataset.

    Attributes:
        alloy_id: Unique identifier for the alloy entry.
        composition: Dictionary mapping element symbols to their atomic fractions.
        yield_strength_mpa: Yield strength in MPa.
        crystal_structure: The crystal structure of the alloy (e.g., 'BCC', 'FCC', 'HCP').
        temperature: Measurement temperature (optional).
        metadata: Additional key-value pairs for provenance or specific conditions.
    """
    alloy_id: str
    composition: Dict[str, float]
    yield_strength_mpa: float
    crystal_structure: str
    temperature: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate that composition values sum to approximately 1.0."""
        if self.composition:
            total = sum(self.composition.values())
            if not (0.99 <= total <= 1.01):
                raise ValueError(f"Composition sum {total:.4f} is not within [0.99, 1.01] for alloy {self.alloy_id}")


@dataclass
class CompositionalDescriptor:
    """
    Represents the engineered feature vector for an alloy.

    Attributes:
        alloy_id: Reference to the source alloy.
        scalar_descriptors: Dictionary of scalar calculated features (e.g., delta, VEC, entropy).
        ilr_transformed_features: List of floats representing the Isometric Log-Ratio transformed composition.
            Initialized as an empty list by default. This field is populated by the feature engineering
            step (T026) and used in downstream modeling.
    """
    alloy_id: str
    scalar_descriptors: Dict[str, float] = field(default_factory=dict)
    ilr_transformed_features: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the descriptor to a dictionary for serialization."""
        return {
            "alloy_id": self.alloy_id,
            "scalar_descriptors": self.scalar_descriptors,
            "ilr_transformed_features": self.ilr_transformed_features,
        }
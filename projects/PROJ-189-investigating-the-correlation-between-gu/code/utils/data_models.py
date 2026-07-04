"""
Base data models and entities for the Gut Microbiome and Cognitive Decline Analysis.

This module defines the core data structures (Sample, Taxon) used throughout the pipeline.
These models are designed to be serializable and compatible with pandas DataFrames.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import json


class DataType(Enum):
    """Enumeration of supported data types for validation."""
    RAW_COUNTS = "raw_counts"
    RELATIVE_ABUNDANCE = "relative_abundance"
    CLR_TRANSFORMED = "clr_transformed"
    COGNITIVE_SCORE = "cognitive_score"
    COVARIATE = "covariate"


@dataclass
class Taxon:
    """
    Represents a taxonomic entity (e.g., a genus, species, or family).

    Attributes:
        id: Unique identifier for the taxon (e.g., 'g__Bacteroides').
        rank: Taxonomic rank (e.g., 'genus', 'species', 'family').
        name: Human-readable name.
        metadata: Optional dictionary for additional taxonomic metadata.
    """
    id: str
    rank: str
    name: str
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the Taxon object to a dictionary."""
        return {
            "id": self.id,
            "rank": self.rank,
            "name": self.name,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Taxon':
        """Create a Taxon object from a dictionary."""
        return cls(
            id=data.get("id", ""),
            rank=data.get("rank", "unknown"),
            name=data.get("name", ""),
            metadata=data.get("metadata", {})
        )


@dataclass
class Sample:
    """
    Represents a single biological sample associated with a participant.

    This model aggregates microbial abundance data and associated metadata
    (age, cognitive scores, etc.) for a single row in the analysis dataset.

    Attributes:
        sample_id: Unique identifier for the sample (often matches participant_id).
        participant_id: The ID of the human participant.
        age: Age of the participant at time of sample collection.
        cognitive_scores: Dictionary of cognitive test scores (e.g., {'memory': 0.85}).
        covariates: Dictionary of covariates (e.g., {'bmi': 24.5, 'education_years': 16}).
        taxon_abundances: Dictionary mapping Taxon IDs to abundance values (counts or relative).
        data_type: The type of abundance data stored (raw, relative, clr).
        metadata: Additional sample-level metadata.
    """
    sample_id: str
    participant_id: str
    age: Optional[float] = None
    cognitive_scores: Dict[str, float] = field(default_factory=dict)
    covariates: Dict[str, float] = field(default_factory=dict)
    taxon_abundances: Dict[str, float] = field(default_factory=dict)
    data_type: DataType = DataType.RAW_COUNTS
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)

    def get_abundance(self, taxon_id: str) -> float:
        """Retrieve abundance for a specific taxon, defaulting to 0.0 if missing."""
        return self.taxon_abundances.get(taxon_id, 0.0)

    def has_non_null_cognitive_score(self) -> bool:
        """Check if at least one cognitive score is present and non-null."""
        return any(
            score is not None and not (isinstance(score, float) and score != score)
            for score in self.cognitive_scores.values()
        )

    def filter_by_age(self, min_age: int) -> bool:
        """
        Returns True if the sample's age meets the minimum threshold.
        Note: This is a check, not an in-place filter.
        """
        if self.age is None:
            return False
        return self.age >= min_age

    def to_dict(self) -> Dict[str, Any]:
        """Convert the Sample object to a dictionary for serialization."""
        return {
            "sample_id": self.sample_id,
            "participant_id": self.participant_id,
            "age": self.age,
            "cognitive_scores": self.cognitive_scores,
            "covariates": self.covariates,
            "taxon_abundances": self.taxon_abundances,
            "data_type": self.data_type.value,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Sample':
        """Create a Sample object from a dictionary."""
        return cls(
            sample_id=data.get("sample_id", ""),
            participant_id=data.get("participant_id", ""),
            age=data.get("age"),
            cognitive_scores=data.get("cognitive_scores", {}),
            covariates=data.get("covariates", {}),
            taxon_abundances=data.get("taxon_abundances", {}),
            data_type=DataType(data.get("data_type", "raw_counts")),
            metadata=data.get("metadata", {})
        )

    def to_json(self) -> str:
        """Serialize the sample to a JSON string."""
        # Custom serialization for Enum
        data = self.to_dict()
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> 'Sample':
        """Deserialize a sample from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

"""
Data entities for the drought tolerance prediction pipeline.

This module defines the core data structures used throughout the project:
- SpeciesRecord: Represents a single species with its traits, genomic markers, and label.
- ModelResult: Stores the results of a model training run, including metrics and hyperparameters.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import json


@dataclass
class SpeciesRecord:
    """
    Represents a single species record containing physiological traits,
    genomic markers, and the drought tolerance label.

    Attributes:
        species_id (str): Unique identifier for the species.
        traits_dict (Dict[str, float]): Dictionary mapping trait names to their values.
        genomic_markers (List[str]): List of gene markers present for this species.
        label (int): Drought tolerance label (1 = tolerant, 0 = sensitive).
    """
    species_id: str
    traits_dict: Dict[str, float]
    genomic_markers: List[str]
    label: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert the record to a dictionary for serialization."""
        return {
            "species_id": self.species_id,
            "traits_dict": self.traits_dict,
            "genomic_markers": self.genomic_markers,
            "label": self.label
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpeciesRecord":
        """Create a SpeciesRecord instance from a dictionary."""
        return cls(
            species_id=data["species_id"],
            traits_dict=data["traits_dict"],
            genomic_markers=data["genomic_markers"],
            label=data["label"]
        )


@dataclass
class ModelResult:
    """
    Stores the results of a model training run.

    Attributes:
        model_name (str): Name of the model (e.g., "RandomForest", "XGBoost").
        metrics (Dict[str, float]): Dictionary of evaluation metrics (e.g., AUC, accuracy).
        hyperparameters (Dict[str, Any]): Dictionary of the model's hyperparameters used.
        feature_importance (Dict[str, float]): Dictionary mapping feature names to importance scores.
    """
    model_name: str
    metrics: Dict[str, float]
    hyperparameters: Dict[str, Any]
    feature_importance: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary for serialization."""
        return {
            "model_name": self.model_name,
            "metrics": self.metrics,
            "hyperparameters": self.hyperparameters,
            "feature_importance": self.feature_importance
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize the result to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelResult":
        """Create a ModelResult instance from a dictionary."""
        return cls(
            model_name=data["model_name"],
            metrics=data["metrics"],
            hyperparameters=data["hyperparameters"],
            feature_importance=data["feature_importance"]
        )

    @classmethod
    def from_json(cls, json_str: str) -> "ModelResult":
        """Create a ModelResult instance from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
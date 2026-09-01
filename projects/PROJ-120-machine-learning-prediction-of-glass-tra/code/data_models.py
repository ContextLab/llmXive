"""
Data models for the Glass Transition Temperature Prediction pipeline.

This module defines Pydantic models for:
- GlassSample: A single glass composition with its properties.
- ModelResult: The output of a model prediction or evaluation.
- Dataset: A collection of GlassSamples.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json
from pathlib import Path

@dataclass
class GlassSample:
    """
    Represents a single glass sample with composition and target property.

    Attributes:
        formula (str): Chemical formula string (e.g., "SiO2").
        tg (float): Glass transition temperature in Kelvin.
        composition (Dict[str, float]): Elemental atomic fractions (e.g., {"Si": 0.33, "O": 0.67}).
        features (Dict[str, float]): Calculated compositional descriptors (e.g., avg_electronegativity).
        source_id (Optional[str]): Original identifier from the source dataset.
    """
    formula: str
    tg: float
    composition: Dict[str, float] = field(default_factory=dict)
    features: Dict[str, float] = field(default_factory=dict)
    source_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the sample to a dictionary for serialization."""
        return {
            "formula": self.formula,
            "tg": self.tg,
            "composition": self.composition,
            "features": self.features,
            "source_id": self.source_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GlassSample":
        """Reconstruct a GlassSample from a dictionary."""
        return cls(
            formula=data["formula"],
            tg=data["tg"],
            composition=data.get("composition", {}),
            features=data.get("features", {}),
            source_id=data.get("source_id")
        )


@dataclass
class ModelResult:
    """
    Represents the result of a model prediction or evaluation run.

    Attributes:
        model_name (str): Name of the model used (e.g., "RandomForest").
        metrics (Dict[str, float]): Evaluation metrics (e.g., R2, MAE, RMSE).
        predictions (List[float]): List of predicted values.
        targets (List[float]): List of true target values.
        hyperparameters (Dict[str, Any]): The hyperparameters used for this model.
        fold_id (Optional[int]): If from cross-validation, the fold index.
    """
    model_name: str
    metrics: Dict[str, float]
    predictions: List[float]
    targets: List[float]
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    fold_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary for serialization."""
        return {
            "model_name": self.model_name,
            "metrics": self.metrics,
            "predictions": self.predictions,
            "targets": self.targets,
            "hyperparameters": self.hyperparameters,
            "fold_id": self.fold_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelResult":
        """Reconstruct a ModelResult from a dictionary."""
        return cls(
            model_name=data["model_name"],
            metrics=data["metrics"],
            predictions=data["predictions"],
            targets=data["targets"],
            hyperparameters=data.get("hyperparameters", {}),
            fold_id=data.get("fold_id")
        )


@dataclass
class Dataset:
    """
    Container for a collection of GlassSamples.

    Attributes:
        samples (List[GlassSample]): List of glass samples.
        metadata (Dict[str, Any]): Dataset-level metadata (e.g., source, date).
    """
    samples: List[GlassSample] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_sample(self, sample: GlassSample) -> None:
        """Add a sample to the dataset."""
        self.samples.append(sample)

    def extend(self, samples: List[GlassSample]) -> None:
        """Add multiple samples to the dataset."""
        self.samples.extend(samples)

    def filter_by_formula_prefix(self, prefix: str) -> "Dataset":
        """Return a new dataset containing only samples with formulas starting with prefix."""
        new_samples = [s for s in self.samples if s.formula.startswith(prefix)]
        return Dataset(samples=new_samples, metadata=self.metadata.copy())

    def to_json(self, path: Path) -> None:
        """Serialize the dataset to a JSON file."""
        data = {
            "metadata": self.metadata,
            "samples": [s.to_dict() for s in self.samples]
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def from_json(cls, path: Path) -> "Dataset":
        """Load a dataset from a JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        samples = [GlassSample.from_dict(s) for s in data.get("samples", [])]
        metadata = data.get("metadata", {})
        return cls(samples=samples, metadata=metadata)

    def __len__(self) -> int:
        return len(self.samples)

    def __iter__(self):
        return iter(self.samples)
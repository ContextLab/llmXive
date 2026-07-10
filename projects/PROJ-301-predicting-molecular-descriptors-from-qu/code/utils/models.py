"""
Base data model classes for the molecular descriptor prediction pipeline.

Defines the core data structures:
- Molecule: Represents a single molecular entity with identifiers and properties.
- FeatureSet: Container for precomputed feature matrices (2D/3D) and metadata.
- ModelResult: Container for model predictions, metrics, and metadata.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
import numpy as np
import json


@dataclass
class Molecule:
    """
    Represents a single molecule with its identifiers and target properties.

    Attributes:
        mol_id: Unique identifier for the molecule (e.g., from QM9).
        smiles: Canonical SMILES string representation.
        properties: Dictionary of target DFT properties (e.g., dipole, HOMO, LUMO).
        metadata: Additional metadata (e.g., atom count, source index).
    """
    mol_id: str
    smiles: str
    properties: Dict[str, float]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the molecule instance to a dictionary."""
        return {
            "mol_id": self.mol_id,
            "smiles": self.smiles,
            "properties": self.properties,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Molecule":
        """Construct a Molecule instance from a dictionary."""
        return cls(
            mol_id=data["mol_id"],
            smiles=data["smiles"],
            properties=data["properties"],
            metadata=data.get("metadata", {})
        )


@dataclass
class FeatureSet:
    """
    Container for precomputed feature matrices and their metadata.

    Attributes:
        features_2d: 2D feature matrix (e.g., fingerprints) of shape (n_samples, n_features_2d).
        features_3d: 3D feature matrix (e.g., graph features) of shape (n_samples, n_features_3d).
        indices: List of molecule IDs corresponding to the rows in the feature matrices.
        metadata: Metadata about the feature extraction (e.g., fingerprint radius, nBits).
    """
    features_2d: Optional[np.ndarray] = None
    features_3d: Optional[np.ndarray] = None
    indices: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate consistency after initialization."""
        if self.features_2d is not None and self.features_3d is not None:
            if self.features_2d.shape[0] != self.features_3d.shape[0]:
                raise ValueError(
                    f"Shape mismatch: features_2d has {self.features_2d.shape[0]} samples, "
                    f"features_3d has {self.features_3d.shape[0]} samples."
                )
        if self.features_2d is not None:
            if len(self.indices) != self.features_2d.shape[0]:
                raise ValueError(
                    f"Index count ({len(self.indices)}) does not match feature row count ({self.features_2d.shape[0]})."
                )

    def get_2d_array(self) -> np.ndarray:
        """Return the 2D feature array, raising an error if missing."""
        if self.features_2d is None:
            raise ValueError("2D features are not available in this FeatureSet.")
        return self.features_2d

    def get_3d_array(self) -> np.ndarray:
        """Return the 3D feature array, raising an error if missing."""
        if self.features_3d is None:
            raise ValueError("3D features are not available in this FeatureSet.")
        return self.features_3d

    def to_dict(self) -> Dict[str, Any]:
        """Convert the FeatureSet to a dictionary (for JSON serialization of metadata)."""
        return {
            "metadata": self.metadata,
            "indices": self.indices,
            "shape_2d": list(self.features_2d.shape) if self.features_2d is not None else None,
            "shape_3d": list(self.features_3d.shape) if self.features_3d is not None else None
        }


@dataclass
class ModelResult:
    """
    Container for model training results and predictions.

    Attributes:
        model_type: String identifier for the model (e.g., "RandomForest_2D").
        predictions: Array of predicted values.
        actuals: Array of actual target values.
        metrics: Dictionary of evaluation metrics (e.g., MAE, RMSE, R2).
        fold_metrics: Optional list of metrics per cross-validation fold.
        metadata: Additional metadata (e.g., hyperparameters, training timestamp).
    """
    model_type: str
    predictions: np.ndarray
    actuals: np.ndarray
    metrics: Dict[str, float]
    fold_metrics: Optional[List[Dict[str, float]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate consistency after initialization."""
        if len(self.predictions) != len(self.actuals):
            raise ValueError(
                f"Shape mismatch: predictions ({len(self.predictions)}) "
                f"and actuals ({len(self.actuals)}) must have the same length."
            )

    def get_error(self) -> np.ndarray:
        """Calculate absolute errors."""
        return np.abs(self.predictions - self.actuals)

    def get_mean_error(self) -> float:
        """Calculate Mean Absolute Error (MAE)."""
        return float(np.mean(self.get_error()))

    def to_dict(self) -> Dict[str, Any]:
        """Convert the ModelResult to a dictionary (excluding large arrays)."""
        return {
            "model_type": self.model_type,
            "metrics": self.metrics,
            "fold_metrics": self.fold_metrics,
            "metadata": self.metadata,
            "n_samples": len(self.predictions),
            "mean_absolute_error": self.get_mean_error()
        }

    def save_metrics_json(self, path: str) -> None:
        """Save the metrics and metadata to a JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
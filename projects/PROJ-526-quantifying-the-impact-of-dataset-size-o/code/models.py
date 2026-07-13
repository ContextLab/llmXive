"""
Base data models for the Quantifying the Impact of Dataset Size on ML Accuracy project.

This module defines the core data structures (Pydantic models) used throughout the pipeline:
- MaterialEntry: Represents a single material record with composition and target property.
- LearningCurve: Represents a single point on a learning curve (subset size vs error).
- ScalingResult: Represents the aggregated result of fitting a power-law scaling model.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np

@dataclass
class MaterialEntry:
    """
    Represents a single material entry.

    Attributes:
        material_id (str): Unique identifier for the material (e.g., from Materials Project).
        composition (Dict[str, float]): Dictionary mapping element symbols to fractions.
        magpie_features (np.ndarray): Composition-only Magpie descriptor vector.
        target_property (float): The target property value (e.g., formation energy).
        property_name (str): Name of the target property (e.g., 'formation_energy_per_atom').
        structure_available (bool): Whether structural data is available (False for composition-only).
        metadata (Dict[str, Any]): Additional metadata (source, citations, etc.).
    """
    material_id: str
    composition: Dict[str, float]
    magpie_features: np.ndarray
    target_property: float
    property_name: str
    structure_available: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the entry to a dictionary suitable for serialization."""
        return {
            "material_id": self.material_id,
            "composition": self.composition,
            "magpie_features": self.magpie_features.tolist(),
            "target_property": self.target_property,
            "property_name": self.property_name,
            "structure_available": self.structure_available,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MaterialEntry':
        """Create a MaterialEntry from a dictionary."""
        return cls(
            material_id=data["material_id"],
            composition=data["composition"],
            magpie_features=np.array(data["magpie_features"]),
            target_property=data["target_property"],
            property_name=data["property_name"],
            structure_available=data.get("structure_available", False),
            metadata=data.get("metadata", {})
        )


@dataclass
class LearningCurve:
    """
    Represents a single point on a learning curve.

    Attributes:
        property_name (str): Name of the property being modeled.
        subset_size (int): Number of training samples used.
        mean_error (float): Mean error metric (e.g., MAE) across seeds.
        std_error (float): Standard deviation of the error metric.
        seed (int): Random seed used for this specific run (if single-seed).
        model_type (str): Type of model used (e.g., 'RandomForest').
        hyperparameters (Dict[str, Any]): Hyperparameters used for training.
    """
    property_name: str
    subset_size: int
    mean_error: float
    std_error: float
    seed: Optional[int] = None
    model_type: str = "RandomForest"
    hyperparameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the learning curve point to a dictionary."""
        return {
            "property_name": self.property_name,
            "subset_size": self.subset_size,
            "mean_error": self.mean_error,
            "std_error": self.std_error,
            "seed": self.seed,
            "model_type": self.model_type,
            "hyperparameters": self.hyperparameters
        }


@dataclass
class ScalingResult:
    """
    Represents the result of fitting a power-law scaling model to a learning curve.

    Attributes:
        property_name (str): Name of the property.
        exponent_b (float): The scaling exponent (b) in Error = a * N^(-b).
        intercept_a (float): The intercept (a) in Error = a * N^(-b).
        r_squared (float): R-squared value of the fit.
        fit_status (str): Status of the fit (e.g., 'power-law', 'non-power-law', 'insufficient_data').
        data_points_count (int): Number of data points used for fitting.
        class_label (Optional[str]): Physical class label if available (e.g., 'electronic', 'mechanical').
    """
    property_name: str
    exponent_b: float
    intercept_a: float
    r_squared: float
    fit_status: str
    data_points_count: int
    class_label: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the scaling result to a dictionary."""
        return {
            "property_name": self.property_name,
            "exponent_b": self.exponent_b,
            "intercept_a": self.intercept_a,
            "r_squared": self.r_squared,
            "fit_status": self.fit_status,
            "data_points_count": self.data_points_count,
            "class_label": self.class_label
        }
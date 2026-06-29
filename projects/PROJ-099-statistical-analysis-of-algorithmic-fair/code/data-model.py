"""
Data model classes for the statistical analysis of algorithmic fairness pipeline.

This module defines the core data structures used throughout the research
pipeline: Dataset, Model, FairnessMetric, and DatasetCharacteristic.

These classes provide type-safe containers for research artifacts and ensure
consistency across the analysis pipeline.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import hashlib
import json


class DatasetCharacteristic:
    """
    Represents a characteristic of a dataset that may influence fairness metrics.

    Per Constitution Principle VII, these characteristics are associational
    predictors, not causal determinants of fairness outcomes.

    Attributes:
        dataset_id: Unique identifier for the dataset
        base_rate_difference: Difference in outcome base rates between groups
        class_imbalance_ratio: Ratio of majority to minority class
        feature_dimensionality: Number of features in the dataset
        protected_attribute_name: Name of the protected attribute column
        sample_size: Number of samples in the dataset
    """

    def __init__(
        self,
        dataset_id: str,
        base_rate_difference: float = 0.0,
        class_imbalance_ratio: float = 1.0,
        feature_dimensionality: int = 0,
        protected_attribute_name: str = "",
        sample_size: int = 0,
    ):
        """
        Initialize a DatasetCharacteristic.

        Args:
            dataset_id: Unique identifier for the dataset
            base_rate_difference: Difference in outcome base rates between groups
            class_imbalance_ratio: Ratio of majority to minority class (≥1.0)
            feature_dimensionality: Number of features in the dataset
            protected_attribute_name: Name of the protected attribute column
            sample_size: Number of samples in the dataset
        """
        self.dataset_id: str = dataset_id
        self.base_rate_difference: float = base_rate_difference
        self.class_imbalance_ratio: float = max(class_imbalance_ratio, 1.0)
        self.feature_dimensionality: int = feature_dimensionality
        self.protected_attribute_name: str = protected_attribute_name
        self.sample_size: int = sample_size

    def to_dict(self) -> Dict[str, Any]:
        """Convert the characteristic to a dictionary."""
        return {
            "dataset_id": self.dataset_id,
            "base_rate_difference": self.base_rate_difference,
            "class_imbalance_ratio": self.class_imbalance_ratio,
            "feature_dimensionality": self.feature_dimensionality,
            "protected_attribute_name": self.protected_attribute_name,
            "sample_size": self.sample_size,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatasetCharacteristic":
        """Create a DatasetCharacteristic from a dictionary."""
        return cls(
            dataset_id=data["dataset_id"],
            base_rate_difference=data.get("base_rate_difference", 0.0),
            class_imbalance_ratio=data.get("class_imbalance_ratio", 1.0),
            feature_dimensionality=data.get("feature_dimensionality", 0),
            protected_attribute_name=data.get("protected_attribute_name", ""),
            sample_size=data.get("sample_size", 0),
        )

    def __repr__(self) -> str:
        return (
            f"DatasetCharacteristic("
            f"dataset_id={self.dataset_id}, "
            f"base_rate_diff={self.base_rate_difference:.4f}, "
            f"class_imbalance={self.class_imbalance_ratio:.2f}, "
            f"n_features={self.feature_dimensionality}, "
            f"n_samples={self.sample_size})"
        )


@dataclass
class FairnessMetric:
    """
    Represents a fairness metric computed on a model's predictions.

    Per FR-008, all findings are associational only; no causal claims
    are made about fairness metrics and dataset characteristics.

    Attributes:
        metric_name: Name of the metric (e.g., "demographic_parity_difference")
        metric_value: Computed value of the metric
        protected_attribute: The protected attribute used for grouping
        dataset_id: ID of the dataset used
        model_id: ID of the model used
        formula: LaTeX formula for the metric
        citation: Reference to the metric's definition source
    """

    metric_name: str
    metric_value: float
    protected_attribute: str
    dataset_id: str
    model_id: str
    formula: str = ""
    citation: str = ""
    confidence_interval: Optional[tuple] = None

    def __post_init__(self):
        """Validate the metric after initialization."""
        if not isinstance(self.metric_value, (int, float)):
            raise TypeError("metric_value must be a number")
        if not isinstance(self.protected_attribute, str):
            raise TypeError("protected_attribute must be a string")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the metric to a dictionary."""
        result = {
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "protected_attribute": self.protected_attribute,
            "dataset_id": self.dataset_id,
            "model_id": self.model_id,
            "formula": self.formula,
            "citation": self.citation,
        }
        if self.confidence_interval:
            result["confidence_interval"] = list(self.confidence_interval)
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FairnessMetric":
        """Create a FairnessMetric from a dictionary."""
        ci = data.get("confidence_interval")
        if ci:
            ci = tuple(ci)
        return cls(
            metric_name=data["metric_name"],
            metric_value=data["metric_value"],
            protected_attribute=data["protected_attribute"],
            dataset_id=data["dataset_id"],
            model_id=data["model_id"],
            formula=data.get("formula", ""),
            citation=data.get("citation", ""),
            confidence_interval=ci,
        )

    def __repr__(self) -> str:
        ci_str = ""
        if self.confidence_interval:
            ci_str = f" [CI: {self.confidence_interval[0]:.4f}, {self.confidence_interval[1]:.4f}]"
        return (
            f"FairnessMetric("
            f"name={self.metric_name}, "
            f"value={self.metric_value:.4f}{ci_str}, "
            f"protected={self.protected_attribute})"
        )


@dataclass
class Model:
    """
    Represents a trained machine learning model in the fairness analysis pipeline.

    Attributes:
        model_id: Unique identifier for the model
        model_type: Type of model (e.g., "LogisticRegression", "RandomForest")
        dataset_id: ID of the dataset used for training
        metrics: List of fairness metrics computed for this model
        parameters: Hyperparameters used for training
        trained: Whether the model has been trained
        path: Path to the saved model file
    """

    model_id: str
    model_type: str
    dataset_id: str
    metrics: List[FairnessMetric] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    trained: bool = False
    path: Optional[str] = None

    def __post_init__(self):
        """Validate the model after initialization."""
        if not isinstance(self.metrics, list):
            raise TypeError("metrics must be a list of FairnessMetric objects")
        if not isinstance(self.parameters, dict):
            raise TypeError("parameters must be a dictionary")

    def add_metric(self, metric: FairnessMetric) -> None:
        """
        Add a fairness metric to this model.

        Args:
            metric: The FairnessMetric to add
        """
        self.metrics.append(metric)

    def get_metrics_by_name(self, metric_name: str) -> List[FairnessMetric]:
        """
        Get all metrics with a specific name.

        Args:
            metric_name: Name of the metric to filter by

        Returns:
            List of FairnessMetric objects with the given name
        """
        return [m for m in self.metrics if m.metric_name == metric_name]

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary."""
        return {
            "model_id": self.model_id,
            "model_type": self.model_type,
            "dataset_id": self.dataset_id,
            "metrics": [m.to_dict() for m in self.metrics],
            "parameters": self.parameters,
            "trained": self.trained,
            "path": self.path,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Model":
        """Create a Model from a dictionary."""
        metrics = [
            FairnessMetric.from_dict(m) for m in data.get("metrics", [])
        ]
        return cls(
            model_id=data["model_id"],
            model_type=data["model_type"],
            dataset_id=data["dataset_id"],
            metrics=metrics,
            parameters=data.get("parameters", {}),
            trained=data.get("trained", False),
            path=data.get("path"),
        )

    def __repr__(self) -> str:
        return (
            f"Model("
            f"id={self.model_id}, "
            f"type={self.model_type}, "
            f"dataset={self.dataset_id}, "
            f"n_metrics={len(self.metrics)})"
        )


@dataclass
class Dataset:
    """
    Represents a dataset in the fairness analysis pipeline.

    Per Constitution Principle III, raw data files must remain unchanged
    after processing; this class tracks both raw and processed versions.

    Attributes:
        dataset_id: Unique identifier for the dataset
        name: Human-readable name of the dataset
        raw_path: Path to the raw data file
        processed_path: Path to the preprocessed data file
        protected_attribute: Name of the protected attribute column
        outcome: Name of the outcome column
        predictions: Name of the predictions column
        checksum: SHA-256 checksum of the raw file
        sample_size: Number of samples after preprocessing
        characteristics: Dataset characteristics (base rate, imbalance, etc.)
    """

    dataset_id: str
    name: str
    raw_path: Optional[str] = None
    processed_path: Optional[str] = None
    protected_attribute: str = ""
    outcome: str = ""
    predictions: str = ""
    checksum: Optional[str] = None
    sample_size: int = 0
    characteristics: Optional[DatasetCharacteristic] = None
    url: Optional[str] = None

    def __post_init__(self):
        """Validate the dataset after initialization."""
        if self.checksum and not self._is_valid_checksum_format(self.checksum):
            raise ValueError(
                f"Invalid checksum format: {self.checksum}. "
                "Expected SHA-256 hex string (64 characters)."
            )

    @staticmethod
    def _is_valid_checksum_format(checksum: str) -> bool:
        """Check if a string is a valid SHA-256 hex checksum."""
        return (
            isinstance(checksum, str)
            and len(checksum) == 64
            and all(c in "0123456789abcdef" for c in checksum.lower())
        )

    def compute_checksum(self, filepath: str) -> str:
        """
        Compute SHA-256 checksum of a file.

        Args:
            filepath: Path to the file to checksum

        Returns:
            SHA-256 hex digest of the file contents
        """
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def verify_checksum(self, filepath: str) -> bool:
        """
        Verify that a file's checksum matches the stored checksum.

        Args:
            filepath: Path to the file to verify

        Returns:
            True if checksums match, False otherwise
        """
        if not self.checksum:
            return False
        computed = self.compute_checksum(filepath)
        return computed.lower() == self.checksum.lower()

    def set_characteristics(
        self,
        base_rate_difference: float = 0.0,
        class_imbalance_ratio: float = 1.0,
        feature_dimensionality: int = 0,
    ) -> None:
        """
        Set dataset characteristics.

        Args:
            base_rate_difference: Difference in outcome base rates between groups
            class_imbalance_ratio: Ratio of majority to minority class
            feature_dimensionality: Number of features in the dataset
        """
        self.characteristics = DatasetCharacteristic(
            dataset_id=self.dataset_id,
            base_rate_difference=base_rate_difference,
            class_imbalance_ratio=class_imbalance_ratio,
            feature_dimensionality=feature_dimensionality,
            protected_attribute_name=self.protected_attribute,
            sample_size=self.sample_size,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataset to a dictionary."""
        result = {
            "dataset_id": self.dataset_id,
            "name": self.name,
            "raw_path": self.raw_path,
            "processed_path": self.processed_path,
            "protected_attribute": self.protected_attribute,
            "outcome": self.outcome,
            "predictions": self.predictions,
            "checksum": self.checksum,
            "sample_size": self.sample_size,
            "url": self.url,
        }
        if self.characteristics:
            result["characteristics"] = self.characteristics.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Dataset":
        """Create a Dataset from a dictionary."""
        characteristics_data = data.get("characteristics")
        characteristics = None
        if characteristics_data:
            characteristics = DatasetCharacteristic.from_dict(characteristics_data)
        return cls(
            dataset_id=data["dataset_id"],
            name=data["name"],
            raw_path=data.get("raw_path"),
            processed_path=data.get("processed_path"),
            protected_attribute=data.get("protected_attribute", ""),
            outcome=data.get("outcome", ""),
            predictions=data.get("predictions", ""),
            checksum=data.get("checksum"),
            sample_size=data.get("sample_size", 0),
            characteristics=characteristics,
            url=data.get("url"),
        )

    def __repr__(self) -> str:
        char_str = ""
        if self.characteristics:
            char_str = f", characteristics={self.characteristics}"
        return (
            f"Dataset("
            f"id={self.dataset_id}, "
            f"name={self.name}, "
            f"n_samples={self.sample_size}{char_str})"
        )

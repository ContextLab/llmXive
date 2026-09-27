"""
Base data models for the crystal structure prediction pipeline.

Defines core dataclasses for MoleculeRecord, ModelMetrics, and FeatureImportance
used throughout the ingestion, modeling, and analysis phases.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


@dataclass
class MoleculeRecord:
    """
    Represents a single molecule entry with its structural and crystallographic data.

    Attributes:
        smiles: Canonical SMILES string of the molecule.
        space_group: Space group identifier (e.g., 'P2_1/c', 'Fm-3m').
        lattice_a: Lattice parameter a (Angstrom).
        lattice_b: Lattice parameter b (Angstrom).
        lattice_c: Lattice parameter c (Angstrom).
        alpha: Lattice angle alpha (degrees).
        beta: Lattice angle beta (degrees).
        gamma: Lattice angle gamma (degrees).
        molecular_weight: Calculated molecular weight (g/mol).
        fingerprint_bits: List of integers representing ECFP4 fingerprint bits.
        source_id: Original identifier from the source database (e.g., COD ID).
        processed_at: Timestamp of processing.
    """
    smiles: str
    space_group: str
    lattice_a: float
    lattice_b: float
    lattice_c: float
    alpha: float
    beta: float
    gamma: float
    molecular_weight: float
    fingerprint_bits: List[int]
    source_id: str
    processed_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the record to a dictionary suitable for JSON/CSV serialization."""
        return {
            "smiles": self.smiles,
            "space_group": self.space_group,
            "lattice_a": self.lattice_a,
            "lattice_b": self.lattice_b,
            "lattice_c": self.lattice_c,
            "alpha": self.alpha,
            "beta": self.beta,
            "gamma": self.gamma,
            "molecular_weight": self.molecular_weight,
            "fingerprint_bits": self.fingerprint_bits,
            "source_id": self.source_id,
            "processed_at": self.processed_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MoleculeRecord":
        """Reconstruct a MoleculeRecord from a dictionary."""
        # Handle timestamp deserialization if needed
        ts = data.get("processed_at")
        if isinstance(ts, str):
            data["processed_at"] = datetime.fromisoformat(ts)
        return cls(**data)


@dataclass
class ModelMetrics:
    """
    Stores performance metrics for a trained model.

    Attributes:
        model_name: Name/identifier of the model (e.g., 'RandomForest', 'Ridge').
        metric_type: Type of task ('classification' or 'regression').
        accuracy: Accuracy score (classification).
        macro_f1: Macro-averaged F1 score (classification).
        r_squared: R-squared value (regression).
        mae: Mean Absolute Error (regression).
        train_size: Number of samples in training set.
        test_size: Number of samples in test set.
        timestamp: Timestamp when metrics were calculated.
        metadata: Additional context (e.g., hyperparameters, split method).
    """
    model_name: str
    metric_type: str  # 'classification' or 'regression'
    accuracy: Optional[float] = None
    macro_f1: Optional[float] = None
    r_squared: Optional[float] = None
    mae: Optional[float] = None
    train_size: int = 0
    test_size: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to a dictionary."""
        return {
            "model_name": self.model_name,
            "metric_type": self.metric_type,
            "accuracy": self.accuracy,
            "macro_f1": self.macro_f1,
            "r_squared": self.r_squared,
            "mae": self.mae,
            "train_size": self.train_size,
            "test_size": self.test_size,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize metrics to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


@dataclass
class FeatureImportance:
    """
    Stores importance scores for specific fingerprint bits or features.

    Attributes:
        feature_id: Identifier for the feature (e.g., fingerprint bit index).
        importance_score: The calculated importance score (e.g., permutation importance).
        method: Method used to calculate importance (e.g., 'permutation', 'shap').
        substructure: Optional chemical substructure string (SMILES) if mapped.
        collision_flag: True if this bit maps to multiple substructures.
        rank: Rank of this feature in the overall list (1-based).
    """
    feature_id: int
    importance_score: float
    method: str
    substructure: Optional[str] = None
    collision_flag: bool = False
    rank: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "feature_id": self.feature_id,
            "importance_score": self.importance_score,
            "method": self.method,
            "substructure": self.substructure,
            "collision_flag": self.collision_flag,
            "rank": self.rank
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeatureImportance":
        """Reconstruct from dictionary."""
        return cls(**data)

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
